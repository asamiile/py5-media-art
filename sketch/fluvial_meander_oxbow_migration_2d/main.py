"""Fluvial meander & oxbow migration.

A lowland river slowly rewrites its own path across a floodplain. Bends grow by
curvature-driven lateral migration (a simplified Howard & Knutson model), necks
pinch off into still oxbow lakes, and the swept floodplain fossilizes the river's
history as ochre point-bar scroll ridges.

Theme first: the quiet, geologic patience of water reshaping land.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import random

import numpy as np
from scipy.spatial import cKDTree
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(18, 22)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

# --- Palette (warm floodplain, cool water) -----------------------------------
LOAM = (34, 28, 24)            # deep warm brown-black background
SCROLL_A = (150, 112, 64)      # ochre scroll deposit
SCROLL_B = (118, 78, 46)       # sienna scroll deposit
ACCRETION = (214, 190, 138)    # pale-sand fresh point-bar ridge
WATER_DEEP = (44, 86, 94)      # active channel base
WATER_CORE = (118, 196, 204)   # bright thalweg core
OXBOW = (30, 58, 60)           # abandoned still water
OXBOW_RIM = (70, 110, 110)     # faint oxbow shoreline

# --- Meander model parameters ------------------------------------------------
DS = 12.0                      # target arc-length spacing between nodes (px)
CHANNEL_HALF = 17.0            # half channel width (px)
SUBSTEPS = 2                   # migration integrations per rendered frame
MIG_RATE = 2.4                 # base lateral migration magnitude
CURV_CAP = 0.45                # clip on curvature-driven rate (keeps bends sane)
UPSTREAM_TAU = 6.0             # upstream curvature memory (in nodes)
RECENTER = 0.03                # cancel net vertical drift (does NOT flatten bends)
AMP_LIMIT = 1300.0             # soft cap on bend excursion from valley axis (px)
MAXNODES = 1100                # node ceiling (sinuosity is bounded by cutoffs)
INIT_WAVES = 3                 # initial bends across the frame
CUTOFF_DIST = 2.4 * DS         # neck proximity that triggers a cutoff
CUTOFF_MIN_SEP = 14            # min node index separation to consider a cutoff

flood = None                   # persistent floodplain buffer
cx = cy = None                 # centerline node arrays
base_y = 0.0                   # valley axis (vertical center)
hue_phase = 0.0


def _resample(x, y, ds):
    """Resample a polyline to roughly uniform arc-length spacing."""
    dx = np.diff(x)
    dy = np.diff(y)
    seg = np.hypot(dx, dy)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    n = min(MAXNODES, max(8, int(total / ds)))
    sn = np.linspace(0.0, total, n)
    return np.interp(sn, s, x), np.interp(sn, s, y)


def _curvature(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    den = (dx * dx + dy * dy) ** 1.5 + 1e-9
    return (dx * ddy - dy * ddx) / den


def _normals(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    mag = np.hypot(dx, dy) + 1e-9
    # left normal
    return -dy / mag, dx / mag


def _upstream_weighted(curv):
    """Weight curvature by an exponentially decaying upstream window."""
    k = np.exp(-np.arange(0, 30) / UPSTREAM_TAU)
    k /= k.sum()
    # causal convolution from upstream (lower indices = upstream)
    padded = np.concatenate([np.full(len(k) - 1, curv[0]), curv])
    return np.convolve(padded, k[::-1], mode="valid")


def _deposit_floodplain(g, x, y, nx, ny, curv):
    """Accumulate the swept channel and a fresh inner-bank scroll ridge."""
    global hue_phase
    # band polygon (left bank -> reversed right bank), low-alpha sediment
    t = 0.5 + 0.5 * np.sin(hue_phase)
    base = [int(SCROLL_A[i] * t + SCROLL_B[i] * (1 - t)) for i in range(3)]
    g.no_stroke()
    g.fill(base[0], base[1], base[2], 26)
    g.begin_shape()
    for i in range(len(x)):
        g.vertex(x[i] + nx[i] * CHANNEL_HALF, y[i] + ny[i] * CHANNEL_HALF)
    for i in range(len(x) - 1, -1, -1):
        g.vertex(x[i] - nx[i] * CHANNEL_HALF, y[i] - ny[i] * CHANNEL_HALF)
    g.end_shape(py5.CLOSE)

    # inner-bank (point-bar) accretion ridge -> concentric scroll bars
    sign = np.sign(curv)
    off = CHANNEL_HALF * 0.7
    g.no_fill()
    g.stroke(ACCRETION[0], ACCRETION[1], ACCRETION[2], 22)
    g.stroke_weight(2.0)
    g.begin_shape()
    for i in range(len(x)):
        g.vertex(x[i] - sign[i] * nx[i] * off, y[i] - sign[i] * ny[i] * off)
    g.end_shape()
    hue_phase += 0.06


def _fill_oxbow(g, xs, ys):
    """Stamp a permanent oxbow lake where a neck has pinched off."""
    g.stroke(OXBOW_RIM[0], OXBOW_RIM[1], OXBOW_RIM[2], 120)
    g.stroke_weight(3.0)
    g.fill(OXBOW[0], OXBOW[1], OXBOW[2], 235)
    g.begin_shape()
    for i in range(len(xs)):
        g.vertex(xs[i], ys[i])
    g.end_shape(py5.CLOSE)


def _check_cutoff():
    """Detect a neck cutoff; abandon the loop as an oxbow, shortcut the channel."""
    global cx, cy
    pts = np.column_stack([cx, cy])
    tree = cKDTree(pts)
    pairs = tree.query_pairs(CUTOFF_DIST)
    best = None
    for a, b in pairs:
        i, j = (a, b) if a < b else (b, a)
        if j - i >= CUTOFF_MIN_SEP:
            loop_len = j - i
            if best is None or loop_len > best[2]:
                best = (i, j, loop_len)
    if best is None:
        return None
    i, j, _ = best
    ox_x = cx[i:j + 1].copy()
    ox_y = cy[i:j + 1].copy()
    cx = np.concatenate([cx[:i + 1], cx[j:]])
    cy = np.concatenate([cy[:i + 1], cy[j:]])
    return ox_x, ox_y


def setup():
    global flood, cx, cy, base_y
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    flood = py5.create_graphics(W, H)
    flood.begin_draw()
    flood.background(*LOAM)
    flood.no_stroke()
    # large-scale tonal patches so the whole frame reads as floodplain terrain,
    # not an empty void above and below the river belt
    for _ in range(220):
        gx = random.uniform(0, W)
        gy = random.uniform(0, H)
        warm = random.uniform(-1, 1)
        flood.fill(LOAM[0] + 18 * warm, LOAM[1] + 12 * warm, LOAM[2] + 7 * warm, 26)
        flood.circle(gx, gy, random.uniform(280, 720))
    # finer grain mottling on top
    for _ in range(4200):
        gx = random.uniform(0, W)
        gy = random.uniform(0, H)
        shade = random.randint(-12, 16)
        flood.fill(LOAM[0] + shade, LOAM[1] + shade, LOAM[2] + shade, 38)
        flood.circle(gx, gy, random.uniform(8, 70))
    flood.end_draw()

    # initial gently sinuous channel spanning the frame
    n = 240
    xs = np.linspace(-40, W + 40, n)
    base_y = H * 0.5
    amp = 300.0
    phase = random.uniform(0, py5.TWO_PI)
    ys = base_y + amp * np.sin(xs / W * py5.TWO_PI * INIT_WAVES + phase)
    ys += np.random.normal(0, 6, n)
    cx, cy = _resample(xs, ys, DS)


def _migrate():
    global cx, cy
    curv = _curvature(cx, cy)
    wcurv = _upstream_weighted(curv)
    nx, ny = _normals(cx, cy)
    # deposit history BEFORE moving so scroll bars trail the channel
    flood.begin_draw()
    _deposit_floodplain(flood, cx, cy, nx, ny, curv)
    flood.end_draw()

    # curvature-driven outward migration (bends grow); clipped to stay stable
    rate = MIG_RATE * np.clip(wcurv * DS, -CURV_CAP, CURV_CAP)
    cx = cx - rate * nx
    cy = cy - rate * ny
    # cancel only the net vertical drift, then soft-cap large excursions
    cy = cy + (base_y - cy.mean()) * RECENTER
    excess = np.clip(np.abs(cy - base_y) - AMP_LIMIT, 0.0, None)
    cy = cy - np.sign(cy - base_y) * excess * 0.10
    # pin the inflow / outflow so the river enters and leaves the scene
    lin = np.linspace(-40, W + 40, len(cx))
    cx[0], cx[1], cx[2] = lin[0], lin[1], lin[2]
    cx[-1] = W + 40
    cx, cy = _resample(cx, cy, DS)

    res = _check_cutoff()
    if res is not None:
        flood.begin_draw()
        _fill_oxbow(flood, res[0], res[1])
        flood.end_draw()


def _draw_water():
    nx, ny = _normals(cx, cy)
    # soft outer glow band
    py5.no_stroke()
    py5.fill(WATER_DEEP[0], WATER_DEEP[1], WATER_DEEP[2], 90)
    py5.begin_shape()
    for i in range(len(cx)):
        py5.vertex(cx[i] + nx[i] * (CHANNEL_HALF + 6), cy[i] + ny[i] * (CHANNEL_HALF + 6))
    for i in range(len(cx) - 1, -1, -1):
        py5.vertex(cx[i] - nx[i] * (CHANNEL_HALF + 6), cy[i] - ny[i] * (CHANNEL_HALF + 6))
    py5.end_shape(py5.CLOSE)

    # channel body
    py5.fill(*WATER_DEEP)
    py5.begin_shape()
    for i in range(len(cx)):
        py5.vertex(cx[i] + nx[i] * CHANNEL_HALF, cy[i] + ny[i] * CHANNEL_HALF)
    for i in range(len(cx) - 1, -1, -1):
        py5.vertex(cx[i] - nx[i] * CHANNEL_HALF, cy[i] - ny[i] * CHANNEL_HALF)
    py5.end_shape(py5.CLOSE)

    # bright thalweg core
    py5.no_fill()
    py5.stroke(*WATER_CORE)
    py5.stroke_weight(3.0)
    py5.begin_shape()
    for i in range(len(cx)):
        py5.vertex(cx[i], cy[i])
    py5.end_shape()


def draw():
    for _ in range(SUBSTEPS):
        _migrate()

    py5.image(flood, 0, 0)
    _draw_water()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} "
              f"({py5.frame_count/TOTAL_FRAMES*100:.1f}%) nodes={len(cx)}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
        import os
        os._exit(0)


py5.run_sketch()

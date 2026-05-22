"""
phononic_crystal_lens  (revision 1)
====================================
2D FDTD scalar wave — phononic crystal metamaterial slab.
Fixes v0: softer scatterers (C_SCATTER 0.35), lower frequency (0.04 Hz/step)
to hit the pass-band, smaller scatterer radius (r=4) for better transmission.
The wave now visibly threads through the crystal and collimates on the far side.

Palette : amber (compression) | slate-indigo (rarefaction) | steel-blue (crystal)
Format  : 15 s @ 60 fps  →  phononic_crystal_lens.mp4
"""

from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

# ── constants ───────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS           # 900
PREVIEW_FRAME = TOTAL_FRAMES // 4           # 225
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# ── FDTD simulation grid ─────────────────────────────────────────────────────
GW, GH = 640, 360
SUBSTEPS = 3
DT       = 0.25
C_FREE   = 1.0
C_SCATTER = 0.35   # ← softer: allows more transmission through crystal
PML_D    = 20

# ── phononic crystal slab ────────────────────────────────────────────────────
XTAL_L   = GW * 2 // 5     # 256  (moved slightly left to give more room right)
XTAL_R   = GW * 3 // 5     # 384
XTAL_Y0  = GH // 8         # 45
XTAL_Y1  = GH * 7 // 8     # 315
LAT_SPACE = 24
SCAT_R    = 4               # ← smaller radius → more open channels

# ── wave source ──────────────────────────────────────────────────────────────
SRC_COL  = 30
SRC_FREQ = 0.04             # ← lower frequency → wider band, better transmission
SRC_AMP  = 1.0

# ── tracers ──────────────────────────────────────────────────────────────────
N_TRACERS = 120_000

# ── module-level state ───────────────────────────────────────────────────────
_p     = None
_p_pre = None
_c2    = None
_xtal  = None
_damp  = None
_tx    = None
_ty    = None
_step  = 0


def _build_c2_and_mask():
    c2   = np.full((GH, GW), C_FREE ** 2, dtype=np.float32)
    xtal = np.zeros((GH, GW), dtype=bool)
    for row_i, cy in enumerate(range(XTAL_Y0, XTAL_Y1, LAT_SPACE)):
        x_off = LAT_SPACE // 2 if (row_i % 2) else 0
        for cx in range(XTAL_L + x_off, XTAL_R, LAT_SPACE):
            gy_lo = max(0, cy - SCAT_R)
            gy_hi = min(GH, cy + SCAT_R + 1)
            gx_lo = max(0, cx - SCAT_R)
            gx_hi = min(GW, cx + SCAT_R + 1)
            gy_r = np.arange(gy_lo, gy_hi)[:, None]
            gx_r = np.arange(gx_lo, gx_hi)[None, :]
            circ = (gy_r - cy) ** 2 + (gx_r - cx) ** 2 <= SCAT_R ** 2
            c2  [gy_lo:gy_hi, gx_lo:gx_hi][circ] = C_SCATTER ** 2
            xtal[gy_lo:gy_hi, gx_lo:gx_hi][circ] = True
    return c2, xtal


def _build_damp():
    m = np.ones((GH, GW), dtype=np.float32)
    d = PML_D
    ramp = np.linspace(0.005, 1.0, d, dtype=np.float32) ** 2
    m[:d,  :]  *= ramp[:, None]
    m[-d:, :]  *= ramp[::-1, None]
    m[:,  :d]  *= ramp[None, :]
    m[:, -d:]  *= ramp[None, ::-1]
    return m


def _fdtd_step():
    global _p, _p_pre, _step
    lap = (
        np.roll(_p,  1, axis=1) +
        np.roll(_p, -1, axis=1) +
        np.roll(_p,  1, axis=0) +
        np.roll(_p, -1, axis=0) -
        4.0 * _p
    )
    p_new = (2.0 * _p - _p_pre + DT * DT * _c2 * lap) * _damp
    _p_pre = _p
    _p = p_new

    # Sinusoidal line source with smooth envelope
    env = min(1.0, _step / 60.0)
    _p[:, SRC_COL] += np.sin(2.0 * np.pi * SRC_FREQ * _step) * env * SRC_AMP

    # Hard-wall: zero pressure inside scatterers
    _p[_xtal]     = 0.0
    _p_pre[_xtal] = 0.0

    _step += 1


def setup():
    global _p, _p_pre, _c2, _xtal, _damp, _tx, _ty

    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)

    _p     = np.zeros((GH, GW), dtype=np.float32)
    _p_pre = np.zeros((GH, GW), dtype=np.float32)
    _c2, _xtal = _build_c2_and_mask()
    _damp  = _build_damp()

    _tx = np.random.uniform(0, GW, N_TRACERS).astype(np.float32)
    _ty = np.random.uniform(0, GH, N_TRACERS).astype(np.float32)

    print(f"[{WORK_NAME}] Setup OK  grid={GW}×{GH}  canvas={SIZE[0]}×{SIZE[1]}")


def draw():
    global _tx, _ty

    fc = py5.frame_count
    W, H = SIZE

    # ── FDTD substeps ──────────────────────────────────────────────────────
    for _ in range(SUBSTEPS):
        _fdtd_step()

    # ── pressure → RGB (grid coords) ──────────────────────────────────────
    p_norm = np.clip(_p / 1.2, -1.0, 1.0)
    pos = np.clip(p_norm,  0.0, 1.0)   # compression → amber
    neg = np.clip(-p_norm, 0.0, 1.0)   # rarefaction → indigo

    # Boost contrast: gamma
    pos = pos ** 0.7
    neg = neg ** 0.7

    r_g = (pos * 220 + 8).astype(np.int16)
    g_g = (pos * 65  + 6).astype(np.int16)
    b_g = (neg * 190 + 6).astype(np.int16)

    # Steel-blue tint on scatterer cells
    r_g[_xtal] = np.clip(r_g[_xtal] + 20, 0, 80)
    g_g[_xtal] = np.clip(g_g[_xtal] + 38, 0, 90)
    b_g[_xtal] = np.clip(b_g[_xtal] + 75, 0, 130)

    r_g = r_g.astype(np.uint8)
    g_g = g_g.astype(np.uint8)
    b_g = b_g.astype(np.uint8)

    # ── upscale grid → canvas via kron ────────────────────────────────────
    sx = W // GW
    sy = H // GH
    ones = np.ones((sy, sx), dtype=np.uint8)
    r_up = np.kron(r_g, ones)[:H, :W]
    g_up = np.kron(g_g, ones)[:H, :W]
    b_up = np.kron(b_g, ones)[:H, :W]

    # ── tracer particles ───────────────────────────────────────────────────
    ix = np.clip(_tx.astype(np.int32), 1, GW - 2)
    iy = np.clip(_ty.astype(np.int32), 1, GH - 2)
    dpx = (_p[iy, ix + 1] - _p[iy, ix - 1]) * 0.5
    dpy = (_p[iy + 1, ix] - _p[iy - 1, ix]) * 0.5
    noise = np.random.normal(0, 0.10, N_TRACERS).astype(np.float32)
    _tx += dpx * 1.5 + noise
    _ty += dpy * 1.5 + noise

    oob = (_tx < 0) | (_tx >= GW) | (_ty < 0) | (_ty >= GH)
    n_oob = int(oob.sum())
    if n_oob:
        _tx[oob] = np.random.uniform(0, GW, n_oob).astype(np.float32)
        _ty[oob] = np.random.uniform(0, GH, n_oob).astype(np.float32)

    pix_x = np.clip((_tx * (W / GW)).astype(np.int32), 0, W - 1)
    pix_y = np.clip((_ty * (H / GH)).astype(np.int32), 0, H - 1)

    r_up_i = r_up.astype(np.int16)
    g_up_i = g_up.astype(np.int16)
    b_up_i = b_up.astype(np.int16)
    np.add.at(r_up_i, (pix_y, pix_x), 20)
    np.add.at(g_up_i, (pix_y, pix_x), 24)
    np.add.at(b_up_i, (pix_y, pix_x), 36)
    r_up = np.clip(r_up_i, 0, 255).astype(np.uint8)
    g_up = np.clip(g_up_i, 0, 255).astype(np.uint8)
    b_up = np.clip(b_up_i, 0, 255).astype(np.uint8)

    # ── write pixel buffer ─────────────────────────────────────────────────
    py5.load_np_pixels()
    ah, aw = py5.np_pixels.shape[:2]
    py5.np_pixels[:ah, :aw, 0] = 255
    py5.np_pixels[:ah, :aw, 1] = r_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 2] = g_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 3] = b_up[:ah, :aw]
    py5.update_np_pixels()

    # ── save frame ─────────────────────────────────────────────────────────
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % FPS == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES}"
              f" ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[FFmpeg] Encoding {TOTAL_FRAMES} frames …")
        subprocess.run([
            "ffmpeg", "-y",
            "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Cleanup] Frames directory removed.")


py5.run_sketch()

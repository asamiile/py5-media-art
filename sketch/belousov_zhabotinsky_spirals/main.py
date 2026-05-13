"""
belousov_zhabotinsky_spirals
----------------------------
Belousov-Zhabotinsky (BZ) reaction simulation using a continuous
three-variable excitable medium model (Barkley model variant).

The field evolves via:
  u_{t+1} = u + dt*(u*(1-u)*(u - (v+b)/a) + Du*laplacian(u))
  v_{t+1} = v + dt*(u - v)

where u = activator (excitation), v = inhibitor (refractory).
Spiral waves form spontaneously from broken-symmetry seeds.

Palette: near-black → deep crimson → warm amber-ochre → ivory wavefront
Format : 20 seconds @ 60 fps, 4K MP4
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

# ── constants ─────────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME   = SKETCH_DIR.name
FRAMES_DIR  = SKETCH_DIR / "frames"

DURATION_SEC  = 20
FPS           = 60
TOTAL_FRAMES  = DURATION_SEC * FPS
PREVIEW_FRAME = TOTAL_FRAMES // 2          # grab mid-point frame as preview

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()
GRID_W, GRID_H = 768, 432                  # simulation resolution
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
STEPS_PER_FRAME = 6
sim_tick = 0

# ── Barkley parameters ────────────────────────────────────────────────────────
A   = 0.74    # threshold parameter
B   = 0.035   # excitability
EPS = 0.080   # time-scale separation (fast u, slow v)
DT  = 0.030   # integration timestep
DU  = 0.220   # diffusion of activator
DV  = 0.015   # weak inhibitor diffusion softens refractory wakes

# ── palette  ──────────────────────────────────────────────────────────────────
# u in [0,1] → RGBA; map through 5-stop gradient
# 0.0 → #0c0608  (near-black charcoal)
# 0.2 → #3d0a10  (deep maroon)
# 0.5 → #8b1a1a  (crimson)
# 0.75→ #c47b14  (warm amber-ochre)
# 1.0 → #f5efe0  (ivory wavefront)
PALETTE_U = np.array([0.0, 0.2, 0.5, 0.75, 1.0])
PALETTE_R = np.array([12,  61,  139, 196,  245], dtype=np.float32)
PALETTE_G = np.array([6,   10,  26,  123,  239], dtype=np.float32)
PALETTE_B = np.array([8,   16,  26,  20,   224], dtype=np.float32)

# ── state ─────────────────────────────────────────────────────────────────────
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
v = np.zeros((GRID_H, GRID_W), dtype=np.float32)
yy, xx = np.indices((GRID_H, GRID_W), dtype=np.float32)
nx = xx / (GRID_W - 1)
ny = yy / (GRID_H - 1)
grain = np.zeros((GRID_H, GRID_W), dtype=np.float32)
pacemakers = []

def _seed_spirals():
    """Plant broken wavefronts that evolve into counter-rotating spirals."""
    global grain, pacemakers
    rng = np.random.default_rng(seed=None)   # no fixed seed — different every run
    grain = rng.normal(0.0, 1.0, (GRID_H, GRID_W)).astype(np.float32)
    for _ in range(5):
        grain = (
            grain
            + np.roll(grain, 1, 0)
            + np.roll(grain, -1, 0)
            + np.roll(grain, 1, 1)
            + np.roll(grain, -1, 1)
        ) / 5.0
    grain = (grain - grain.min()) / (grain.max() - grain.min() + 1e-6)

    pacemakers = [
        (0.20, 0.26, 1.0, 0.090),
        (0.46, 0.64, -1.0, 0.105),
        (0.72, 0.33, 1.0, 0.082),
        (0.83, 0.78, -1.0, 0.095),
    ]
    for px, py, charge, spacing in pacemakers:
        dx = nx - px
        dy = (ny - py) * (GRID_H / GRID_W)
        radius = np.sqrt(dx * dx + dy * dy)
        angle = np.arctan2(dy, dx)
        phase = charge * angle + radius / spacing
        mask = radius < 0.34
        front = np.exp(-((np.sin(phase) - 0.92) ** 2) / 0.018) * mask
        refractory = np.exp(-((np.sin(phase + 0.85) - 0.80) ** 2) / 0.045) * mask
        u[:] = np.maximum(u, front.astype(np.float32))
        v[:] = np.maximum(v, (refractory * 0.55).astype(np.float32))

    for _ in range(22):
        cy = rng.integers(18, GRID_H - 18)
        cx = rng.integers(18, GRID_W - 18)
        r = rng.integers(5, 11)
        patch = (yy - cy) ** 2 + (xx - cx) ** 2 < r ** 2
        u[patch] = rng.uniform(0.65, 1.0)


_seed_spirals()


def _laplacian(field):
    """2D discrete Laplacian with periodic boundaries."""
    return (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
        4 * field
    )


def _step():
    global u, v, sim_tick
    sim_tick += 1
    lap_u = _laplacian(u)
    lap_v = _laplacian(v)
    # Barkley activator/inhibitor update
    threshold = (v + B) / A
    f_u = (u * (1 - u) * (u - threshold)) / EPS
    du  = DT * (f_u + DU * lap_u)
    dv  = DT * (u - v + DV * lap_v)
    u = np.clip(u + du, 0.0, 1.0)
    v = np.clip(v + dv, 0.0, 1.0)

    drive = np.zeros_like(u)
    for px, py, charge, spacing in pacemakers:
        dx = nx - px
        dy = (ny - py) * (GRID_H / GRID_W)
        radius = np.sqrt(dx * dx + dy * dy)
        angle = np.arctan2(dy, dx)
        phase = charge * angle + radius / spacing - sim_tick * 0.018
        source = np.exp(-((np.sin(phase) - 0.965) ** 2) / 0.006)
        envelope = np.exp(-(radius ** 2) / 0.075)
        drive = np.maximum(drive, source * envelope)
    u = np.maximum(u, drive.astype(np.float32) * (0.82 - v * 0.40))


def _u_to_rgb(u_field):
    """Map activator field into a warm BZ reaction palette."""
    u_flat = u_field.ravel()
    r = np.interp(u_flat, PALETTE_U, PALETTE_R).reshape(GRID_H, GRID_W)
    g = np.interp(u_flat, PALETTE_U, PALETTE_G).reshape(GRID_H, GRID_W)
    b = np.interp(u_flat, PALETTE_U, PALETTE_B).reshape(GRID_H, GRID_W)
    edge = np.hypot(np.gradient(u_field, axis=0), np.gradient(u_field, axis=1))
    edge = np.clip(edge * 5.5, 0.0, 1.0)
    r += edge * 78.0 + grain * 5.0
    g += edge * 48.0 + grain * 3.0
    b += edge * 18.0 + grain * 2.0
    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb, 0.0, 255.0).astype(np.uint8)


# pre-compute upscale grid for efficiency
from PIL import Image as _PILImage


def _render_frame():
    """Render current u field into py5 using the actual pixel buffer size."""
    rgb = _u_to_rgb(np.clip(u * 0.92 + v * 0.18, 0.0, 1.0))
    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]
    pil  = _PILImage.fromarray(rgb, "RGB")
    pil  = pil.resize((actual_w, actual_h), _PILImage.LANCZOS)
    arr  = np.asarray(pil)                     # shape (H, W, 3) uint8 RGB
    # py5 np_pixels expects ARGB order
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = arr[..., 0]
    py5.np_pixels[..., 2] = arr[..., 1]
    py5.np_pixels[..., 3] = arr[..., 2]
    py5.update_np_pixels()


# ── py5 sketch ────────────────────────────────────────────────────────────────
def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)
    # warm up simulation so spirals are already forming on first frame
    for _ in range(260):
        _step()


def draw():
    # advance simulation a few steps per rendered frame for richer motion
    for _ in range(STEPS_PER_FRAME):
        _step()

    _render_frame()

    fc = py5.frame_count
    frame_path = str(FRAMES_DIR / f"frame-{fc:04d}.png")
    py5.save_frame(frame_path)

    if fc == PREVIEW_FRAME:
        shutil.copy(frame_path,
                    str(SKETCH_DIR / PREVIEW_FILENAME))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        output_path = SKETCH_DIR / "output.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-r", str(FPS),
            "-start_number", "1",
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(output_path),
        ], check=True)
        shutil.copyfile(output_path, SKETCH_DIR / f"{WORK_NAME}.mp4")


py5.run_sketch()

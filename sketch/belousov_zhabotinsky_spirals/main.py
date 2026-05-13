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
GRID_W, GRID_H = 512, 512                  # simulation resolution
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# ── Barkley parameters ────────────────────────────────────────────────────────
A   = 0.75    # threshold parameter
B   = 0.01    # excitability
EPS = 0.02    # time-scale separation (fast u, slow v)
DT  = 0.4     # integration timestep
DU  = 1.0     # diffusion of activator
DV  = 0.0     # inhibitor is local (non-diffusing)

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

def _seed_spirals():
    """Plant a handful of broken-symmetry seeds that produce counter-rotating spirals."""
    rng = np.random.default_rng(seed=None)   # no fixed seed — different every run
    centres = [
        (GRID_H // 4,     GRID_W // 4),
        (GRID_H // 4,     3 * GRID_W // 4),
        (3 * GRID_H // 4, GRID_W // 4),
        (3 * GRID_H // 4, 3 * GRID_W // 4),
        (GRID_H // 2,     GRID_W // 2),
    ]
    for cy, cx in centres:
        r  = 22
        y0, y1 = max(0, cy - r), min(GRID_H, cy + r)
        x0, x1 = max(0, cx - r), min(GRID_W, cx + r)
        # half-circle of u=1, other half v=0.5 (asymmetric seed → spiral)
        ys = np.arange(y0, y1)[:, None]
        xs = np.arange(x0, x1)[None, :]
        in_circle = ((ys - cy) ** 2 + (xs - cx) ** 2) < r ** 2
        left_half = (xs - cx) <= 0
        u[y0:y1, x0:x1] = np.where(in_circle & left_half, 1.0, u[y0:y1, x0:x1])
        v[y0:y1, x0:x1] = np.where(in_circle & ~left_half, 0.5, v[y0:y1, x0:x1])
    # a few scattered random sparks
    ry = rng.integers(10, GRID_H - 10, 8)
    rx = rng.integers(10, GRID_W - 10, 8)
    for cy, cx in zip(ry, rx):
        u[cy - 3: cy + 3, cx - 3: cx + 3] = 1.0


_seed_spirals()


def _laplacian(field):
    """2D discrete Laplacian with periodic boundaries."""
    return (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
        4 * field
    )


def _step():
    global u, v
    lap_u = _laplacian(u)
    # Barkley activator/inhibitor update
    f_u = u * (1 - u) * (u - (v + B) / A)
    du  = DT * (f_u + DU * lap_u)
    dv  = EPS * DT * (u - v)
    u = np.clip(u + du, 0.0, 1.0)
    v = np.clip(v + dv, 0.0, 1.0)


def _u_to_rgba(u_field):
    """Map activator field u ∈ [0,1] → RGBA uint8 array (H, W, 4)."""
    u_flat = u_field.ravel()
    r = np.interp(u_flat, PALETTE_U, PALETTE_R).reshape(GRID_H, GRID_W)
    g = np.interp(u_flat, PALETTE_U, PALETTE_G).reshape(GRID_H, GRID_W)
    b = np.interp(u_flat, PALETTE_U, PALETTE_B).reshape(GRID_H, GRID_W)
    a = np.full_like(r, 255)
    rgba = np.stack([r, g, b, a], axis=-1).astype(np.uint8)
    return rgba


# pre-compute upscale grid for efficiency
from PIL import Image as _PILImage


def _render_frame():
    """Render current u field into py5 using the actual pixel buffer size."""
    rgba = _u_to_rgba(u)
    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]
    pil  = _PILImage.fromarray(rgba, "RGBA")
    pil  = pil.resize((actual_w, actual_h), _PILImage.LANCZOS)
    arr  = np.asarray(pil)                     # shape (H, W, 4) uint8 RGBA
    # py5 np_pixels expects ARGB order
    py5.np_pixels[:, :, :] = arr[:, :, [3, 0, 1, 2]]
    py5.update_np_pixels()


# ── py5 sketch ────────────────────────────────────────────────────────────────
def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)
    # warm up simulation so spirals are already forming on first frame
    for _ in range(60):
        _step()


def draw():
    # advance simulation a few steps per rendered frame for richer motion
    for _ in range(4):
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

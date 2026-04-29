from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 120

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Theme: "Dust settling" — Peter de Jong attractor, parchment-on-black
# Parameters chosen for an intricate, filigree-like structure
A, B, C, D = -2.0, -2.0, -1.2, 2.0

N_TRAJ  = 5000
N_STEPS = 2500
BURN_IN = 300

# Palette: near-black → cold dim blue-gray → warm sand/parchment at peak
BG_COL      = np.array([6,   6,  10], dtype=np.float32) / 255.0
LOW_COL     = np.array([30,  32,  48], dtype=np.float32) / 255.0  # dim blue-gray
HIGH_COL    = np.array([212, 196, 160], dtype=np.float32) / 255.0 # warm parchment


def setup():
    py5.size(*SIZE)

    rng = np.random.default_rng()
    x = rng.uniform(-0.5, 0.5, N_TRAJ)
    y = rng.uniform(-0.5, 0.5, N_TRAJ)

    chunks_x, chunks_y = [], []
    for step in range(N_STEPS):
        # Peter de Jong map
        xn = np.sin(A * y) - np.cos(B * x)
        yn = np.sin(C * x) - np.cos(D * y)
        x, y = xn, yn
        if step >= BURN_IN:
            chunks_x.append(x.copy())
            chunks_y.append(y.copy())

    xs = np.concatenate(chunks_x)
    ys = np.concatenate(chunks_y)

    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    margin = 80

    px = ((xs - xs.min()) / (xs.max() - xs.min()) * (w - 2 * margin) + margin).astype(np.int32)
    py_arr = ((ys - ys.min()) / (ys.max() - ys.min()) * (h - 2 * margin) + margin).astype(np.int32)
    np.clip(px, 0, w - 1, out=px)
    np.clip(py_arr, 0, h - 1, out=py_arr)

    density = np.zeros((h, w), dtype=np.float32)
    np.add.at(density, (py_arr, px), 1.0)

    d = np.log1p(density)
    d /= d.max()   # 0 (empty) → 1 (peak density)

    # Color: interpolate LOW_COL → HIGH_COL; brightness by d^0.45 for fine grain
    brightness = d ** 0.45
    r = (LOW_COL[0] * (1 - d) + HIGH_COL[0] * d) * brightness
    g = (LOW_COL[1] * (1 - d) + HIGH_COL[1] * d) * brightness
    b = (LOW_COL[2] * (1 - d) + HIGH_COL[2] * d) * brightness

    r_px = np.clip(r * 255, 0, 255).astype(np.uint8)
    g_px = np.clip(g * 255, 0, 255).astype(np.uint8)
    b_px = np.clip(b * 255, 0, 255).astype(np.uint8)
    alpha = np.full((h, w), 255, dtype=np.uint8)

    py5.np_pixels[:, :, 0] = alpha
    py5.np_pixels[:, :, 1] = r_px
    py5.np_pixels[:, :, 2] = g_px
    py5.np_pixels[:, :, 3] = b_px
    py5.update_np_pixels()


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

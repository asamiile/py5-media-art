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
PREVIEW_FRAME = 60

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Theme: "Deep frond" — Barnsley's IFS fern rendered as a density-accumulated glow field
# Technique: four affine transforms applied stochastically to 800k points;
# each point's transform index (stem / main frond / left sub / right sub) drives color;
# log-scale density mapping reveals structural layers

# IFS transform coefficients: (a, b, c, d, e, f, prob)
TRANSFORMS = [
    ( 0.00,  0.00,  0.00,  0.16,  0.00,  0.00, 0.01),  # stem
    ( 0.85,  0.04, -0.04,  0.85,  0.00,  1.60, 0.85),  # main frond (self-similar)
    ( 0.20, -0.26,  0.23,  0.22,  0.00,  1.60, 0.07),  # left sub-frond
    (-0.15,  0.28,  0.26,  0.24,  0.00,  0.44, 0.07),  # right sub-frond
]

N_POINTS = 800_000

# Palette: very dark moss → rich fern green → pale lime tip
BG_COL    = np.array([  6,  10,   5], dtype=np.uint8)
COL_DARK  = np.array([ 14,  42,  18], dtype=np.float32)   # low density — dark canopy
COL_MID   = np.array([ 55, 148,  72], dtype=np.float32)   # mid density — fern green
COL_LIGHT = np.array([215, 238, 175], dtype=np.float32)   # high density — pale tip glow

# Fern coordinate bounds (Barnsley coords)
X_MIN, X_MAX = -2.6,  2.8
Y_MIN, Y_MAX =  0.0, 10.0


def ifs_iterate(n_points):
    """Run the Barnsley fern IFS for n_points steps, return (xs, ys)."""
    probs = np.array([t[6] for t in TRANSFORMS], dtype=np.float64)
    probs /= probs.sum()
    cum = np.cumsum(probs)

    A = np.array([t[0] for t in TRANSFORMS])
    B = np.array([t[1] for t in TRANSFORMS])
    C = np.array([t[2] for t in TRANSFORMS])
    D = np.array([t[3] for t in TRANSFORMS])
    E = np.array([t[4] for t in TRANSFORMS])
    F = np.array([t[5] for t in TRANSFORMS])

    rng = np.random.default_rng()
    t_ids = np.searchsorted(cum, rng.random(n_points + 50))  # +50 burnin

    xs = np.empty(n_points, dtype=np.float32)
    ys = np.empty(n_points, dtype=np.float32)
    x, y = 0.0, 0.0
    for i in range(n_points + 50):
        ti = t_ids[i]
        x, y = A[ti] * x + B[ti] * y + E[ti], C[ti] * x + D[ti] * y + F[ti]
        if i >= 50:
            xs[i - 50] = x
            ys[i - 50] = y

    return xs, ys


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    xs, ys = ifs_iterate(N_POINTS)

    # Map fern coords to pixel coords (center horizontally, margin vertically)
    x_range = X_MAX - X_MIN
    y_range = Y_MAX - Y_MIN
    scale = H * 0.93 / y_range
    margin_y = int(H * 0.03)

    px = np.clip(((xs - (X_MIN + X_MAX) / 2) * scale + W / 2).astype(np.int32), 0, W - 1)
    py_coord = np.clip((H - margin_y - (ys - Y_MIN) * scale).astype(np.int32), 0, H - 1)

    # Accumulate density
    density = np.zeros((H, W), dtype=np.float32)
    np.add.at(density, (py_coord, px), 1.0)

    # Log-scale and normalize to [0, 1]
    density = np.log1p(density * 60.0)
    density /= density.max() + 1e-8

    # Color mapping: 3-stop gradient BG → COL_DARK → COL_MID → COL_LIGHT
    t1 = np.clip(density * 3.0, 0.0, 1.0)        # dark → mid
    t2 = np.clip(density * 3.0 - 1.0, 0.0, 1.0)  # mid → light
    t3 = np.clip(density * 3.0 - 2.0, 0.0, 1.0)  # light tip

    r_ch = (COL_DARK[0] * (1 - t1) + COL_MID[0] * t1
            + (COL_LIGHT[0] - COL_MID[0]) * t3).astype(np.uint8)
    g_ch = (COL_DARK[1] * (1 - t1) + COL_MID[1] * t1
            + (COL_LIGHT[1] - COL_MID[1]) * t3).astype(np.uint8)
    b_ch = (COL_DARK[2] * (1 - t1) + COL_MID[2] * t1
            + (COL_LIGHT[2] - COL_MID[2]) * t3).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != H or w_buf != W:
        # Retina: upscale 2× with nearest-neighbour
        r_ch = np.repeat(np.repeat(r_ch, 2, axis=0), 2, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, 2, axis=0), 2, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, 2, axis=0), 2, axis=1)

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 2] = g_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 3] = b_ch[:h_buf, :w_buf]
    py5.update_np_pixels()


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

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

# Theme: "Boundary of infinity" — the Mandelbrot set; each pixel is a parameter c,
# colored by how long z² + c takes to escape — revealing the fractal coastline
# where bounded and unbounded orbits meet.

# View window (Mandelbrot parameter space)
X_MIN, X_MAX = -2.40,  0.85
Y_MID        =  0.00
Y_HALF       = (X_MAX - X_MIN) * SIZE[1] / SIZE[0] / 2  # maintain aspect

MAX_ITER     = 280
ESCAPE_R     = 2.0

# Palette: near-black interior; deep violet far-escaped → warm amber → pale gold at boundary
INT_COL    = np.array([  4,   3,  14], dtype=np.float32)   # interior (bounded)
COL_FAR    = np.array([ 12,   8,  38], dtype=np.float32)   # fast escape — deep violet
COL_MID    = np.array([168,  96,  28], dtype=np.float32)   # medium iter — burnt amber
COL_NEAR   = np.array([245, 232, 188], dtype=np.float32)   # slow escape — pale gold


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    x = np.linspace(X_MIN, X_MAX, W, dtype=np.float64)
    y = np.linspace(Y_MID + Y_HALF, Y_MID - Y_HALF, H, dtype=np.float64)
    C = x[np.newaxis, :] + 1j * y[:, np.newaxis]   # shape (H, W)

    Z = np.zeros((H, W), dtype=np.complex128)
    # smooth iteration count (0 = interior / never escaped)
    smooth_iter = np.zeros((H, W), dtype=np.float64)
    escaped = np.zeros((H, W), dtype=bool)

    for i in range(MAX_ITER):
        mask = ~escaped
        if not mask.any():
            break
        Z[mask] = Z[mask] ** 2 + C[mask]
        newly = mask & (np.abs(Z) > ESCAPE_R)
        if newly.any():
            # Smooth colouring: nu = i + 1 - log₂(log₂|z|)
            abs_z = np.abs(Z[newly])
            nu = (i + 1) - np.log2(np.maximum(np.log2(abs_z), 1e-8))
            smooth_iter[newly] = np.maximum(nu, 0.0)
        escaped |= newly

    # Normalize escaped pixels to [0, 1]
    interior = ~escaped
    t_raw = smooth_iter.copy()
    mx = t_raw[escaped].max() if escaped.any() else 1.0
    t = t_raw / (mx + 1e-8)     # 0 = fast escape, 1 = slow (near boundary)

    # 3-stop gradient: far → mid → near
    t2 = np.clip(t * 2.0,       0.0, 1.0)   # far → mid
    t3 = np.clip(t * 2.0 - 1.0, 0.0, 1.0)  # mid → near

    r_ch = (COL_FAR[0] * (1 - t2) + COL_MID[0] * t2 + (COL_NEAR[0] - COL_MID[0]) * t3)
    g_ch = (COL_FAR[1] * (1 - t2) + COL_MID[1] * t2 + (COL_NEAR[1] - COL_MID[1]) * t3)
    b_ch = (COL_FAR[2] * (1 - t2) + COL_MID[2] * t2 + (COL_NEAR[2] - COL_MID[2]) * t3)

    # Interior
    r_ch[interior] = INT_COL[0]
    g_ch[interior] = INT_COL[1]
    b_ch[interior] = INT_COL[2]

    r_ch = np.clip(r_ch, 0, 255).astype(np.uint8)
    g_ch = np.clip(g_ch, 0, 255).astype(np.uint8)
    b_ch = np.clip(b_ch, 0, 255).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != H or w_buf != W:
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

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

# Theme: "Ordered chaos" — the Hilbert space-filling curve at order 8 (256×256 cells);
# each cell is colored by its 1D position along the curve's path, revealing how
# a single winding thread can cover all of 2D space without crossing itself.

ORDER    = 8         # 2^ORDER × 2^ORDER = 256×256 = 65536 cells
N        = 1 << ORDER   # 256

# Cyclic palette: 3-stop colors that cycle N_CYCLES times along the curve;
# the cycling makes the winding path visible as alternating colour bands.
N_CYCLES  = 20
COL_A     = np.array([ 22,  14,  72], dtype=np.float32)   # deep indigo
COL_B     = np.array([ 14, 158, 152], dtype=np.float32)   # cyan-teal
COL_C     = np.array([222, 174,  32], dtype=np.float32)   # warm amber

BG_COL    = np.array([  8,   6,  14], dtype=np.uint8)     # near-black margins


def hilbert_xy(order):
    """Vectorised d→(x,y) mapping for the Hilbert curve of given order."""
    n_pts = (1 << order) ** 2
    d = np.arange(n_pts, dtype=np.int64)
    x = np.zeros(n_pts, dtype=np.int64)
    y = np.zeros(n_pts, dtype=np.int64)

    s = 1
    d_tmp = d.copy()
    while s < (1 << order):
        rx = (d_tmp >> 1) & 1
        ry = (d_tmp & 1) ^ rx

        rot_mask  = ry == 0
        flip_mask = rot_mask & (rx == 1)

        x[flip_mask] = (s - 1) - x[flip_mask]
        y[flip_mask] = (s - 1) - y[flip_mask]

        x_tmp = x[rot_mask].copy()
        x[rot_mask] = y[rot_mask]
        y[rot_mask] = x_tmp

        x += s * rx
        y += s * ry

        d_tmp >>= 2
        s     <<= 1

    return x.astype(np.int32), y.astype(np.int32)


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    xs, ys = hilbert_xy(ORDER)   # each in [0, N-1]
    n_pts  = N * N

    # Cyclic color: t oscillates N_CYCLES times so the winding path becomes visible
    t_lin = np.linspace(0.0, 1.0, n_pts, dtype=np.float32)
    t     = (t_lin * N_CYCLES) % 1.0      # repeating [0,1) sawtooth
    t2    = np.clip(t * 2.0, 0.0, 1.0)
    t3    = np.clip(t * 2.0 - 1.0, 0.0, 1.0)

    r_flat = (COL_A[0]*(1-t2) + COL_B[0]*t2 + (COL_C[0]-COL_B[0])*t3).astype(np.uint8)
    g_flat = (COL_A[1]*(1-t2) + COL_B[1]*t2 + (COL_C[1]-COL_B[1])*t3).astype(np.uint8)
    b_flat = (COL_A[2]*(1-t2) + COL_B[2]*t2 + (COL_C[2]-COL_B[2])*t3).astype(np.uint8)

    # Place colors into a (N, N) grid ordered by Hilbert index
    grid_r = np.full((N, N), BG_COL[0], dtype=np.uint8)
    grid_g = np.full((N, N), BG_COL[1], dtype=np.uint8)
    grid_b = np.full((N, N), BG_COL[2], dtype=np.uint8)
    grid_r[ys, xs] = r_flat
    grid_g[ys, xs] = g_flat
    grid_b[ys, xs] = b_flat

    # Scale up: cell_size = H // N = 1080 // 256 = 4 px
    cell_size = H // N
    scaled_r = np.repeat(np.repeat(grid_r, cell_size, axis=0), cell_size, axis=1)  # (1024, 1024)
    scaled_g = np.repeat(np.repeat(grid_g, cell_size, axis=0), cell_size, axis=1)
    scaled_b = np.repeat(np.repeat(grid_b, cell_size, axis=0), cell_size, axis=1)

    gh, gw = scaled_r.shape   # 1024 × 1024
    x_off  = (W - gw) // 2    # 448 px left margin

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    # Fill background
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = BG_COL[0]
    py5.np_pixels[:, :, 2] = BG_COL[1]
    py5.np_pixels[:, :, 3] = BG_COL[2]

    # Retina: buffer may be 2× logical size
    if h_buf == H and w_buf == W:
        py5.np_pixels[:gh, x_off:x_off+gw, 1] = scaled_r
        py5.np_pixels[:gh, x_off:x_off+gw, 2] = scaled_g
        py5.np_pixels[:gh, x_off:x_off+gw, 3] = scaled_b
    else:
        # 2× upscale
        sr2 = np.repeat(np.repeat(scaled_r, 2, axis=0), 2, axis=1)
        sg2 = np.repeat(np.repeat(scaled_g, 2, axis=0), 2, axis=1)
        sb2 = np.repeat(np.repeat(scaled_b, 2, axis=0), 2, axis=1)
        gh2, gw2 = sr2.shape
        x_off2 = (w_buf - gw2) // 2
        py5.np_pixels[:gh2, x_off2:x_off2+gw2, 1] = sr2
        py5.np_pixels[:gh2, x_off2:x_off2+gw2, 2] = sg2
        py5.np_pixels[:gh2, x_off2:x_off2+gw2, 3] = sb2

    py5.update_np_pixels()


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

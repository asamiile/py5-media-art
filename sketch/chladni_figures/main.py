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

# Theme: "Resonance geometry" — Chladni figures: sand settles at nodal lines
# of a vibrating square plate. The pattern is f(x,y) = superposition of modes.
# Sand accumulates where |f| < threshold → reveals standing-wave geometry.

# Superposition of multiple vibrational modes
# Each mode: amplitude * sin(m*π*x) * sin(n*π*y) + sin(n*π*x) * sin(m*π*y)
# The symmetric sum gives the rotational symmetry of Chladni figures
MODES = [
    # (m, n, amplitude)
    (3, 5, 1.00),
    (5, 3, 0.85),
    (4, 7, 0.55),
    (7, 4, 0.45),
    (2, 9, 0.30),
]

# Sand / node threshold — tune for density of lines
THRESHOLD = 0.08

# Palette: warm dark felt background, sand-white nodes, subtle gold mid-tone
BG_COL     = np.array([18,  14,  10], dtype=np.float32)   # #120e0a dark felt
SAND_COL   = np.array([228, 218, 188], dtype=np.float32)  # #e4dab  pale sand
GOLD_COL   = np.array([180, 148,  80], dtype=np.float32)  # #b49450 dull gold mid

pixels_arr = None


def setup():
    global pixels_arr
    py5.size(*SIZE)

    H, W = SIZE[1], SIZE[0]

    # Square plate occupies full height; centered horizontally
    plate_h = H
    plate_w = H   # square
    plate_x0 = (W - plate_w) // 2

    # Coordinate grid over [0,1]×[0,1] for the plate
    x = np.linspace(0, 1, plate_w, dtype=np.float32)
    y = np.linspace(0, 1, plate_h, dtype=np.float32)
    X, Y = np.meshgrid(x, y)  # (plate_h, plate_w)

    # Compute superposed vibrational field
    field = np.zeros((plate_h, plate_w), dtype=np.float32)
    for m, n, amp in MODES:
        # Symmetric combination for square plate (4-fold symmetry)
        term = (np.sin(m * np.pi * X) * np.sin(n * np.pi * Y) +
                np.sin(n * np.pi * X) * np.sin(m * np.pi * Y))
        field += amp * term

    # Normalize field to [-1, 1]
    mx = np.abs(field).max()
    if mx > 0:
        field /= mx

    # Sand accumulates at nodal lines where |field| ≈ 0
    f_abs = np.abs(field)

    # Three-zone coloring:
    # |f| < THRESHOLD*0.3 → dense sand (pale sand)
    # THRESHOLD*0.3 < |f| < THRESHOLD → sparse sand (gold)
    # |f| > THRESHOLD → plate surface (background)
    dense  = f_abs < THRESHOLD * 0.35
    sparse = (f_abs >= THRESHOLD * 0.35) & (f_abs < THRESHOLD)
    bg     = f_abs >= THRESHOLD

    # Smooth alpha for the transition zone
    t_sparse = np.where(sparse,
        1.0 - (f_abs - THRESHOLD * 0.35) / (THRESHOLD * 0.65),
        0.0)

    r_plate = np.where(dense, SAND_COL[0],
              np.where(sparse, SAND_COL[0] * t_sparse + GOLD_COL[0] * (1 - t_sparse),
              BG_COL[0]))
    g_plate = np.where(dense, SAND_COL[1],
              np.where(sparse, SAND_COL[1] * t_sparse + GOLD_COL[1] * (1 - t_sparse),
              BG_COL[1]))
    b_plate = np.where(dense, SAND_COL[2],
              np.where(sparse, SAND_COL[2] * t_sparse + GOLD_COL[2] * (1 - t_sparse),
              BG_COL[2]))

    # Build full canvas (left/right margins in bg color)
    r_full = np.full((H, W), BG_COL[0], dtype=np.float32)
    g_full = np.full((H, W), BG_COL[1], dtype=np.float32)
    b_full = np.full((H, W), BG_COL[2], dtype=np.float32)

    r_full[:, plate_x0:plate_x0 + plate_w] = r_plate
    g_full[:, plate_x0:plate_x0 + plate_w] = g_plate
    b_full[:, plate_x0:plate_x0 + plate_w] = b_plate

    r_px = np.clip(r_full, 0, 255).astype(np.uint8)
    g_px = np.clip(g_full, 0, 255).astype(np.uint8)
    b_px = np.clip(b_full, 0, 255).astype(np.uint8)

    alpha = np.full((H, W), 255, dtype=np.uint8)
    small = np.stack([alpha, r_px, g_px, b_px], axis=-1)

    # Build at Retina size
    pixels_arr = np.repeat(np.repeat(small, 2, axis=0), 2, axis=1)


def draw():
    py5.load_np_pixels()
    py5.np_pixels[:] = pixels_arr
    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

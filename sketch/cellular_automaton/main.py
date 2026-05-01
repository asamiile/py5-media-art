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

CELL = 2
COLS = SIZE[0] // CELL   # 960
ROWS = SIZE[1] // CELL   # 540
RULE = 110   # Rule 110 — Turing-complete, aperiodic complex patterns

# Ice-blue palette — brightness only, no hue shift
# dead cell: #050810  recent: #e8f4ff  old: #b8d4e8
BG_RGB  = np.array([5,   8,  16], dtype=np.uint8)    # background / dead
NEW_RGB = np.array([232, 244, 255], dtype=np.uint8)   # just-born cell
OLD_RGB = np.array([184, 212, 232], dtype=np.uint8)   # older cell

pixels_arr = None


def build_rule_lut(rule_num):
    return np.array([(rule_num >> i) & 1 for i in range(8)], dtype=np.uint8)


def evolve(rule_lut):
    grid = np.zeros((ROWS, COLS), dtype=np.uint8)
    # Complex initial row — Rule 110 needs non-trivial start to fill canvas
    grid[0] = np.random.randint(0, 2, COLS, dtype=np.uint8)

    for gen in range(1, ROWS):
        row = grid[gen - 1]
        left  = np.roll(row,  1)
        right = np.roll(row, -1)
        triple = (left << 2) | (row << 1) | right
        grid[gen] = rule_lut[triple]

    return grid


def build_pixels(grid):
    rows, cols = grid.shape

    # Brightness by generation (recency): top row = most recent pattern start
    # We want newer rows (lower index) to appear slightly brighter
    gen_frac = np.arange(rows, dtype=np.float32) / rows   # 0 (top) → 1 (bottom)

    # Interpolate NEW_RGB → OLD_RGB based on gen_frac
    r_alive = (NEW_RGB[0] * (1 - gen_frac) + OLD_RGB[0] * gen_frac).astype(np.uint8)
    g_alive = (NEW_RGB[1] * (1 - gen_frac) + OLD_RGB[1] * gen_frac).astype(np.uint8)
    b_alive = (NEW_RGB[2] * (1 - gen_frac) + OLD_RGB[2] * gen_frac).astype(np.uint8)

    # Expand to (rows, cols)
    R = np.where(grid == 1, np.tile(r_alive[:, np.newaxis], (1, cols)), BG_RGB[0])
    G = np.where(grid == 1, np.tile(g_alive[:, np.newaxis], (1, cols)), BG_RGB[1])
    B = np.where(grid == 1, np.tile(b_alive[:, np.newaxis], (1, cols)), BG_RGB[2])

    alpha = np.full((rows, cols), 255, dtype=np.uint8)
    small = np.stack([alpha, R.astype(np.uint8),
                      G.astype(np.uint8), B.astype(np.uint8)], axis=-1)
    return np.repeat(np.repeat(small, CELL, axis=0), CELL, axis=1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    rule_lut = build_rule_lut(RULE)
    grid = evolve(rule_lut)
    pixels_arr = build_pixels(grid)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)
    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

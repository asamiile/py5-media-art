from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

CELL = 2
COLS = SIZE[0] // CELL   # 960
ROWS = SIZE[1] // CELL   # 540
RULE = 90   # Rule 90 — Sierpinski triangle fractal

pixels_arr = None


def build_rule_lut(rule_num):
    return np.array([(rule_num >> i) & 1 for i in range(8)], dtype=np.uint8)


def evolve(rule_lut):
    grid = np.zeros((ROWS, COLS), dtype=np.uint8)
    # Single "on" cell at center of first row → pure Sierpinski triangle
    grid[0, COLS // 2] = 1

    for gen in range(1, ROWS):
        row = grid[gen - 1]
        left   = np.roll(row, 1)
        right  = np.roll(row, -1)
        triple = (left << 2) | (row << 1) | right
        grid[gen] = rule_lut[triple]

    return grid


def build_pixels(grid):
    rows, cols = grid.shape

    # Hue varies by generation (top=warm amber, bottom=cool violet)
    gen_idx = np.arange(rows, dtype=np.float32) / rows
    hue_row = (gen_idx * 240 + 30).astype(np.float32)  # 30° (amber) → 270° (violet)
    H = np.tile(hue_row[:, np.newaxis], (1, cols))

    S, V = 0.88, 0.95
    h = H / 60.0
    i6 = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = V * (1 - S)
    q = V * (1 - S * f)
    t = V * (1 - S * (1 - f))

    idx = [i6 == k for k in range(6)]
    Vf = np.full_like(H, V)
    r = np.select(idx, [Vf, q, p, p, t, Vf])
    g = np.select(idx, [t, Vf, Vf, q, p, p])
    b = np.select(idx, [p, p, t, Vf, Vf, q])

    alive = grid == 1
    r_out = np.where(alive, (r * 255).astype(np.uint8), np.uint8(6))
    g_out = np.where(alive, (g * 255).astype(np.uint8), np.uint8(4))
    b_out = np.where(alive, (b * 255).astype(np.uint8), np.uint8(12))

    alpha = np.full((rows, cols), 255, dtype=np.uint8)
    small = np.stack([alpha, r_out, g_out, b_out], axis=-1)
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

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

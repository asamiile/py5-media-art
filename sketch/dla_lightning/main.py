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

# Theme: "Branching discharge" — fractal lightning via midpoint displacement
# Recursive subdivision: each segment splits at a midpoint displaced perpendicular
# Branches spawn at split points with decreasing probability at depth

MAX_DEPTH  = 11      # recursion depth — controls detail level
ROUGHNESS  = 0.58    # perpendicular displacement decay per level (< 1 = smoother)
BRANCH_P   = 0.40    # probability of spawning a side branch at each split

# Palette: near-black sky, bright cyan core → dim blue tips → glow halo
BG_COL    = np.array([2,   3,   8], dtype=np.uint8)
HOT_COL   = np.array([210, 240, 255], dtype=np.float32)   # near-white core
MID_COL   = np.array([60,  160, 240], dtype=np.float32)   # mid branches
COOL_COL  = np.array([18,   60, 120], dtype=np.float32)   # deep tips

segments = []   # list of (x1, y1, x2, y2, depth)


def subdivide(x1, y1, x2, y2, depth, disp, rng):
    if depth == 0:
        segments.append((x1, y1, x2, y2, depth))
        return

    # Midpoint with perpendicular displacement
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx * dx + dy * dy)
    if length < 0.5:
        segments.append((x1, y1, x2, y2, depth))
        return

    # Perpendicular direction (normalized)
    px = -dy / length
    py =  dx / length

    # Displacement proportional to segment length × roughness factor
    offset = rng.uniform(-disp, disp) * length
    mx += px * offset
    my += py * offset

    new_disp = disp * ROUGHNESS

    subdivide(x1, y1, mx, my, depth - 1, new_disp, rng)
    subdivide(mx, my, x2, y2, depth - 1, new_disp, rng)

    # Possible side branch at this midpoint
    if depth >= 3 and rng.random() < BRANCH_P * (depth / MAX_DEPTH):
        # Branch deflects at 20–55° from main direction
        main_angle = np.arctan2(y2 - y1, x2 - x1)
        side_sign = rng.choice([-1, 1])
        branch_angle = main_angle + side_sign * rng.uniform(0.35, 0.95)
        branch_len = length * rng.uniform(0.35, 0.55)
        bx = mx + np.cos(branch_angle) * branch_len
        by = my + np.sin(branch_angle) * branch_len
        subdivide(mx, my, bx, by, depth - 3, new_disp * 0.7, rng)


def build_pixels(width, height):
    # Render segments onto a pixel buffer with depth-coded glow
    # Use a float accumulation canvas; then tone-map to ARGB
    canvas_r = np.zeros((height, width), dtype=np.float32)
    canvas_g = np.zeros((height, width), dtype=np.float32)
    canvas_b = np.zeros((height, width), dtype=np.float32)

    if not segments:
        alpha = np.full((height, width), 255, dtype=np.uint8)
        bg = np.stack([alpha,
                       np.full((height, width), BG_COL[0], dtype=np.uint8),
                       np.full((height, width), BG_COL[1], dtype=np.uint8),
                       np.full((height, width), BG_COL[2], dtype=np.uint8)], axis=-1)
        return bg

    max_d = max(s[4] for s in segments) or 1
    for x1, y1, x2, y2, depth in segments:
        t = depth / max_d   # 0 = tip (cool), 1 = trunk (hot)  — inverted below
        tip_frac = 1 - (depth / MAX_DEPTH)   # 0 = trunk/seed, 1 = fine tips

        col_r = HOT_COL[0] * (1 - tip_frac) + COOL_COL[0] * tip_frac
        col_g = HOT_COL[1] * (1 - tip_frac) + COOL_COL[1] * tip_frac
        col_b = HOT_COL[2] * (1 - tip_frac) + COOL_COL[2] * tip_frac

        # Rasterize line via Bresenham-style numpy approach
        x1i, y1i = int(round(x1)), int(round(y1))
        x2i, y2i = int(round(x2)), int(round(y2))
        steps = max(abs(x2i - x1i), abs(y2i - y1i), 1)
        lx = np.round(np.linspace(x1i, x2i, steps + 1)).astype(int)
        ly = np.round(np.linspace(y1i, y2i, steps + 1)).astype(int)
        mask = (lx >= 0) & (lx < width) & (ly >= 0) & (ly < height)
        lx, ly = lx[mask], ly[mask]
        if len(lx) == 0:
            continue

        # Glow: thicker segments get glow radius scaled by their depth
        glow_r = max(1, int(3 * (1 - tip_frac)))
        weight = 1.0 + 4.0 * (1 - tip_frac)

        for gy in range(-glow_r, glow_r + 1):
            for gx in range(-glow_r, glow_r + 1):
                dist2 = gx * gx + gy * gy
                if dist2 > glow_r * glow_r:
                    continue
                gfall = np.exp(-dist2 / max(glow_r, 1))
                glx = np.clip(lx + gx, 0, width - 1)
                gly = np.clip(ly + gy, 0, height - 1)
                np.add.at(canvas_r, (gly, glx), col_r * weight * gfall / 255.0)
                np.add.at(canvas_g, (gly, glx), col_g * weight * gfall / 255.0)
                np.add.at(canvas_b, (gly, glx), col_b * weight * gfall / 255.0)

    # Tone map: log1p + normalize
    max_v = max(canvas_r.max(), canvas_g.max(), canvas_b.max())
    if max_v > 0:
        scale = np.log1p(np.array([canvas_r, canvas_g, canvas_b]) * 12.0)
        scale /= scale.max()
        r_px = np.clip(scale[0] * 255, 0, 255).astype(np.uint8)
        g_px = np.clip(scale[1] * 255, 0, 255).astype(np.uint8)
        b_px = np.clip(scale[2] * 255, 0, 255).astype(np.uint8)
    else:
        r_px = g_px = b_px = np.zeros((height, width), dtype=np.uint8)

    alpha = np.full((height, width), 255, dtype=np.uint8)
    return np.stack([alpha, r_px, g_px, b_px], axis=-1)


pixels_arr = None


def setup():
    global pixels_arr
    py5.size(*SIZE)
    rng = np.random.default_rng()

    W, H = SIZE[0], SIZE[1]
    # Lightning strikes downward from a point high on the canvas
    start_x = W * rng.uniform(0.38, 0.62)
    start_y = H * 0.04
    end_x   = W * rng.uniform(0.35, 0.65)
    end_y   = H * 0.88

    subdivide(start_x, start_y, end_x, end_y, MAX_DEPTH, 0.28, rng)
    pixels_arr = build_pixels(W, H)


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

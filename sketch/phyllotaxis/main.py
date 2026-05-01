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

# Theme: "Nature's arithmetic" — golden angle phyllotaxis pattern
# The golden angle φ = 360° × (1 − 1/φ²) ≈ 137.508° encodes the Fibonacci sequence
GOLDEN_ANGLE = 137.508   # degrees — nature's packing optimum

N_SEEDS  = 8500    # total seeds
C_SCALE  = 10.2    # r = C_SCALE × √n (controls spacing)

# The pattern fills a circle; radius of outermost seed determines canvas fit
MAX_R = min(SIZE[0], SIZE[1]) * 0.47   # fit within canvas with margin

# Palette — 3 concentric color zones (center = oldest growth)
# Inner zone (first seeds): deep amber
# Middle: golden yellow
# Outer rim (newest seeds): pale warm cream
INNER_COL = np.array([180,  95,  25], dtype=np.float32)   # #b45f19 amber
MID_COL   = np.array([225, 175,  60], dtype=np.float32)   # #e1af3c golden
OUTER_COL = np.array([240, 225, 185], dtype=np.float32)   # #f0e1b9 pale cream
BG_COL    = (8, 6, 3)


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)
    py5.no_stroke()

    CX, CY = SIZE[0] / 2, SIZE[1] / 2

    # Compute seed positions via Vogel's formula
    ns = np.arange(1, N_SEEDS + 1, dtype=np.float32)
    angles_rad = np.radians(ns * GOLDEN_ANGLE)
    r_norm = np.sqrt(ns / N_SEEDS)          # normalized radius 0→1
    r_px = r_norm * MAX_R                   # pixel radius

    xs = CX + r_px * np.cos(angles_rad)
    ys = CY + r_px * np.sin(angles_rad)

    # Seed size: larger at center (older, more established), smaller at edge
    seed_r = 7.5 * (1 - r_norm * 0.72)     # 7.5 → 2.1 px from center to edge

    # Color by normalized radius: inner→mid→outer
    t0 = np.clip(r_norm * 2.0, 0, 1)           # inner → mid
    t1 = np.clip(r_norm * 2.0 - 1.0, 0, 1)    # mid → outer

    r_col = INNER_COL[0] * (1 - t0) + MID_COL[0] * t0 * (1 - t1) + OUTER_COL[0] * t1
    g_col = INNER_COL[1] * (1 - t0) + MID_COL[1] * t0 * (1 - t1) + OUTER_COL[1] * t1
    b_col = INNER_COL[2] * (1 - t0) + MID_COL[2] * t0 * (1 - t1) + OUTER_COL[2] * t1

    # Alpha: fully opaque at center, slightly transparent at outer edge
    alpha = (200 + 55 * (1 - r_norm)).astype(int)

    # Draw seeds from outermost (back) to innermost (front) so center overlaps edge
    order = np.argsort(r_norm)[::-1]

    for i in order:
        x, y = xs[i], ys[i]
        sr = seed_r[i]
        if sr < 0.5:
            continue
        py5.fill(int(r_col[i]), int(g_col[i]), int(b_col[i]), int(alpha[i]))
        py5.ellipse(x, y, sr * 2, sr * 2)

    # Faint outer ring to frame the sunflower head
    py5.no_fill()
    py5.stroke(80, 65, 40, 60)
    py5.stroke_weight(1.5)
    py5.ellipse(CX, CY, MAX_R * 2.04, MAX_R * 2.04)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

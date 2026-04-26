from pathlib import Path
import math
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Singular crystal" — a single hexagonal snow crystal grown by recursive
# branching; each run draws a unique crystal because branch angles and decay
# rates are randomized, but perfect 6-fold symmetry is enforced by applying the
# same parameters to all 6 arms.

MAX_DEPTH    = 7        # recursion depth (7 gives fine dendritic tips)
ARM_LENGTH   = 175.0    # initial arm length in pixels (fits within H/2)
MIN_LEN      = 2.0      # stop branching below this length

# Color palette
BG_COL   = (  8,  12,  24)    # midnight blue-black
TRUNK_COL = ( 60, 100, 200)   # deep ice blue (center, thick trunk)
TIP_COL   = (220, 235, 255)   # near-white (fine outer tips)


def arm_color(depth_remaining):
    """Interpolate from trunk (large depth) to tip (depth=0)."""
    t = 1.0 - depth_remaining / MAX_DEPTH   # 0=trunk, 1=tip
    r = int(TRUNK_COL[0] * (1 - t) + TIP_COL[0] * t)
    g = int(TRUNK_COL[1] * (1 - t) + TIP_COL[1] * t)
    b = int(TRUNK_COL[2] * (1 - t) + TIP_COL[2] * t)
    return r, g, b


def draw_branch(x1, y1, angle, length, depth, branch_params):
    """Recursively draw one branch of the snowflake arm."""
    if depth <= 0 or length < MIN_LEN:
        return

    x2 = x1 + length * math.cos(angle)
    y2 = y1 + length * math.sin(angle)

    r, g, b = arm_color(depth)
    py5.stroke(r, g, b, 230)
    sw = max(0.6, depth * 0.55)
    py5.stroke_weight(sw)
    py5.line(x1, y1, x2, y2)

    len_decay, branch_angle, branch_len_frac = branch_params[MAX_DEPTH - depth]

    # Continue main trunk
    draw_branch(x2, y2, angle, length * len_decay, depth - 1, branch_params)

    # Symmetric side branches (bilateral symmetry within the arm)
    side_len = length * branch_len_frac
    draw_branch(x2, y2, angle + branch_angle, side_len, depth - 2, branch_params)
    draw_branch(x2, y2, angle - branch_angle, side_len, depth - 2, branch_params)


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    CX, CY = SIZE[0] / 2, SIZE[1] / 2

    rng = np.random.default_rng()

    # Randomized per-depth parameters (same for all 6 arms — ensures 6-fold symmetry)
    len_decays    = rng.uniform(0.55, 0.70, MAX_DEPTH)    # main trunk decay
    branch_angles = rng.uniform(55, 72, MAX_DEPTH) * math.pi / 180
    branch_fracs  = rng.uniform(0.50, 0.68, MAX_DEPTH)    # side branch length as fraction

    branch_params = list(zip(len_decays, branch_angles, branch_fracs))

    # Draw 6 arms at 60° intervals (6-fold symmetry)
    py5.no_fill()
    for k in range(6):
        arm_angle = k * math.pi / 3.0
        draw_branch(CX, CY, arm_angle, ARM_LENGTH, MAX_DEPTH, branch_params)

    # Faint star-like background dots for winter atmosphere
    rng2 = np.random.default_rng()
    n_stars = 200
    sx = rng2.integers(0, SIZE[0], n_stars)
    sy = rng2.integers(0, SIZE[1], n_stars)
    br = rng2.integers(40, 140, n_stars)
    py5.no_stroke()
    for i in range(n_stars):
        py5.fill(br[i], br[i] + 10, br[i] + 30, 180)
        py5.ellipse(float(sx[i]), float(sy[i]), 1.5, 1.5)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

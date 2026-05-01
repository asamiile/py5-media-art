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

# Theme: "Fading resonance" — a harmonograph: dual pendulum mechanical plotter whose
# exponentially decaying oscillations trace an inward-spiraling Lissajous curve.
# The trace glows gold at the start (wide swings) and dims to near-black as it
# settles at center — the entire life of a mechanical drawing on a single canvas.

# Harmonograph parameters:
#   x(t) = A1*sin(f1*t + p1)*exp(-d1*t) + A2*sin(f2*t + p2)*exp(-d2*t)
#   y(t) = A3*sin(f3*t + p3)*exp(-d3*t) + A4*sin(f4*t + p4)*exp(-d4*t)

N_POINTS = 500_000
T_MAX    = 200.0      # total time; pendulums have mostly died by this point

# Canvas center and scale
W, H   = SIZE
CX, CY = W / 2, H / 2
SCALE  = min(W, H) * 0.46

# Palette
BG_COL    = np.array([  5,   4,   9], dtype=np.uint8)
COL_BRIGHT = np.array([225, 175,  55], dtype=np.float32)   # early trace — warm gold
COL_DIM    = np.array([ 58,  40,  12], dtype=np.float32)   # late trace — dark amber
COL_DEAD   = np.array([  8,   6,  14], dtype=np.float32)   # dead center — near BG

# Stroke alpha range (dense accumulation, drawn point by point)
ALPHA_MAX = 240
ALPHA_MIN =   6


def make_params(rng):
    """Draw harmonograph parameters: near-rational frequency ratios with slight drift."""
    # X pendulum: two components near ratio 2:3
    f1 = 2.0 + rng.uniform(-0.003, 0.003)
    f2 = 3.0 + rng.uniform(-0.003, 0.003)
    # Y pendulum: near 2:3 as well, with independent drift
    f3 = 2.0 + rng.uniform(-0.003, 0.003)
    f4 = 3.0 + rng.uniform(-0.003, 0.003)

    p1 = rng.uniform(0, 2 * np.pi)
    p2 = rng.uniform(0, 2 * np.pi)
    p3 = rng.uniform(0, 2 * np.pi)
    p4 = rng.uniform(0, 2 * np.pi)

    # Decay rates (slow: d ≈ 0.003–0.008)
    d1 = rng.uniform(0.003, 0.007)
    d2 = rng.uniform(0.003, 0.007)
    d3 = rng.uniform(0.003, 0.007)
    d4 = rng.uniform(0.003, 0.007)

    # Amplitudes (sum to 1 for each axis)
    a1 = rng.uniform(0.4, 0.7)
    a2 = 1.0 - a1
    a3 = rng.uniform(0.4, 0.7)
    a4 = 1.0 - a3

    return (f1, f2, f3, f4, p1, p2, p3, p4, d1, d2, d3, d4, a1, a2, a3, a4)


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    rng = np.random.default_rng()
    f1, f2, f3, f4, p1, p2, p3, p4, d1, d2, d3, d4, a1, a2, a3, a4 = make_params(rng)

    t = np.linspace(0, T_MAX, N_POINTS, dtype=np.float64)

    x = (a1 * np.sin(f1 * t + p1) * np.exp(-d1 * t)
         + a2 * np.sin(f2 * t + p2) * np.exp(-d2 * t))
    y = (a3 * np.sin(f3 * t + p3) * np.exp(-d3 * t)
         + a4 * np.sin(f4 * t + p4) * np.exp(-d4 * t))

    # Max amplitude at t=0 for normalization
    x_amp0 = a1 + a2   # max when both sines = 1
    y_amp0 = a3 + a4

    px = (CX + x * SCALE / x_amp0).astype(np.float32)
    py_coord = (CY + y * SCALE / y_amp0).astype(np.float32)

    # Age parameter [0, 1]: 0 = start (bright gold), 1 = end (dead)
    age = (t / T_MAX).astype(np.float32)

    # Color per point: bright → dim → dead
    t2 = np.clip(age * 2.0, 0.0, 1.0)
    t3 = np.clip(age * 2.0 - 1.0, 0.0, 1.0)
    r_vals = (COL_BRIGHT[0] * (1 - t2) + COL_DIM[0] * t2
              + (COL_DEAD[0] - COL_DIM[0]) * t3).astype(np.uint8)
    g_vals = (COL_BRIGHT[1] * (1 - t2) + COL_DIM[1] * t2
              + (COL_DEAD[1] - COL_DIM[1]) * t3).astype(np.uint8)
    b_vals = (COL_BRIGHT[2] * (1 - t2) + COL_DIM[2] * t2
              + (COL_DEAD[2] - COL_DIM[2]) * t3).astype(np.uint8)
    alpha_vals = (ALPHA_MAX * (1 - age) + ALPHA_MIN * age).astype(np.uint8)

    # Draw using py5 stroke points
    py5.stroke_weight(1.4)
    py5.no_fill()

    step = 4   # draw every Nth point for speed (still 125k points)
    for i in range(0, N_POINTS, step):
        xi, yi = float(px[i]), float(py_coord[i])
        if 0 <= xi < W and 0 <= yi < H:
            py5.stroke(int(r_vals[i]), int(g_vals[i]), int(b_vals[i]), int(alpha_vals[i]))
            py5.point(xi, yi)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

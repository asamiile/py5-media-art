from pathlib import Path
import sys
import math
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

MAX_DEPTH = 11
BASE_ANGLE = 22.0       # base spread; wide for naturalism
LENGTH_RATIO = 0.68
TRUNK_LENGTH = SIZE[1] * 0.28

# Wind lean: left branches slightly shorter and more horizontal
WIND_BIAS = 8.0   # degrees — bends right branch slightly up, left down

segments = []


def branch(x, y, angle_deg, length, depth):
    if depth == 0 or length < 1.5:
        return

    nx = x + math.cos(math.radians(angle_deg)) * length
    ny = y + math.sin(math.radians(angle_deg)) * length
    segments.append((x, y, nx, ny, depth))

    # Upper levels: always 2 children; lower (finer) levels: 1 or 2 randomly
    n = 2 if depth > MAX_DEPTH // 2 else int(np.random.choice([1, 2], p=[0.25, 0.75]))

    # Angle jitter ±25° for strong stochastic asymmetry
    jitter = np.random.uniform(-25.0, 25.0, n)
    sides = np.linspace(-BASE_ANGLE, BASE_ANGLE, n)

    # Apply wind lean: left child (negative spread) tends more horizontal
    wind = np.linspace(WIND_BIAS, -WIND_BIAS, n)
    child_angles = sides + jitter + wind + angle_deg

    # Left children slightly shorter (wind-compressed)
    len_scale = np.linspace(LENGTH_RATIO - 0.06, LENGTH_RATIO + 0.04, n)
    child_lens = length * len_scale * np.random.uniform(0.92, 1.08, n)

    for ca, cl in zip(child_angles, child_lens):
        branch(nx, ny, ca, cl, depth - 1)


def setup():
    global segments
    py5.size(*SIZE)

    # Sky gradient: pale cold gray-blue (top) → warm white (horizon)
    py5.no_stroke()
    for row in range(SIZE[1]):
        t = row / SIZE[1]
        r = int(214 + (234 - 214) * t)
        g = int(221 + (232 - 221) * t)
        b = int(232 + (224 - 232) * t)
        py5.fill(r, g, b)
        py5.rect(0, row, SIZE[0], 1)

    # Slight atmospheric haze band near horizon
    py5.fill(200, 205, 212, 60)
    py5.rect(0, SIZE[1] * 0.7, SIZE[0], SIZE[1] * 0.3)

    # Root at bottom-center pointing straight up (-90°)
    branch(SIZE[0] / 2, SIZE[1] * 0.97, -90.0, TRUNK_LENGTH, MAX_DEPTH)


def draw():
    py5.no_fill()
    for x1, y1, x2, y2, depth in segments:
        t = 1.0 - depth / MAX_DEPTH   # 0 = trunk, 1 = tips

        # Dark brown trunk → mid brown → lighter brown-gray twigs
        r = int(45 + 62 * t)     # #2d → #6b
        g = int(35 + 52 * t)     # #23 → #58
        b = int(24 + 48 * t)     # #18 → #48

        # Thick trunk tapering aggressively to hairline tips
        sw = max(0.5, 12.0 * (1 - t) ** 2.2)
        alpha = int(220 - 40 * t)

        py5.stroke(r, g, b, alpha)
        py5.stroke_weight(sw)
        py5.line(x1, y1, x2, y2)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

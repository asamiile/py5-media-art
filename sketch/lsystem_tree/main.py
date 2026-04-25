from pathlib import Path
import math
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

MAX_DEPTH = 11
BRANCH_ANGLE = 28.0   # base spread angle in degrees
LENGTH_RATIO = 0.68   # child length as fraction of parent
TRUNK_LENGTH = SIZE[1] * 0.28

segments = []   # (x1, y1, x2, y2, depth, max_depth)


def branch(x, y, angle_deg, length, depth):
    if depth == 0 or length < 1.2:
        return

    nx = x + math.cos(math.radians(angle_deg)) * length
    ny = y + math.sin(math.radians(angle_deg)) * length
    segments.append((x, y, nx, ny, depth))

    # Number of children: 2 for deep trunk, 2–3 nearer the tips
    n = 2 if depth > MAX_DEPTH // 2 else np.random.choice([2, 3], p=[0.6, 0.4])

    # Spread angles: symmetric ± base, plus small jitter
    spreads = np.random.uniform(-BRANCH_ANGLE * 0.35, BRANCH_ANGLE * 0.35, n)
    sides = np.linspace(-BRANCH_ANGLE, BRANCH_ANGLE, n)
    child_angles = sides + spreads + angle_deg

    child_len = length * np.random.uniform(LENGTH_RATIO - 0.05, LENGTH_RATIO + 0.05, n)

    for ca, cl in zip(child_angles, child_len):
        branch(nx, ny, ca, cl, depth - 1)


def setup():
    global segments
    py5.size(*SIZE)

    # Gradient background: deep indigo → warm near-black
    py5.no_stroke()
    for row in range(SIZE[1]):
        t = row / SIZE[1]
        py5.fill(int(8 + 18 * t), int(6 + 10 * t), int(20 + 18 * (1 - t)))
        py5.rect(0, row, SIZE[0], 1)

    # Root at bottom-center pointing upward
    branch(SIZE[0] / 2, SIZE[1] * 0.97, -90.0, TRUNK_LENGTH, MAX_DEPTH)


def draw():
    py5.no_fill()
    n = len(segments)

    for x1, y1, x2, y2, depth in segments:
        t = 1.0 - depth / MAX_DEPTH  # 0 = trunk, 1 = tips

        # Stroke weight: thick trunk → hairline tips
        sw = max(0.4, 6.0 * (1 - t) ** 2.8)

        # Color: dark sienna → warm ochre → sage-gold tips
        r = int(70 + 150 * t)
        g = int(38 + 155 * t)
        b = int(12 + 72 * t)

        py5.stroke(r, g, b, int(180 + 75 * t))
        py5.stroke_weight(sw)
        py5.line(x1, y1, x2, y2)

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

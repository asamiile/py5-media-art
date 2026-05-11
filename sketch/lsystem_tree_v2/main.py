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
BASE_ANGLE = 26.0       # Wider spread for natural canopy
LENGTH_RATIO = 0.72
TRUNK_LENGTH = SIZE[1] * 0.32

segments = []
leaves = []


def branch(x, y, angle_deg, length, depth):
    if depth == 0 or length < 1.0:
        # Add leaves at tips
        leaves.append((x, y, np.random.uniform(3, 8)))
        return

    # Natural Fidelity: Split long segments (especially trunk) into smaller curved pieces
    steps = 1 if depth < 8 else 3
    curr_x, curr_y = x, y
    step_len = length / steps
    
    # Cumulative angle jitter for a "bent" look
    curr_angle = angle_deg
    for _ in range(steps):
        # Slight bend in segments
        curr_angle += np.random.uniform(-4.0, 4.0)
        nx = curr_x + math.cos(math.radians(curr_angle)) * step_len
        ny = curr_y + math.sin(math.radians(curr_angle)) * step_len
        segments.append((curr_x, curr_y, nx, ny, depth))
        curr_x, curr_y = nx, ny

    # Asymmetric branching
    n = 2 if depth > 4 else int(np.random.choice([1, 2], p=[0.3, 0.7]))
    
    # Angles with more stochastic variance
    sides = np.linspace(-BASE_ANGLE, BASE_ANGLE, n)
    jitter = np.random.uniform(-15.0, 15.0, n)
    child_angles = curr_angle + sides + jitter
    
    # Randomize length per child
    child_lens = length * LENGTH_RATIO * np.random.uniform(0.85, 1.15, n)

    for ca, cl in zip(child_angles, child_lens):
        branch(curr_x, curr_y, ca, cl, depth - 1)


def setup():
    global segments, leaves
    py5.size(*SIZE)

    # Sky: Beautiful Night Sky (Obsidian to Deep Indigo)
    py5.no_stroke()
    for row in range(SIZE[1]):
        t = row / SIZE[1]
        # #050508 (top) -> #0f0a20 (bottom)
        r = int(5 + (15 - 5) * t)
        g = int(5 + (10 - 5) * t)
        b = int(8 + (32 - 8) * t)
        py5.fill(r, g, b)
        py5.rect(0, row, SIZE[0], 1)

    # Stars
    py5.fill(255, 255, 255, 180)
    for _ in range(400):
        py5.ellipse(np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), 1.2, 1.2)

    # Root
    branch(SIZE[0] / 2, SIZE[1] * 0.95, -90.0, TRUNK_LENGTH, MAX_DEPTH)


def draw():
    py5.no_fill()
    
    # 1. Render Branches
    for x1, y1, x2, y2, depth in segments:
        t = 1.0 - depth / MAX_DEPTH
        
        # Deep Charcoal to Aged Wood
        r = int(15 + 40 * t)
        g = int(10 + 30 * t)
        b = int(8 + 20 * t)

        # Tapering
        sw = max(0.4, 18.0 * (1 - t) ** 2.5)
        py5.stroke(r, g, b, 240)
        py5.stroke_weight(sw)
        py5.line(x1, y1, x2, y2)

    # 2. Render Bioluminescent Leaves (Teal)
    py5.blend_mode(py5.ADD)
    for x, y, size in leaves:
        # Core
        py5.no_stroke()
        py5.fill(0, 230, 200, 100) # Luminous Teal
        py5.ellipse(x, y, size, size)
        
        # Glow
        py5.fill(0, 230, 200, 20)
        py5.ellipse(x, y, size*2.5, size*2.5)
        
    # 3. Add small "firefly" accents (Gold)
    for _ in range(12):
        fx = np.random.uniform(SIZE[0]*0.2, SIZE[0]*0.8)
        fy = np.random.uniform(SIZE[1]*0.3, SIZE[1]*0.9)
        py5.fill(255, 200, 0, 150)
        py5.ellipse(fx, fy, 2, 2)
        py5.fill(255, 200, 0, 30)
        py5.ellipse(fx, fy, 6, 6)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="lsystem_tree_v2_p1.png")


py5.run_sketch()

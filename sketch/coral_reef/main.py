from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Color palette
DEEP_NAVY = (10, 15, 35)
CORAL_PINK = (255, 127, 127)
SEAFOAM_TEAL = (64, 224, 208)
GOLDEN_AMBER = (255, 193, 7)
SOFT_LAVENDER = (200, 180, 220)
BRIGHT_TURQUOISE = (0, 206, 209)
OCEAN_BLUE = (30, 60, 100)

# Coral types with different growth patterns
CORAL_TYPES = [
    {
        'name': 'branching',
        'branch_angle': 25,
        'branch_decay': 0.7,
        'depth': 6,
        'color': CORAL_PINK,
        'thickness': 3
    },
    {
        'name': 'plate',
        'branch_angle': 45,
        'branch_decay': 0.85,
        'depth': 4,
        'color': SEAFOAM_TEAL,
        'thickness': 5
    },
    {
        'name': 'staghorn',
        'branch_angle': 20,
        'branch_decay': 0.65,
        'depth': 7,
        'color': GOLDEN_AMBER,
        'thickness': 2
    },
    {
        'name': 'brain',
        'branch_angle': 60,
        'branch_decay': 0.9,
        'depth': 3,
        'color': SOFT_LAVENDER,
        'thickness': 6
    },
    {
        'name': 'fan',
        'branch_angle': 70,
        'branch_decay': 0.8,
        'depth': 5,
        'color': BRIGHT_TURQUOISE,
        'thickness': 4
    }
]

np.random.seed(None)


def draw_coral_branch(x, y, angle, length, depth, coral_type, max_depth):
    """Recursively draw coral branches with organic variation."""
    if depth <= 0 or length < 2:
        return

    # Calculate end point
    end_x = x + length * np.cos(angle)
    end_y = y + length * np.sin(angle)

    # Draw branch with thickness tapering
    thickness = max(1, coral_type['thickness'] * (depth / max_depth))
    py5.stroke_weight(thickness)

    # Color variation based on depth
    base_color = coral_type['color']
    depth_factor = 1 - (depth / max_depth)
    r = int(base_color[0] * (1 - depth_factor * 0.3))
    g = int(base_color[1] * (1 - depth_factor * 0.2))
    b = int(base_color[2] * (1 - depth_factor * 0.1))
    py5.stroke(r, g, b, 200)

    py5.line(x, y, end_x, end_y)

    # Branch with organic variation
    num_branches = np.random.randint(2, 4)
    for i in range(num_branches):
        # Random angle variation
        angle_variation = np.random.uniform(-coral_type['branch_angle'], coral_type['branch_angle'])
        new_angle = angle + angle_variation

        # Length decay with variation
        length_decay = coral_type['branch_decay'] * np.random.uniform(0.9, 1.1)
        new_length = length * length_decay

        draw_coral_branch(end_x, end_y, new_angle, new_length, depth - 1, coral_type, max_depth)


def draw_coral_colony(start_x, start_y, coral_type):
    """Draw a complete coral colony with multiple branches."""
    num_branches = np.random.randint(3, 6)
    for i in range(num_branches):
        angle = np.random.uniform(-np.pi/2, np.pi/2)
        length = np.random.uniform(40, 80)
        draw_coral_branch(start_x, start_y, angle, length, coral_type['depth'], coral_type, coral_type['depth'])


def draw_sea_floor():
    """Draw organic sea floor with depth gradient."""
    for y in range(int(SIZE[1] * 0.7), int(SIZE[1])):
        depth = (y - SIZE[1] * 0.7) / (SIZE[1] * 0.3)
        r = int(DEEP_NAVY[0] * (1 - depth * 0.5))
        g = int(DEEP_NAVY[1] * (1 - depth * 0.5))
        b = int(DEEP_NAVY[2] * (1 - depth * 0.3))
        py5.stroke(r, g, b)
        py5.line(0, y, SIZE[0], y)


def draw_light_rays():
    """Draw underwater light rays with fading."""
    num_rays = np.random.randint(5, 8)
    for i in range(num_rays):
        x = np.random.uniform(0, SIZE[0])
        width = np.random.uniform(20, 50)
        alpha = np.random.uniform(10, 30)

        py5.no_stroke()
        py5.fill(255, 255, 255, alpha)
        py5.begin_shape()
        py5.vertex(x, 0)
        py5.vertex(x + width, 0)
        py5.vertex(x + width * 1.5, SIZE[1] * 0.6)
        py5.vertex(x + width * 0.5, SIZE[1] * 0.6)
        py5.end_shape(py5.CLOSE)


def draw_bubbles():
    """Draw rising bubbles with varying sizes."""
    num_bubbles = np.random.randint(20, 30)
    for i in range(num_bubbles):
        x = np.random.uniform(0, SIZE[0])
        y = np.random.uniform(SIZE[1] * 0.3, SIZE[1])
        size = np.random.uniform(2, 8)
        alpha = np.random.uniform(50, 150)

        py5.no_stroke()
        py5.fill(200, 220, 255, alpha)
        py5.circle(x, y, size)


def setup():
    py5.size(*SIZE)
    py5.background(*DEEP_NAVY)


def draw():
    # Draw sea floor
    draw_sea_floor()

    # Draw light rays
    draw_light_rays()

    # Draw coral colonies
    num_colonies = np.random.randint(8, 12)
    for i in range(num_colonies):
        x = np.random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        y = np.random.uniform(SIZE[1] * 0.6, SIZE[1] * 0.9)
        coral_type = np.random.choice(CORAL_TYPES)
        draw_coral_colony(x, y, coral_type)

    # Draw bubbles
    draw_bubbles()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR)


if __name__ == '__main__':
    py5.run_sketch()

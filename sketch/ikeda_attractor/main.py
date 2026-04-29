from pathlib import Path
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

MAX_ITERATIONS = 50000  # Reduced for performance
U = 0.9  # Ikeda parameter - controls chaos

def setup():
    py5.size(*SIZE)
    py5.background(10, 14, 39)  # Deep midnight blue
    py5.no_stroke()

    # Start from a random point
    x, y = np.random.uniform(-1, 1), np.random.uniform(-1, 1)

    # Pre-allocate arrays for performance
    points_x = np.zeros(MAX_ITERATIONS)
    points_y = np.zeros(MAX_ITERATIONS)

    # Generate Ikeda attractor points
    for i in range(MAX_ITERATIONS):
        t = 0.4 - 6 / (1 + x**2 + y**2)
        x_new = 1 + U * (x * np.cos(t) - y * np.sin(t))
        y_new = U * (x * np.sin(t) + y * np.cos(t))

        points_x[i] = x_new
        points_y[i] = y_new

        x, y = x_new, y_new

    # Normalize points to screen coordinates
    x_min, x_max = points_x.min(), points_x.max()
    y_min, y_max = points_y.min(), points_y.max()

    # Scale to fit screen with padding
    padding = 100
    scale_x = (SIZE[0] - 2 * padding) / (x_max - x_min)
    scale_y = (SIZE[1] - 2 * padding) / (y_max - y_min)
    scale = min(scale_x, scale_y)

    screen_x = ((points_x - x_min) * scale + padding).astype(int)
    screen_y = ((points_y - y_min) * scale + padding).astype(int)

    # Draw points with color based on iteration
    for i in range(MAX_ITERATIONS):
        # Color based on iteration for gradient effect
        progress = i / MAX_ITERATIONS

        # Electric cyan to warm magenta gradient
        if progress < 0.5:
            # Cyan to magenta
            t = progress * 2
            r = int(255 * t)
            g = int(212 * (1 - t))
            b = 255
        else:
            # Magenta to white
            t = (progress - 0.5) * 2
            r = 255
            g = int(212 * t)
            b = 255

        # Add some variation based on position
        variation = np.sin(i * 0.01) * 30
        r = int(np.clip(r + variation, 0, 255))
        g = int(np.clip(g + variation, 0, 255))
        b = int(np.clip(b + variation, 0, 255))

        # Draw points
        alpha = int(50 + 100 * progress)  # Fade in
        py5.fill(r, g, b, alpha)
        py5.point(screen_x[i], screen_y[i])

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")

py5.run_sketch()

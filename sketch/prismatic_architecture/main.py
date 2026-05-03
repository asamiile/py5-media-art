from pathlib import Path
import sys
import numpy as np
import py5

# Standard imports for the repo
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    py5.background(10, 10, 10)  # Obsidian
    py5.blend_mode(py5.SCREEN)
    py5.no_loop()


def draw_crystal_face(points, thickness):
    # Simulate thin-film interference
    # Thickness drives the phase shift for R, G, B
    r = 127 + 127 * np.sin(thickness * 0.05 + 0)
    g = 127 + 127 * np.sin(thickness * 0.05 + py5.TWO_PI / 3)
    b = 127 + 127 * np.sin(thickness * 0.05 + 2 * py5.TWO_PI / 3)
    
    # Add a bit of gold/teal bias
    r = r * 0.8 + 50 # Gold bias
    g = g * 0.9 + 50 # Teal bias
    b = b * 1.0 + 30
    
    py5.fill(r, g, b, 180)
    py5.stroke(255, 255, 255, 100)
    py5.stroke_weight(1.0)
    
    py5.begin_shape()
    for p in points:
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)


def draw_isometric_cube(x, y, s, thickness):
    # Isometric projection of a cube
    h = s * np.sqrt(3) / 2
    
    # Points
    p1 = (x, y - s)
    p2 = (x + h, y - s/2)
    p3 = (x + h, y + s/2)
    p4 = (x, y + s)
    p5 = (x - h, y + s/2)
    p6 = (x - h, y - s/2)
    p_mid = (x, y)
    
    # Top face
    draw_crystal_face([p1, p2, p_mid, p6], thickness)
    # Right face
    draw_crystal_face([p2, p3, p4, p_mid], thickness + 50)
    # Left face
    draw_crystal_face([p6, p_mid, p4, p5], thickness + 100)


def subdivide(x, y, s, depth, max_depth):
    if depth >= max_depth or (depth > 1 and np.random.random() < 0.3):
        thickness = (x + y) * 0.1 + np.random.uniform(0, 1000)
        draw_isometric_cube(x, y, s, thickness)
        return

    # Subdivide into 4 quadrants (effectively)
    new_s = s * 0.55
    offset = s * 0.5
    
    # Jitter offsets for "crystal growth" look
    subdivide(x, y - offset, new_s, depth + 1, max_depth)
    subdivide(x + offset * 0.86, y + offset * 0.5, new_s, depth + 1, max_depth)
    subdivide(x - offset * 0.86, y + offset * 0.5, new_s, depth + 1, max_depth)
    
    # Optional center crystal
    if np.random.random() < 0.5:
        subdivide(x, y, new_s * 0.8, depth + 1, max_depth)


def draw():
    w, h = SIZE
    
    # Multiple "buildings" or clusters
    num_clusters = 12
    for _ in range(num_clusters):
        cx = np.random.uniform(w * 0.1, w * 0.9)
        cy = np.random.uniform(h * 0.2, h * 0.8)
        base_size = np.random.uniform(100, 300)
        subdivide(cx, cy, base_size, 0, 4)

    # Final pass - no filter needed for now
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()

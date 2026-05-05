from pathlib import Path
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    py5.background(2, 4, 12) # Deep obsidian void

def draw_city(x, y, w, h, depth):
    # Recursive Quadtree City
    if depth > 0 and (py5.random(1) < 0.75 or depth > 3):
        # Subdivide
        hw, hh = w / 2, h / 2
        draw_city(x, y, hw, hh, depth - 1)
        draw_city(x + hw, y, hw, hh, depth - 1)
        draw_city(x, y + hh, hw, hh, depth - 1)
        draw_city(x + hw, y + hh, hw, hh, depth - 1)
    else:
        # Draw a "glass" building
        height = py5.random(20, 200) * (5 - depth)
        
        py5.push_matrix()
        py5.translate(x + w/2, y + h/2, height/2)
        
        # Spectral refraction fringes (additive lines)
        # We draw multiple slightly offset boxes with different spectral colors
        py5.stroke_weight(1.0)
        
        # Core structure
        py5.fill(10, 20, 40, 100) # Dark transparent glass
        py5.stroke(255, 255, 255, 150) # White edges
        py5.box(w * 0.9, h * 0.9, height)
        
        # Spectral fringes (simulating refraction)
        py5.no_fill()
        py5.stroke(0, 255, 255, 120) # Cyan fringe
        py5.box(w * 0.92, h * 0.92, height + 2)
        py5.stroke(255, 0, 255, 120) # Magenta fringe
        py5.box(w * 0.88, h * 0.88, height - 2)
        
        py5.pop_matrix()

def draw():
    py5.background(2, 4, 12)
    
    # Dense Starfield
    py5.stroke_weight(1)
    np.random.seed(42) # Keep stars consistent for the still
    for _ in range(3000):
        sx, sy = np.random.rand(2)
        py5.stroke(200, 220, 255, 150)
        py5.point(sx * py5.width, sy * py5.height, -500) # Stars in background

    # Setup Camera for Isometric-like view
    py5.translate(py5.width/2, py5.height/2 + 200, -200)
    py5.rotate_x(-np.pi / 6)
    py5.rotate_z(np.pi / 4)
    
    # Center the city
    py5.translate(-500, -500, 0)
    
    # Draw city
    py5.random_seed(1234)
    draw_city(0, 0, 1000, 1000, 5)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

py5.run_sketch()

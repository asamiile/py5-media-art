from pathlib import Path
import sys
import numpy as np
import py5

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

# Singularity masses
NUM_SINGULARITIES = 4
singularities = []
masses = []

def setup():
    py5.size(*SIZE)
    py5.background(5, 5, 12)  # Deep midnight navy
    
    global singularities, masses
    print("Initializing singularities...")
    for _ in range(NUM_SINGULARITIES):
        singularities.append(np.array([
            py5.random(py5.width * 0.15, py5.width * 0.85),
            py5.random(py5.height * 0.15, py5.height * 0.85)
        ]))
        # Larger masses for more dramatic warp
        masses.append(py5.random(8000, 25000))
        
    print("Drawing starfield...")
    draw_starfield()
    
    print("Drawing warped grid pass 1 (Silver)...")
    draw_warped_grid(color=(180, 180, 220), offset=0)
    
    # Additive pass for glow
    py5.blend_mode(py5.ADD)
    print("Drawing warped grid pass 2 (Sapphire glow)...")
    draw_warped_grid(color=(0, 60, 180), offset=1.5) # Darker/Subtler Blue
    
    print("Drawing Einstein rings...")
    draw_einstein_rings()
    
    print("Rendering complete.")
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def draw_starfield():
    """Render a dense background starfield."""
    py5.push_style()
    for _ in range(4000):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        mag = np.random.power(6) * 255
        py5.stroke(mag, mag, mag * 1.1, mag * 0.8)
        py5.stroke_weight(py5.random(0.4, 1.3))
        py5.point(x, y)
    py5.pop_style()

def warp_point(x, y, offset_val=0):
    """Apply gravitational lensing distortion with optional offset for aberration."""
    p = np.array([x, y], dtype=np.float32)
    disp = np.zeros(2, dtype=np.float32)
    
    for i in range(NUM_SINGULARITIES):
        s = singularities[i]
        m = masses[i]
        diff = p - s
        dist_sq = np.sum(diff**2) + 1500
        # Displacement with slight offset per color channel for aberration
        factor = m / dist_sq
        disp -= factor * diff * (1.0 + offset_val * 0.02)
        
    return p + disp

def draw_warped_grid(color, offset=0):
    """Render the distorted geometric grid."""
    py5.push_style()
    py5.stroke(*color, 120)
    py5.no_fill()
    
    COLS = 90
    ROWS = 60
    
    # Horizontal
    for r in range(ROWS + 1):
        y = r * (py5.height / ROWS)
        py5.begin_shape()
        for c in range(COLS + 1):
            x = c * (py5.width / COLS)
            wp = warp_point(x, y, offset)
            py5.vertex(wp[0], wp[1])
        py5.end_shape()

    # Vertical
    for c in range(COLS + 1):
        x = c * (py5.width / COLS)
        py5.begin_shape()
        for r in range(ROWS + 1):
            y = r * (py5.height / ROWS)
            wp = warp_point(x, y, offset)
            py5.vertex(wp[0], wp[1])
        py5.end_shape()
    py5.pop_style()

def draw_einstein_rings():
    """Render distorted rings of light around singularities."""
    py5.push_style()
    py5.blend_mode(py5.ADD)
    py5.no_fill() # CRITICAL FIX
    
    for i in range(NUM_SINGULARITIES):
        s = singularities[i]
        m = masses[i]
        
        # Central glow
        for r_inner in range(15, 0, -3):
            py5.stroke(0, 150, 255, 60) # Reduced alpha
            py5.stroke_weight(r_inner)
            py5.point(s[0], s[1])
            
        # Golden core
        py5.stroke(255, 215, 0, 100) # Reduced alpha
        py5.stroke_weight(2)
        py5.point(s[0], s[1])

        # Distorted luminous rings
        num_rings = 6
        for j in range(1, num_rings + 1):
            radius = np.sqrt(m) * j * 0.45
            py5.begin_shape()
            alpha = py5.remap(j, 1, num_rings, 80, 20) # Reduced alpha
            py5.stroke(0, 127, 255, alpha)
            py5.stroke_weight(py5.remap(j, 1, num_rings, 2.0, 0.6))
            
            for angle in np.linspace(0, py5.TWO_PI, 150):
                rx = s[0] + py5.cos(angle) * radius
                ry = s[1] + py5.sin(angle) * radius
                wp = warp_point(rx, ry)
                py5.vertex(wp[0], wp[1])
            py5.end_shape(py5.CLOSE)
            
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

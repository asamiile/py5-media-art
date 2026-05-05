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

# Constants
NUM_STARS = 15000

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(2, 3, 8) # Very dark navy
    
    # Generate background stars
    # Some bright, some dim
    stars = np.random.rand(NUM_STARS, 3).astype(np.float32)
    stars[:, 0] *= py5.width
    stars[:, 1] *= py5.height
    stars[:, 2] = np.random.power(5, NUM_STARS) * 255 # Brightness
    
    # Pre-render a subtle cosmic nebula glow
    py5.no_stroke()
    for i in range(150):
        r = py5.remap(i, 0, 150, 600, 0)
        alpha = py5.remap(i, 0, 150, 1, 15)
        # Deep spectral gradient: Indigo -> Violet -> Magenta
        if i < 50:
            py5.fill(10, 20, 50, alpha)
        elif i < 100:
            py5.fill(30, 10, 60, alpha)
        else:
            py5.fill(50, 10, 40, alpha)
        py5.circle(py5.width/2, py5.height/2, r)

    # Lensing / Refraction logic
    # We use additive blending for the RGB split
    py5.blend_mode(py5.ADD)
    
    # RGB offsets for chromatic aberration
    offsets = [
        {"off": 0.00, "col": (200, 0, 0)}, # Red
        {"off": 0.02, "col": (0, 200, 0)}, # Green
        {"off": 0.04, "col": (0, 0, 200)}  # Blue
    ]
    
    center_x, center_y = py5.width / 2, py5.height / 2
    
    for layer in offsets:
        py5.stroke(*layer["col"], 150)
        noise_off = layer["off"]
        
        for i in range(NUM_STARS):
            sx, sy, b = stars[i]
            
            dx = sx - center_x
            dy = sy - center_y
            dist = np.sqrt(dx*dx + dy*dy)
            
            if dist < 500:
                # Lens profile: convex magnification
                # mag increases toward center
                mag_factor = (500 - dist) / 500
                mag = 1.0 + mag_factor * 0.4
                
                tx = dx * mag
                ty = dy * mag
                
                # Distortion: Simplex noise field simulating crystal imperfections
                # Different scale and offset for each color channel creates the prism effect
                nx = py5.os_noise(sx * 0.003 + noise_off, sy * 0.003)
                ny = py5.os_noise(sx * 0.003, sy * 0.003 + noise_off)
                
                tx += (nx - 0.5) * 120 * mag_factor
                ty += (ny - 0.5) * 120 * mag_factor
                
                render_x = center_x + tx
                render_y = center_y + ty
                
                # Brightness boost inside the lens
                py5.stroke(*layer["col"], b * 0.6 * (1 + mag_factor))
            else:
                render_x, render_y = sx, sy
                py5.stroke(*layer["col"], b * 0.4)
            
            py5.point(render_x, render_y)

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

py5.run_sketch()

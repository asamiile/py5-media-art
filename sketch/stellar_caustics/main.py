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

# Algorithm Parameters
NUM_WAVES = 18
SCALE = 22.0
TURBULENCE = 0.5

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(10, 10, 32) # Midnight Indigo
    py5.no_loop()
    
    # Render layers
    field = compute_caustic_field()
    render_caustics(field)
    draw_starfield()
    add_chromatic_glow(field)
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def compute_caustic_field():
    """Vectorized caustic field computation with noise-driven distortion."""
    w, h = py5.width, py5.height
    x = np.linspace(0, SCALE, w)
    y = np.linspace(0, SCALE * (h/w), h)
    X, Y = np.meshgrid(x, y)
    
    # Add turbulence using a sum of low-frequency sine waves (simulating noise)
    dist_x = np.sin(X * 0.5) * np.cos(Y * 0.8) * TURBULENCE
    dist_y = np.cos(X * 0.7) * np.sin(Y * 0.6) * TURBULENCE
    X += dist_x
    Y += dist_y
    
    field = np.zeros_like(X)
    for i in range(NUM_WAVES):
        angle = py5.TWO_PI * i / NUM_WAVES
        # Each wave is a rotated plane wave with a random phase
        phase = i * 1.333
        wave = X * np.cos(angle) + Y * np.sin(angle)
        field += np.cos(wave * 1.5 + phase)
    
    # Normalize and push contrast
    f_min, f_max = np.min(field), np.max(field)
    field = (field - f_min) / (f_max - f_min)
    field = field ** 3.0 # Extra sharp caustic peaks
    
    return field

def render_caustics(field):
    """Map field to Teal/Amber/Indigo palette."""
    # Colors
    indigo = np.array([10, 10, 32], dtype=np.float32)
    teal = np.array([0, 206, 209], dtype=np.float32)
    amber = np.array([255, 191, 0], dtype=np.float32)
    
    h, w = field.shape
    pixels = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Segmented interpolation
    m1 = field < 0.5
    m2 = field >= 0.5
    
    # Indigo to Teal
    t1 = (field[m1] / 0.5)[:, None]
    pixels[m1] = ((1 - t1) * indigo + t1 * teal).astype(np.uint8)
    
    # Teal to Amber
    t2 = ((field[m2] - 0.5) / 0.5)[:, None]
    pixels[m2] = ((1 - t2) * teal + t2 * amber).astype(np.uint8)
    
    py5.set_np_pixels(pixels, bands='RGB')

def draw_starfield():
    """Background starfield with varying magnitudes."""
    py5.push_style()
    py5.blend_mode(py5.SCREEN)
    for _ in range(3000):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        mag = np.random.power(8) * 255
        py5.stroke(mag, mag, mag * 1.2, mag * 0.8)
        py5.stroke_weight(py5.random(0.5, 1.5))
        py5.point(x, y)
    py5.pop_style()

def add_chromatic_glow(field):
    """Add luminous highlights at the caustic peaks."""
    py5.push_style()
    py5.blend_mode(py5.ADD)
    
    # Sample field for glow points
    step = 6
    h, w = field.shape
    for y in range(0, h, step):
        for x in range(0, w, step):
            v = field[y, x]
            if v > 0.92:
                # Solar white flare
                alpha = py5.remap(v, 0.92, 1.0, 20, 150)
                size = py5.remap(v, 0.92, 1.0, 1, 5)
                py5.no_stroke()
                py5.fill(240, 248, 255, alpha)
                py5.circle(x, y, size)
                
                # Soft teal halo
                py5.fill(0, 206, 209, alpha * 0.4)
                py5.circle(x, y, size * 3)
                
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

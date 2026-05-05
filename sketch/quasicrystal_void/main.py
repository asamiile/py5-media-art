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
SYMMETRY = 7
FREQUENCY = 12.0
PHASE = 1.618

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(5, 5, 16) # Deep Obsidian
    py5.no_loop() # Static for preview
    
    # Render logic
    field = compute_quasicrystal_field()
    render_field(field)
    draw_starfield() # Draw stars on top of the field
    add_focal_glows(field)
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def draw_starfield():
    """Dense background starfield."""
    py5.push_style()
    for _ in range(4000):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        mag = np.random.power(6) * 255
        py5.stroke(mag, mag, mag * 1.1, mag * 0.7)
        py5.stroke_weight(py5.random(0.4, 1.2))
        py5.point(x, y)
    py5.pop_style()

def compute_quasicrystal_field():
    """Vectorized quasicrystal field computation using NumPy."""
    w, h = py5.width, py5.height
    x = np.linspace(-3.5, 3.5, w)
    y = np.linspace(-3.5 * (h/w), 3.5 * (h/w), h)
    X, Y = np.meshgrid(x, y)
    
    field = np.zeros_like(X)
    for i in range(SYMMETRY):
        angle = py5.TWO_PI * i / SYMMETRY
        wave = X * np.cos(angle) + Y * np.sin(angle)
        # Add slight phase shift per symmetry axis for complexity
        field += np.cos(FREQUENCY * wave + PHASE * (1 + i * 0.1))
    
    # Normalize to [-1, 1] based on actual min/max for visibility
    f_min, f_max = np.min(field), np.max(field)
    field = 2 * (field - f_min) / (f_max - f_min) - 1
    
    # Push contrast (aggressive power to keep most values low)
    field = np.sign(field) * (np.abs(field) ** 1.5)
    
    return field

def render_field(field):
    """Map the field to a complex iridescent palette."""
    # Define colors
    void = np.array([5, 5, 16], dtype=np.float32)
    amethyst = np.array([80, 20, 150], dtype=np.float32) # Darker
    cyan = np.array([0, 150, 255], dtype=np.float32)
    gold = np.array([255, 200, 50], dtype=np.float32)
    
    # Map [-1, 1] to [0, 1]
    t = (field + 1) / 2
    h, w = field.shape
    
    # Create 3-channel RGB array
    pixels = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 3-segment interpolation: Void -> Amethyst/Cyan -> Gold
    m1 = t < 0.6  # 60% of field is dark/void
    m2 = (t >= 0.6) & (t < 0.85)
    m3 = t >= 0.85
    
    # Seg 1: Void -> Amethyst
    t1 = (t[m1] / 0.6)[:, None]
    pixels[m1] = ((1 - t1) * void + t1 * amethyst).astype(np.uint8)
    
    # Seg 2: Amethyst -> Cyan
    t2 = ((t[m2] - 0.6) / 0.25)[:, None]
    pixels[m2] = ((1 - t2) * amethyst + t2 * cyan).astype(np.uint8)
    
    # Seg 3: Cyan -> Gold
    t3 = ((t[m3] - 0.85) / 0.15)[:, None]
    pixels[m3] = ((1 - t3) * cyan + t3 * gold).astype(np.uint8)
    
    # Add to screen
    py5.set_np_pixels(pixels, bands='RGB')

def add_focal_glows(field):
    """Add luminous points at the peaks of the interference pattern."""
    py5.push_style()
    py5.blend_mode(py5.ADD)
    
    # Sample the field to find peaks
    sample_step = 8
    w, h = py5.width, py5.height
    
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            v = field[y, x]
            if v > 0.85:
                # Gold focal point
                alpha = py5.remap(v, 0.85, 1.0, 50, 180)
                size = py5.remap(v, 0.85, 1.0, 2, 6)
                py5.no_stroke()
                py5.fill(255, 215, 0, alpha)
                py5.circle(x, y, size)
                
                # Soft outer glow
                py5.fill(0, 255, 255, alpha * 0.3)
                py5.circle(x, y, size * 2.5)
                
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

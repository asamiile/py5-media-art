from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes
from lib.paths import sketch_dir

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Algorithm Parameters
SOURCES = [
    (-0.60,  0.35), ( 0.60,  0.35),
    ( 0.00, -0.45), (-0.38, -0.10), ( 0.42,  0.05),
]
WAVELENGTH = 0.12
PHASE_SHIFT = 0.0

def setup():
    # Use P2D for high-resolution pixel manipulation
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.no_loop()
    
    # Compute field at full resolution
    field = compute_interference_field()
    render_field(field)
    draw_ui_overlay()
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def compute_interference_field():
    """Vectorized interference field computation."""
    w, h = py5.width, py5.height
    x = np.linspace(-1.0, 1.0, w, dtype=np.float32)
    y = np.linspace(-1.0 * (h/w), 1.0 * (h/w), h, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    
    field = np.zeros_like(X)
    for sx, sy in SOURCES:
        r = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)
        # Summing sine waves for interference
        field += np.sin(2 * np.pi * r / WAVELENGTH + PHASE_SHIFT)
    
    # Normalize to [-1, 1]
    f_min, f_max = np.min(field), np.max(field)
    return 2 * (field - f_min) / (f_max - f_min) - 1

def render_field(field):
    """Render field with high contrast and optical detail."""
    # Define "Sapphire & Mercury" palette
    void = np.array([5, 8, 20], dtype=np.float32)      # Deep blue-black
    sapphire = np.array([20, 80, 200], dtype=np.float32) # Electric sapphire
    mercury = np.array([220, 230, 255], dtype=np.float32) # Cold mercury
    
    # Map [-1, 1] to [0, 1]
    t = (field + 1) / 2
    
    # Apply a sharpening power to reduce "blurriness"
    t = np.sign(t - 0.5) * (np.abs(t - 0.5) ** 0.8) + 0.5
    t = np.clip(t, 0, 1)
    
    h, w = field.shape
    pixels = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Split into two segments: Void -> Sapphire -> Mercury
    m1 = t < 0.5
    m2 = t >= 0.5
    
    # Segment 1: Void to Sapphire
    t1 = (t[m1] / 0.5)[:, None]
    pixels[m1] = ((1 - t1) * void + t1 * sapphire).astype(np.uint8)
    
    # Segment 2: Sapphire to Mercury
    t2 = ((t[m2] - 0.5) / 0.5)[:, None]
    pixels[m2] = ((1 - t2) * sapphire + t2 * mercury).astype(np.uint8)
    
    # Apply pixels
    py5.set_np_pixels(pixels, bands='RGB')

def draw_ui_overlay():
    """Add technical 'precision instrument' overlays."""
    py5.push_style()
    
    # Subtle grid
    py5.stroke(255, 255, 255, 15)
    py5.stroke_weight(1)
    for x in range(0, py5.width, 100):
        py5.line(x, 0, x, py5.height)
    for y in range(0, py5.height, 100):
        py5.line(0, y, py5.width, y)
        
    # Source markers
    py5.no_fill()
    py5.stroke(255, 255, 255, 80)
    for sx, sy in SOURCES:
        px = py5.remap(sx, -1, 1, 0, py5.width)
        py5.circle(px, py5.height/2 + (sy * py5.width/2), 10)
        py5.line(px-15, py5.height/2 + (sy * py5.width/2), px+15, py5.height/2 + (sy * py5.width/2))
        py5.line(px, py5.height/2 + (sy * py5.width/2) - 15, px, py5.height/2 + (sy * py5.width/2) + 15)
        
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

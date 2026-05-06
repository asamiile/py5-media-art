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
NUM_PARTICLES = 120000
DT = 0.01
ITERATIONS = 500

# Lorenz Attractor Parameters
SIGMA = 10.0
RHO = 28.0
BETA = 8.0/3.0

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(1, 1, 3) # Obsidian Void
    py5.no_loop()
    
    # Initialize particles in a broad region to cover the attractor space
    pos = np.random.rand(NUM_PARTICLES, 3)
    pos[:, 0] = (pos[:, 0] - 0.5) * 40
    pos[:, 1] = (pos[:, 1] - 0.5) * 60
    pos[:, 2] = pos[:, 2] * 50
    
    # Run simulation
    all_pos = []
    for _ in range(ITERATIONS):
        pos = update_lorenz(pos)
        # Only record every 2nd step to save memory but keep density
        if _ % 2 == 0:
            all_pos.append(pos.copy())
    
    # Flatten and render
    all_pos = np.concatenate(all_pos, axis=0)
    render_attractor(all_pos)
    draw_starfield()
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def update_lorenz(pos):
    """Vectorized Lorenz Attractor update."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    
    pos[:, 0] += dx * DT
    pos[:, 1] += dy * DT
    pos[:, 2] += dz * DT
    return pos

def render_attractor(points):
    """Project 3D points to 2D and render using high-performance histogram accumulation."""
    # Rotation for better perspective
    angle_x = py5.radians(15)
    angle_z = py5.radians(10)
    
    # Rot X
    y_rot = points[:, 1] * np.cos(angle_x) - points[:, 2] * np.sin(angle_x)
    z_rot = points[:, 1] * np.sin(angle_x) + points[:, 2] * np.cos(angle_x)
    points[:, 1], points[:, 2] = y_rot, z_rot
    
    # Rot Z
    x_rot = points[:, 0] * np.cos(angle_z) - points[:, 1] * np.sin(angle_z)
    y_rot = points[:, 0] * np.sin(angle_z) + points[:, 1] * np.cos(angle_z)
    points[:, 0], points[:, 1] = x_rot, y_rot
    
    # Projection
    scale = 18.0
    px = py5.width / 2 + points[:, 0] * scale
    py = py5.height / 2 - (points[:, 2] - 25) * scale # Offset Z to center
    
    # Filter points out of bounds
    mask = (px >= 0) & (px < py5.width) & (py >= 0) & (py < py5.height)
    px, py = px[mask], py[mask]
    r = np.sqrt(points[mask, 0]**2 + points[mask, 1]**2 + points[mask, 2]**2)
    
    # Create 2D histogram for density accumulation
    h, w = py5.height, py5.width
    density, _, _ = np.histogram2d(py, px, bins=[h, w], range=[[0, h], [0, w]])
    
    # Power scale for density (gamma correction) for better depth
    density = np.power(density, 0.3)
    d_max = np.max(density)
    if d_max > 0: density /= d_max
    
    r_sum, _, _ = np.histogram2d(py, px, bins=[h, w], range=[[0, h], [0, w]], weights=r)
    p_count, _, _ = np.histogram2d(py, px, bins=[h, w], range=[[0, h], [0, w]])
    avg_r = np.divide(r_sum, p_count, out=np.zeros_like(r_sum), where=p_count!=0)
    
    # Normalize radius for color mapping
    r_min, r_max = np.min(avg_r[p_count>0]), np.max(avg_r[p_count>0])
    avg_r = (avg_r - r_min) / (r_max - r_min + 1e-6)
    
    # Final RGB buffer
    pixels = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Define colors
    violet = np.array([120, 20, 255], dtype=np.float32)
    crimson = np.array([255, 10, 80], dtype=np.float32)
    white = np.array([255, 230, 250], dtype=np.float32)
    
    # Interpolate colors based on radius
    m1 = (avg_r < 0.6) & (p_count > 0)
    m2 = (avg_r >= 0.6) & (p_count > 0)
    
    # Seg 1: Violet -> Crimson
    t1 = (avg_r[m1] / 0.6)[:, None]
    c1 = (1 - t1) * violet + t1 * crimson
    pixels[m1] = (c1 * density[m1][:, None]).astype(np.uint8)
    
    # Seg 2: Crimson -> White
    t2 = ((avg_r[m2] - 0.6) / 0.4)[:, None]
    c2 = (1 - t2) * crimson + t2 * white
    pixels[m2] = (c2 * density[m2][:, None]).astype(np.uint8)
    
    py5.set_np_pixels(pixels, bands='RGB')

def draw_starfield():
    """Background starfield."""
    py5.push_style()
    for _ in range(2500):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        mag = np.random.power(12) * 255
        py5.stroke(mag, mag, mag * 1.1, mag * 0.6)
        py5.stroke_weight(py5.random(0.4, 1.2))
        py5.point(x, y)
    py5.pop_style()

def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

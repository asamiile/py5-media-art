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
PREVIEW_FRAME = 240
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 90_000
DT = 0.5
DIFFUSION = 0.3
POTENTIAL_STRENGTH = 150.0
NOISE_SCALE = 0.003

# State
particles = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
particle_colors = np.zeros((NUM_PARTICLES, 3), dtype=np.uint8)

# Noise Grid for optimization
GRID_SIZE = 512
noise_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
grad_x = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
grad_y = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.background(2, 2, 8)  # Deep midnight navy
    
    # Initialize particles randomly
    global particles, particle_colors, noise_grid, grad_x, grad_y
    particles[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    particles[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    
    # Palette: Cyan, Amethyst, Rose Gold, White-Gold
    palette = np.array([
        [0, 255, 255],    # Electric Cyan
        [153, 102, 204],  # Royal Amethyst
        [183, 110, 121],  # Rose Gold
        [255, 250, 230],  # White-Gold
    ], dtype=np.uint8)
    
    # Assign random colors from palette to particles
    color_indices = np.random.randint(0, len(palette), NUM_PARTICLES)
    particle_colors = palette[color_indices]
    
    # Pre-compute noise grid and gradients
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            n1 = py5.os_noise(x * 0.015, y * 0.015)
            n2 = 0.5 * py5.os_noise(x * 0.03, y * 0.03)
            noise_grid[y, x] = n1 + n2
            
    # Compute gradients
    grad_y, grad_x = np.gradient(noise_grid)
    
    # Draw initial starfield
    draw_starfield()

def draw_starfield():
    """Render a dense, varied starfield in the background."""
    py5.push_style()
    for _ in range(4000):
        x = np.random.uniform(0, py5.width)
        y = np.random.uniform(0, py5.height)
        mag = np.random.power(5) * 255
        py5.stroke(mag, mag, mag * 0.95, mag * 0.7)
        py5.stroke_weight(np.random.uniform(0.5, 1.2))
        py5.point(x, y)
    py5.pop_style()

def draw():
    global particles
    
    # Decay background to prevent saturation
    # We use a very low alpha decay to allow longer trails
    py5.blend_mode(py5.BLEND)
    py5.fill(2, 2, 8, 6) # Slower decay
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Redraw starfield occasionally
    if py5.frame_count % 60 == 0:
        draw_starfield()
    
    # Langevin dynamics update (Vectorized!)
    gx = (particles[:, 0] * (GRID_SIZE / py5.width)).astype(np.int32) % GRID_SIZE
    gy = (particles[:, 1] * (GRID_SIZE / py5.height)).astype(np.int32) % GRID_SIZE
    
    p_gx = grad_x[gy, gx]
    p_gy = grad_y[gy, gx]
    
    # Update positions
    particles[:, 0] -= p_gx * POTENTIAL_STRENGTH * DT
    particles[:, 1] -= p_gy * POTENTIAL_STRENGTH * DT
    
    # Stochastic kick
    particles += np.random.normal(0, DIFFUSION, (NUM_PARTICLES, 2))
    
    # Wrap boundaries
    particles[:, 0] %= py5.width
    particles[:, 1] %= py5.height
    
    # Rendering
    py5.blend_mode(py5.ADD)
    
    palette = [
        [0, 255, 255],    # Electric Cyan
        [153, 102, 204],  # Royal Amethyst
        [183, 110, 121],  # Rose Gold
        [255, 250, 230],  # White-Gold
    ]
    
    for c in palette:
        mask = (particle_colors == c).all(axis=1)
        pts = particles[mask]
        py5.stroke(c[0], c[1], c[2], 28) # Higher alpha for visibility
        py5.stroke_weight(1)
        py5.points(pts)
    
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

if __name__ == "__main__":
    py5.run_sketch()

from pathlib import Path
import sys
import math
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 120  # Allow some accumulation
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Artwork Constants ---
LAYER_COUNT = 32
STEPS = 512
STAR_COUNT = 1500
PERSISTENCE = 0.92  # Persistence of trails

# --- State ---
stars = None
manifold_params = None

def setup():
    global stars, manifold_params
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    
    # Initialize stars
    stars = np.random.rand(STAR_COUNT, 3)  # x, y, size
    stars[:, 0] *= py5.width
    stars[:, 1] *= py5.height
    stars[:, 2] *= 1.5
    
    # Manifold presets (m, n1, n2, n3)
    manifold_params = {
        "m": py5.random(3, 12),
        "n1": py5.random(0.1, 1.5),
        "n2": py5.random(1.0, 5.0),
        "n3": py5.random(1.0, 5.0)
    }

def draw():
    # --- Background Persistence ---
    # Draw a semi-transparent black rectangle to create trails
    py5.no_stroke()
    py5.fill(0, 0, 0, (1.0 - PERSISTENCE) * 100)
    py5.rect(0, 0, py5.width, py5.height)
    
    # --- Starfield ---
    # Only draw stars fully on the first frame or lightly over time
    if py5.frame_count == 1:
        draw_starfield(100)
    else:
        draw_starfield(15) # Subtle twinkle

    # --- Manifold Rendering ---
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    py5.rotate(py5.frame_count * 0.005)
    
    t = py5.frame_count * 0.02
    draw_manifold(t)
    
    py5.pop_matrix()
    
    # --- Exit/Preview ---
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)

def draw_starfield(alpha):
    for i in range(STAR_COUNT):
        x, y, s = stars[i]
        # Twinkle based on noise
        twinkle = py5.os_noise(x * 0.01, y * 0.01, py5.frame_count * 0.05)
        bright = 60 + twinkle * 40
        py5.stroke(40, 5, bright, alpha * (0.5 + twinkle * 0.5))
        py5.stroke_weight(s)
        py5.point(x, y)

def draw_manifold(t):
    base_m = manifold_params["m"]
    base_n1 = manifold_params["n1"]
    base_n2 = manifold_params["n2"]
    base_n3 = manifold_params["n3"]
    
    max_radius = min(py5.width, py5.height) * 0.45
    
    for i in range(LAYER_COUNT):
        progress = i / LAYER_COUNT
        phase = t + i * 0.15
        
        # Animate params
        m = base_m + math.sin(phase * 0.5) * 0.5
        n1 = base_n1 + math.cos(phase * 0.3) * 0.05
        n2 = base_n2 + math.sin(phase * 0.7) * 0.2
        n3 = base_n3 + math.cos(phase * 1.1) * 0.2
        
        scale = max_radius * (0.1 + 0.9 * progress)
        hue = (220 + progress * 80 + math.sin(t * 0.5) * 20) % 360
        
        # Color and Style
        # Outer layers are thinner and more cyan/indigo, inner layers warmer
        py5.no_fill()
        py5.stroke(hue, 70, 90, 40)
        py5.stroke_weight(0.5 + progress * 1.5)
        
        points = get_superformula_points(m, n1, n2, n3, scale, phase)
        
        py5.begin_shape()
        for px, py in points:
            # Domain warping
            nx = py5.os_noise(px * 0.005, py * 0.005, t * 0.5) * 40 - 20
            ny = py5.os_noise(px * 0.005 + 100, py * 0.005 + 100, t * 0.5) * 40 - 20
            py5.vertex(px + nx, py + ny)
        py5.end_shape(py5.CLOSE)

def get_superformula_points(m, n1, n2, n3, scale, phase):
    points = []
    for i in range(STEPS):
        theta = py5.TWO_PI * i / STEPS
        r = superformula_radius(theta, m, n1, n2, n3)
        
        # Jitter radius
        r *= (1.0 + py5.os_noise(theta * 2, phase) * 0.05)
        
        x = math.cos(theta) * r * scale
        y = math.sin(theta) * r * scale
        points.append((x, y))
    return points

def superformula_radius(theta, m, n1, n2, n3):
    a = 1.0
    b = 1.0
    t1 = abs(math.cos(m * theta / 4.0) / a) ** n2
    t2 = abs(math.sin(m * theta / 4.0) / b) ** n3
    r = (t1 + t2) ** (-1.0 / n1)
    return min(r, 10.0)

py5.run_sketch()

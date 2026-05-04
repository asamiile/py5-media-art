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

# Colors
BG_COLOR = "#0A0A0A"
SEAFOAM = "#71B1A1"
AMETHYST = "#6B4F82"
GOLD = "#D4AF37"

def setup():
    py5.size(*SIZE)
    py5.background(0)
    py5.no_loop()
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(10, 10, 5) # Deep charcoal
    
    # Draw boundary
    py5.no_fill()
    py5.stroke(AMETHYST)
    py5.stroke_weight(1)
    # Disk radius in pixels
    R = min(py5.width, py5.height) * 0.45
    py5.ellipse(py5.width/2, py5.height/2, R*2, R*2)
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    
    # Initial branches from center
    num_starts = 8
    for i in range(num_starts):
        angle = i * py5.TWO_PI / num_starts
        branch(complex(0, 0), angle, 0.2, 0)
        
    py5.pop_matrix()
    
    from lib.preview import exit_after_preview_py5
    exit_after_preview_py5(SKETCH_DIR, filename=PREVIEW_FILENAME)

def branch(z, angle, step_rho, depth):
    if depth > 10:
        return
    
    # Mobius transformation to move from origin to a point 'a' in direction 'angle'
    # a = tanh(step_rho/2) * exp(i*angle)
    a = np.tanh(step_rho / 2) * np.exp(1j * angle)
    
    # We want to find the point in the disk that corresponds to moving 'step_rho' 
    # from the current point 'z' in its local 'angle' direction.
    # The transformation that moves the origin to z is T(w) = (w + z) / (1 + conj(z)*w)
    # So the new point is T(a).
    z_next = (a + z) / (1 + np.conj(z) * a)
    
    # Draw segment (approximate geodesic with a line if segment is small)
    # For better visual, we use more segments if needed, but here segments are small.
    R = min(py5.width, py5.height) * 0.45
    x1, y1 = z.real * R, z.imag * R
    x2, y2 = z_next.real * R, z_next.imag * R
    
    # Color based on depth and distance from center
    dist = np.abs(z_next)
    hue = py5.lerp(165, 270, dist) # Seafoam (165) to Amethyst (270)
    sat = py5.lerp(40, 60, dist)
    bri = py5.lerp(60, 90, dist)
    
    py5.stroke(hue, sat, bri, 80)
    # Taper weight
    weight = max(0.5, 3.0 * (1.0 - dist) * (1.0 - depth/12.0))
    py5.stroke_weight(weight)
    
    py5.line(x1, y1, x2, y2)
    
    # Accent tips
    if depth > 7 and py5.random(1) > 0.7:
        py5.stroke(45, 70, 90, 90) # Gold
        py5.stroke_weight(weight * 1.5)
        py5.point(x2, y2)

    # Recursive branching
    # Number of branches decreases or stays small
    num_b = 2 if depth < 4 else (1 if py5.random(1) > 0.4 else 2)
    
    for _ in range(num_b):
        # Angle in the local frame of the current segment
        # In hyperbolic space, angles are preserved (conformal)
        new_angle = angle + py5.random(-0.5, 0.5)
        new_step = step_rho * py5.random(0.7, 0.9)
        branch(z_next, new_angle, new_step, depth + 1)

py5.run_sketch()

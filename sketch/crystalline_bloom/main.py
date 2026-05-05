from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Colors
COLORS = {
    'bg': (10, 14, 26),
    'silver': np.array([162, 194, 225]),
    'amethyst': np.array([153, 102, 204]),
    'gold': np.array([230, 190, 138]),
}

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_recursive_unit(radius, sides, depth, angle_offset, time_val, petal_idx):
    if depth <= 0:
        return
    
    # Color interpolation
    osc = (np.sin(time_val * 2 + depth * 0.8 + petal_idx * 0.1) + 1) / 2
    c = COLORS['silver'] * (1 - osc) + COLORS['amethyst'] * osc
    
    # Gold accent for inner depths
    if depth == 1:
        c = c * 0.7 + COLORS['gold'] * 0.3

    py5.stroke(*c, 100 + depth * 30)
    py5.stroke_weight(1.0 / depth * 1.5)
    py5.no_fill()
    
    py5.begin_shape()
    for i in range(sides):
        theta = i * py5.TWO_PI / sides + angle_offset
        py5.vertex(np.cos(theta) * radius, np.sin(theta) * radius, depth * 5)
    py5.end_shape(py5.CLOSE)
    
    # Sub-units
    new_radius = radius * 0.55
    new_angle = angle_offset + time_val * 0.5
    for i in range(sides):
        theta = i * py5.TWO_PI / sides + angle_offset
        nx = np.cos(theta) * radius * 0.45
        ny = np.sin(theta) * radius * 0.45
        py5.push_matrix()
        py5.translate(nx, ny, -5)
        draw_recursive_unit(new_radius, sides, depth - 1, -new_angle, time_val, petal_idx)
        py5.pop_matrix()

def draw():
    py5.background(*COLORS['bg'])
    
    # Subtle background glow
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, -100)
    py5.no_stroke()
    for r in range(10):
        py5.fill(153, 102, 204, 5)
        py5.ellipse(0, 0, 800 + r*50, 800 + r*50)
    py5.pop_matrix()

    py5.translate(py5.width / 2, py5.height / 2)
    
    # Fermat Spiral points
    n_petals = 150
    c_scale = 18 # scaling constant
    
    time_val = py5.frame_count * 0.015
    
    # Sort petals by depth/index for better 3D layering if needed
    # Here we just draw them in order
    for i in range(n_petals):
        phi = i * 137.508 * (py5.PI / 180)
        r = c_scale * np.sqrt(i)
        
        # Breathing motion
        r_mod = r * (1 + 0.05 * np.sin(time_val + i * 0.05))
        x = r_mod * np.cos(phi)
        y = r_mod * np.sin(phi)
        
        # Individual petal properties
        sides = 3 + (i % 4)
        depth = 3
        petal_radius = (25 + np.sqrt(i) * 1.5) * (1 + 0.1 * np.sin(time_val * 3 + i * 0.2))
        
        py5.push_matrix()
        py5.translate(x, y, 0)
        # Tilt based on distance from center
        py5.rotate_z(phi + time_val)
        py5.rotate_x(r / 500.0)
        
        draw_recursive_unit(petal_radius, sides, depth, 0, time_val, i)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

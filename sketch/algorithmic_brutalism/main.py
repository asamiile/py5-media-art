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
BG = "#121212"
CONCRETE = "#4A4A4A"
DARK_CONCRETE = "#2A2A2A"
SHADOW = "#1A1A1A"
SAFETY_ORANGE = "#FF5F1F"

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(18, 18, 18)
    
    # Lighting
    py5.ambient_light(50, 50, 50)
    py5.directional_light(150, 150, 150, -1, 1, -1)
    
    # Camera
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2, -500)
    py5.rotate_x(py5.PI/4)
    py5.rotate_z(py5.PI/4 + py5.frame_count * 0.002)
    
    t = py5.frame_count * 0.01
    
    # Grid range
    W, H = 1600, 1600
    subdivide(-W/2, -H/2, W, H, 0, t)
    
    py5.pop_matrix()
    
    # Save frames and export
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

def subdivide(x, y, w, h, depth, t):
    # Noise driven split decision
    # Normalize coords for noise
    nx, ny = (x + 800) / 400.0, (y + 800) / 400.0
    val = py5.noise(nx, ny, t)
    
    # Threshold for splitting depends on depth
    threshold = 0.4 + depth * 0.05
    
    if depth < 5 and val > threshold:
        hw, hh = w / 2, h / 2
        subdivide(x, y, hw, hh, depth + 1, t)
        subdivide(x + hw, y, hw, hh, depth + 1, t)
        subdivide(x, y + hh, hw, hh, depth + 1, t)
        subdivide(x + hw, y + hh, hw, hh, depth + 1, t)
    else:
        draw_monolith(x, y, w, h, val, depth, t)

def draw_monolith(x, y, w, h, val, depth, t):
    # Height of the block
    max_z = 300 * (1.0 - depth/6.0)
    z = val * max_z
    
    # Pulsing orange edges
    orange_pulse = py5.sin(t * 2 + val * 10) * 0.5 + 0.5
    is_orange = val > 0.65 and depth > 3
    
    py5.push_matrix()
    py5.translate(x + w/2, y + h/2, z/2)
    
    # Box dimensions
    # Slightly smaller to see gaps
    bw, bh = w * 0.95, h * 0.95
    
    if is_orange:
        py5.fill(255, 95, 31, 200 * orange_pulse)
        # Extra glow box slightly larger
        py5.box(bw * 1.02, bh * 1.02, z * 1.02)
    
    py5.fill(74, 74, 74)
    py5.box(bw, bh, z)
    
    py5.pop_matrix()

py5.run_sketch()

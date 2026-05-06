from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
STAR_COUNT = 1000
GRID_RES = 80
MEMBRANE_SIZE = 1500

def get_pos(u, v, t):
    # u, v in [0, 1]
    x = (u - 0.5) * MEMBRANE_SIZE
    z = (v - 0.5) * MEMBRANE_SIZE
    
    # multi-layered noise warping
    n1 = py5.noise(u * 2, v * 2, t * 0.5)
    n2 = py5.noise(u * 5 + 10, v * 5 + 10, t * 0.2) * 0.3
    
    y = (n1 + n2) * 300 - 150
    # Add folding
    y += np.sin(u * py5.TWO_PI * 2 + t * py5.TWO_PI) * 50
    y += np.cos(v * py5.TWO_PI * 3 - t * py5.TWO_PI) * 40
    
    return x, y, z

stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-1000, 1000), np.random.uniform(-2000, 2000), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background & Lighting
    py5.background(2, 2, 5)
    py5.ambient_light(50, 50, 100)
    py5.directional_light(200, 200, 255, 0, 1, -1)
    
    # Camera
    angle = py5.frame_count * 0.003
    py5.camera(1200 * np.cos(angle), -600, 1200 * np.sin(angle), 0, 0, 0, 0, 1, 0)
    
    # 2. Draw Stars
    py5.no_stroke()
    for sx, sy, sz, s_alpha in stars:
        py5.push_matrix()
        py5.translate(sx, sy, sz)
        py5.fill(255, s_alpha)
        py5.box(2)
        py5.pop_matrix()

    # 3. Draw Membrane
    py5.push_matrix()
    
    # Double layering for iridescence
    for layer in range(2):
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        for i in range(GRID_RES):
            py5.begin_shape(py5.TRIANGLE_STRIP)
            for j in range(GRID_RES + 1):
                u1, v = i/GRID_RES, j/GRID_RES
                u2 = (i+1)/GRID_RES
                
                p1 = get_pos(u1, v, t + layer * 0.01)
                p2 = get_pos(u2, v, t + layer * 0.01)
                
                hue = py5.remap(p1[1], -250, 250, 180, 280)
                py5.fill(hue, 60, 100, 20)
                py5.stroke(hue, 80, 100, 40)
                py5.stroke_weight(0.5)
                
                py5.vertex(*p1)
                py5.vertex(*p2)
            py5.end_shape()
        py5.color_mode(py5.RGB, 255, 255, 255, 255)
        
    py5.pop_matrix()

    # 4. Capture
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

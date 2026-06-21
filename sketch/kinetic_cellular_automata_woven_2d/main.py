from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Rule 30 or 90
RULE = 30
rows = 600
cols = 400
grid = [[0] * cols for _ in range(rows)]
grid[0][cols // 2] = 1

def generate_ca():
    for r in range(1, rows):
        for c in range(cols):
            left = grid[r - 1][(c - 1) % cols]
            mid = grid[r - 1][c]
            right = grid[r - 1][(c + 1) % cols]
            state = (left << 2) | (mid << 1) | right
            grid[r][c] = (RULE >> state) & 1

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    generate_ca()

def draw():
    py5.background(15)
    
    t = py5.frame_count * 0.05
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(t * 0.2)
    
    radius = 300
    py5.stroke_weight(3)
    
    py5.begin_shape(py5.POINTS)
    for r in range(rows):
        y = (r - rows / 2) * 2
        for c in range(cols):
            if grid[r][c] == 1:
                angle = (c / cols) * py5.TWO_PI
                x = py5.cos(angle) * radius
                z = py5.sin(angle) * radius
                
                hue = (100 + r * 0.5 - t * 20) % 360
                py5.stroke(hue, 80, 90)
                py5.vertex(x, y, z)
    py5.end_shape()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            
        import os
        os._exit(0)

py5.run_sketch()

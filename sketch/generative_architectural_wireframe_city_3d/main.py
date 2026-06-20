from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.noise_seed(42)

def draw():
    py5.background(0)
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -400)
    py5.rotate_x(py5.PI / 2.8)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    grid_size = 50
    cols = 40
    rows = 50
    
    offset_y = py5.frame_count * 3.0
    
    for y in range(rows):
        for x in range(cols):
            x_pos = (x - cols / 2) * grid_size
            y_pos = (y - rows / 2) * grid_size
            
            nx = x * 0.1
            ny = (y * grid_size - offset_y) * 0.005
            h = py5.os_noise(nx, ny) * 500
            
            if h < 100: h = 5 
            
            hue = py5.remap(h, 5, 500, 180, 320)
            py5.stroke(hue, 90, 90, 80)
            
            py5.push_matrix()
            py5.translate(x_pos, y_pos, h / 2)
            py5.box(grid_size * 0.8, grid_size * 0.8, h)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw_menger(size, depth):
    if depth == 0:
        py5.box(size)
    else:
        new_size = size / 3.0
        for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
                for z in [-1, 0, 1]:
                    if abs(x) + abs(y) + abs(z) > 1:
                        py5.push_matrix()
                        py5.translate(x * new_size, y * new_size, z * new_size)
                        draw_menger(new_size, depth - 1)
                        py5.pop_matrix()

def draw():
    py5.no_stroke()
    py5.fill(10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.02
    
    py5.camera(
        py5.width/2 + py5.cos(t) * 800, py5.height/2 - 600, 800 + py5.sin(t) * 400,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    
    hue = (150 + t * 20) % 360
    py5.stroke(hue, 80, 90, 50)
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw fractal at depth 3
    draw_menger(600, 3)

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

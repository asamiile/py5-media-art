from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

import numpy as np

cols = 80
rows = 60
scl = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 20, 15)
    py5.blend_mode(py5.ADD)
    
    # Position camera
    py5.translate(py5.width / 2, py5.height / 2 + 300, -200)
    py5.rotate_x(py5.PI / 3)
    py5.translate(-cols * scl / 2, -rows * scl / 2)
    
    t = py5.frame_count * 0.015
    
    # Calculate noise values for the grid
    py5.stroke_weight(2)
    py5.no_fill()
    
    # We will use lines across rows and cols
    for y in range(rows - 1):
        py5.begin_shape(py5.LINES)
        for x in range(cols):
            # Calculate height using two octaves of Perlin noise
            z1 = py5.noise(x * 0.1, (y - t * 20) * 0.1) * 300
            z1 += py5.noise(x * 0.05, (y - t * 20) * 0.05) * 400
            
            z2 = py5.noise(x * 0.1, (y + 1 - t * 20) * 0.1) * 300
            z2 += py5.noise(x * 0.05, (y + 1 - t * 20) * 0.05) * 400
            
            # Color is mapped to Z height
            hue = (200 + z1 * 0.2) % 360
            bright = py5.remap(z1, 200, 700, 30, 100)
            
            py5.stroke(hue, 90, bright, 80)
            py5.vertex(x * scl, y * scl, z1)
            
            hue2 = (200 + z2 * 0.2) % 360
            bright2 = py5.remap(z2, 200, 700, 30, 100)
            
            py5.stroke(hue2, 90, bright2, 80)
            py5.vertex(x * scl, (y + 1) * scl, z2)
        py5.end_shape()
        
    for x in range(cols - 1):
        py5.begin_shape(py5.LINES)
        for y in range(rows):
            z1 = py5.noise(x * 0.1, (y - t * 20) * 0.1) * 300
            z1 += py5.noise(x * 0.05, (y - t * 20) * 0.05) * 400
            
            z2 = py5.noise((x + 1) * 0.1, (y - t * 20) * 0.1) * 300
            z2 += py5.noise((x + 1) * 0.05, (y - t * 20) * 0.05) * 400
            
            hue = (200 + z1 * 0.2) % 360
            bright = py5.remap(z1, 200, 700, 30, 100)
            py5.stroke(hue, 90, bright, 80)
            py5.vertex(x * scl, y * scl, z1)
            
            hue2 = (200 + z2 * 0.2) % 360
            bright2 = py5.remap(z2, 200, 700, 30, 100)
            py5.stroke(hue2, 90, bright2, 80)
            py5.vertex((x + 1) * scl, y * scl, z2)
        py5.end_shape()

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

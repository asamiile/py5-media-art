from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols, rows = 0, 0
scl = 40
w = 4000
h = 3000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    flying = py5.frame_count * 0.05
    
    # Lighting and camera
    py5.camera(py5.width/2, py5.height/2 - 600, 800, 
               py5.width/2, py5.height/2, 0, 
               0, 1, 0)
    
    py5.directional_light(255, 0, 255, 0, 1, -1) # Hot pink
    py5.directional_light(0, 255, 255, 0, -1, 1) # Cyan
    
    py5.translate(py5.width/2 - w/2, py5.height/2 + 200, -h/2 + 1000)
    py5.rotate_x(py5.PI / 3)
    
    py5.no_fill()
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        
        # Color gradient based on y
        c = py5.remap(y, 0, rows, 0, 255)
        py5.stroke(c, 50, 255 - c, 150)
        py5.stroke_weight(2)
        
        for x in range(cols):
            # Calculate height with noise
            z1 = py5.remap(py5.os_noise(x * 0.1, (y - flying) * 0.1), 0, 1, -400, 400)
            py5.vertex(x * scl, y * scl, z1)
            
            z2 = py5.remap(py5.os_noise(x * 0.1, (y + 1 - flying) * 0.1), 0, 1, -400, 400)
            py5.vertex(x * scl, (y + 1) * scl, z2)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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

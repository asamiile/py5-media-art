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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(210, 10, 95) # Soft light background
    
    time = py5.frame_count * 0.02
    
    py5.directional_light(0, 0, 100, 0.5, 0.5, -1)
    py5.ambient_light(0, 0, 40)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(time * 0.2)
    
    py5.translate(-SIZE[0]*0.8, -SIZE[1]*0.8, 0)
    
    cols = 40
    rows = 40
    scl = 100
    
    py5.no_stroke()
    py5.fill(40, 10, 100) # Off-white paper color
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Calculate fold angles based on position and time
            # Using alternating sine waves to create zig-zag folds
            fold_amount = py5.sin(time + x * 0.5) * py5.cos(time + y * 0.5)
            z1 = fold_amount * 150 * (1 if (x+y)%2==0 else -1)
            
            fold_amount_next = py5.sin(time + x * 0.5) * py5.cos(time + (y+1) * 0.5)
            z2 = fold_amount_next * 150 * (1 if (x+y+1)%2==0 else -1)
            
            py5.vertex(x * scl, y * scl, z1)
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

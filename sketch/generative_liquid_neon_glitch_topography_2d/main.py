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
from lib.safety import apply_anti_flicker_filter

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 15)

def draw():
    # Motion blur effect
    py5.no_stroke()
    py5.fill(10, 10, 15, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    time_t = py5.frame_count * 0.015
    
    # Grid of distorted topography
    py5.stroke_weight(2)
    py5.no_fill()
    
    cols = 60
    rows = 40
    margin_x = py5.width * 0.1
    margin_y = py5.height * 0.1
    w = py5.width - margin_x * 2
    h = py5.height - margin_y * 2
    
    x_step = w / cols
    y_step = h / rows
    
    for j in range(rows):
        py5.begin_shape()
        for i in range(cols + 1):
            x = margin_x + i * x_step
            y = margin_y + j * y_step
            
            # 2D noise topography
            noise_val = py5.os_noise(i * 0.1, j * 0.1 - time_t * 2)
            
            # Glitch effect
            glitch = 0
            if py5.random(1) < 0.05 and py5.frame_count % 30 < 10:
                glitch = py5.random(-50, 50)
                
            offset_y = -noise_val * 300 + glitch
            
            # Color based on height and time
            hue = (200 + noise_val * 100 + time_t * 100) % 360
            
            if glitch != 0:
                py5.stroke((hue + 180) % 360, 90, 100, 80)
            else:
                py5.stroke(hue, 80, 100, 60)
            
            py5.vertex(x, y + offset_y)
        py5.end_shape()

    apply_anti_flicker_filter(0.5)
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

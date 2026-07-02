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

num_pendulums = 80
N = 10

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(10)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 15) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    margin_y = 200
    margin_x = 400
    
    spacing = (SIZE[1] - 2 * margin_y) / (num_pendulums - 1)
    amp = (SIZE[0] - 2 * margin_x) / 2
    
    cx = SIZE[0] / 2
    
    py5.no_fill()
    py5.stroke(200, 50, 100, 20)
    py5.stroke_weight(2)
    py5.begin_shape()
    
    for i in range(num_pendulums):
        f_n = (N + i) / DURATION_SEC
        
        x = cx + amp * np.cos(2 * np.pi * f_n * t)
        y = margin_y + i * spacing
        
        py5.vertex(x, y)
        
    py5.end_shape()
    
    py5.no_stroke()
    for i in range(num_pendulums):
        f_n = (N + i) / DURATION_SEC
        x = cx + amp * np.cos(2 * np.pi * f_n * t)
        y = margin_y + i * spacing
        
        hue = (i * 360 / num_pendulums + t * 20) % 360
        py5.fill(hue, 80, 100, 60)
        
        size = 12 + np.sin(t * np.pi + i * 0.1) * 4
        py5.ellipse(x, y, size, size)
        
        py5.fill(hue, 40, 100, 100)
        py5.ellipse(x, y, size*0.5, size*0.5)

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

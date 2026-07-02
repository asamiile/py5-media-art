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
DURATION_SEC = 20
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

def draw():
    py5.background(10, 10, 5, 20) # Slight fade for motion blur
    
    time = py5.frame_count * 0.01
    
    cols = 70
    rows = 40
    w = SIZE[0] / cols
    h = SIZE[1] / rows
    
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    for i in range(cols):
        for j in range(rows):
            x = i * w + w/2
            y = j * h + h/2
            
            # Flow field angle
            n = py5.os_noise(i * 0.05, j * 0.05, time)
            n2 = py5.os_noise(i * 0.05 + 100, j * 0.05 + 100, time)
            
            angle = n * py5.TWO_PI * 4
            
            # Length based on secondary noise
            length = py5.remap(n2, 0, 1, w*0.2, w*2.5)
            
            # Color based on angle
            hue = (py5.degrees(angle) + time * 50) % 360
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(angle)
            
            # Draw an arrow-like shape
            py5.fill(hue, 80, 80, 50)
            py5.begin_shape()
            py5.vertex(-length/2, -h*0.1)
            py5.vertex(length/2 - w*0.2, -h*0.1)
            py5.vertex(length/2 - w*0.2, -h*0.3)
            py5.vertex(length/2, 0)
            py5.vertex(length/2 - w*0.2, h*0.3)
            py5.vertex(length/2 - w*0.2, h*0.1)
            py5.vertex(-length/2, h*0.1)
            py5.end_shape(py5.CLOSE)
            
            py5.pop_matrix()
            
    py5.blend_mode(py5.BLEND)

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

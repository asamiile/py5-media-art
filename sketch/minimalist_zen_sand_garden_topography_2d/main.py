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
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    py5.background(40, 5, 95) # Off-white sand color
    
    time = py5.frame_count * 0.005
    
    py5.no_fill()
    py5.stroke(220, 20, 20) # Dark grey lines
    py5.stroke_weight(4)
    
    # We draw many horizontal lines that get displaced by noise
    num_lines = 150
    points_per_line = 300
    
    margin_x = 200
    margin_y = 200
    
    w = SIZE[0] - margin_x * 2
    h = SIZE[1] - margin_y * 2
    
    for i in range(num_lines):
        y_base = margin_y + (i / float(num_lines)) * h
        
        # We fill below the line with the background color to hide lines behind it
        py5.fill(40, 5, 95)
        py5.begin_shape()
        
        # Start corner for fill
        py5.vertex(margin_x, SIZE[1])
        py5.vertex(margin_x, y_base)
        
        for j in range(points_per_line + 1):
            x = margin_x + (j / float(points_per_line)) * w
            
            # Distance from center to taper the noise
            dist_to_center = abs(j / float(points_per_line) - 0.5) * 2
            taper = max(0, 1.0 - dist_to_center) ** 2
            
            n = py5.os_noise(j * 0.03 - time, i * 0.05 - time)
            
            y_offset = py5.remap(n, 0, 1, -200, 50) * taper
            
            py5.vertex(x, y_base + y_offset)
            
        # End corner for fill
        py5.vertex(SIZE[0] - margin_x, SIZE[1])
        py5.end_shape(py5.CLOSE)

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

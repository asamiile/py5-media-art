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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_LINES = 1500

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Motion blur background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Slow majestic rotation of the entire structure
    py5.rotate_x(py5.sin(t * 0.5) * 0.3)
    py5.rotate_y(t * 0.2)
    py5.rotate_z(py5.cos(t * 0.3) * 0.2)
    
    r1 = 600
    r2 = 400
    r3 = 200
    
    # We will draw lines between points moving on multiple circles.
    # The phase multipliers change over time, morphing the string art.
    m1 = 2 + py5.sin(t * 0.2)
    m2 = 3 + py5.cos(t * 0.3)
    m3 = 5 + py5.sin(t * 0.1)
    
    py5.stroke_weight(1)
    
    # To use begin_shape(LINES) efficiently
    py5.begin_shape(py5.LINES)
    
    for i in range(NUM_LINES):
        # Parametric index
        p = py5.TWO_PI * (i / NUM_LINES)
        
        # Point A on the outer circle
        a_theta = p * m1 + t
        x1 = r1 * py5.cos(a_theta)
        y1 = r1 * py5.sin(a_theta)
        z1 = r3 * py5.cos(p * 3 + t) # Z-axis oscillation
        
        # Point B on the inner circle
        b_theta = p * m2 - t * 1.5
        x2 = r2 * py5.cos(b_theta)
        y2 = r2 * py5.sin(b_theta)
        z2 = r3 * py5.sin(p * 5 - t)
        
        # Map color to index
        hue = (i / NUM_LINES * 360 + t * 50) % 360
        py5.stroke(hue, 90, 100, 40)
        
        py5.vertex(x1, y1, z1)
        py5.vertex(x2, y2, z2)
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

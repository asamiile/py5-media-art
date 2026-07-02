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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Optimization for numpy calculations
RESOLUTION = 10000
theta = np.linspace(0, 100 * np.pi, RESOLUTION)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(10, 15, 25, 30) # slight trail effect
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    py5.translate(py5.width / 2, py5.height / 2)
    
    num_roses = 6
    for i in range(num_roses):
        # Shift parameters continuously based on time and index
        k = 2 + np.sin(t + i) * 1.5 + (py5.noise(t, i) - 0.5) * 5
        scale = 300 + 200 * np.cos(t * 0.5 + i)
        
        # Calculate rose pattern (r = cos(k * theta))
        r = np.cos(k * theta) * scale
        
        # Add a gentle rotation
        x = r * np.cos(theta + t * 0.2 + i * py5.PI / 3)
        y = r * np.sin(theta + t * 0.2 + i * py5.PI / 3)
        
        # Colors: transition through neon spectrum
        c_val = (t * 50 + i * 40) % 255
        py5.color_mode(py5.HSB, 255)
        py5.stroke(c_val, 200, 255, 100)
        py5.stroke_weight(2)
        
        # Fast drawing with shape
        py5.begin_shape()
        # Subsample for speed if needed, but 10k is fast enough in numpy
        for pt_x, pt_y in zip(x, y):
            py5.vertex(pt_x, pt_y)
        py5.end_shape()
        
        py5.color_mode(py5.RGB, 255)

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

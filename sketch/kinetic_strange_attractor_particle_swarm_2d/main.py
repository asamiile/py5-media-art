from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Clifford Attractor Parameters
# x_{n+1} = sin(a * y_n) + c * cos(a * x_n)
# y_{n+1} = sin(b * x_n) + d * cos(b * y_n)

NUM_PARTICLES = 60000

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global x, y
    # Initialize particle positions randomly between -2 and 2
    x = np.random.uniform(-2, 2, NUM_PARTICLES)
    y = np.random.uniform(-2, 2, NUM_PARTICLES)
    
    py5.background(0)
    
def draw():
    global x, y
    
    # Fade background slightly
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 5) # Slow fade
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Modulate parameters of the Clifford attractor over time
    a = -1.4 + math.sin(t * py5.TWO_PI) * 0.2
    b = 1.6 + math.cos(t * py5.TWO_PI * 2) * 0.1
    c = 1.0 + math.sin(t * py5.TWO_PI * 1.5) * 0.2
    d = 0.7 + math.cos(t * py5.TWO_PI * 0.5) * 0.15
    
    # Advance the particles by taking multiple steps per frame to trace the lines
    py5.blend_mode(py5.ADD)
    py5.stroke(190, 80, 100, 20) # Cyan-blue, low opacity
    py5.stroke_weight(2)
    
    steps_per_frame = 2
    
    scale_factor = min(py5.width, py5.height) * 0.2
    
    for _ in range(steps_per_frame):
        # Calculate next positions using numpy vectorized operations
        nx = np.sin(a * y) + c * np.cos(a * x)
        ny = np.sin(b * x) + d * np.cos(b * y)
        
        # Smoothly interpolate to the next position instead of jumping instantly
        x = x + (nx - x) * 0.05
        y = y + (ny - y) * 0.05
        
        # Map to screen coordinates
        screen_x = py5.width / 2 + x * scale_factor
        screen_y = py5.height / 2 + y * scale_factor
        
        points = np.column_stack((screen_x, screen_y))
        
        py5.points(points)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
        import os
        os._exit(0)

py5.run_sketch()

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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    
def draw():
    t = py5.frame_count * 0.02
    
    # We will use pixel manipulation for performance since drawing millions of rects is slow
    py5.load_pixels()
    
    # Precompute per-frame constants
    w = py5.width
    h = py5.height
    
    # Get the raw np pixels array to modify
    # py5 has py5.np_pixels (if loaded) which is a numpy array view
    py5.load_np_pixels()
    
    # Since numpy array in P2D is shape (height, width, 1) containing ARGB ints
    # We can use a vectorized approach or draw lines. Since we are in P2D and want to make it easy:
    # Actually, drawing shapes might be fast enough if we use a grid of larger rectangles (e.g., 8x8)
    # Let's use rects to be safe with standard processing.
    
    py5.background(0)
    
    res = 8 # pixel resolution block
    for y in range(0, py5.height, res):
        for x in range(0, py5.width, res):
            n1 = py5.os_noise(x * 0.003, y * 0.003, t)
            n2 = py5.os_noise(x * 0.01 + 100, y * 0.01 + 100, t * 0.8)
            
            # Interference pattern
            val = (py5.sin(n1 * 20 + n2 * 10) + 1) * 0.5
            
            hue = py5.remap(val, 0, 1, 150, 360) % 360
            sat = py5.remap(n2, 0, 1, 60, 100)
            bri = py5.remap(val, 0, 1, 20, 100)
            
            py5.fill(hue, sat, bri)
            py5.rect(x, y, res, res)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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

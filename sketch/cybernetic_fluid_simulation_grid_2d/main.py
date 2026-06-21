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
    py5.background(0)

def draw():
    py5.background(0, 0, 5, 20)
    
    py5.blend_mode(py5.ADD)
    
    grid_size = 40
    cols = py5.width // grid_size
    rows = py5.height // grid_size
    
    t = py5.frame_count * 0.01
    
    # Render the fluid grid
    for y in range(rows):
        for x in range(cols):
            # Complex fluid-like motion using multiple noise octaves
            n1 = py5.os_noise(x * 0.05, y * 0.05, t)
            n2 = py5.os_noise(x * 0.1 - t, y * 0.1, t * 1.5)
            
            density = (n1 * 0.6 + n2 * 0.4)
            
            if density > 0.4:
                size_mod = py5.remap(density, 0.4, 1.0, 5, grid_size * 0.9)
                hue = py5.remap(density, 0.4, 1.0, 180, 320)
                alpha = py5.remap(density, 0.4, 1.0, 10, 100)
                
                py5.fill(hue, 90, 90, alpha)
                py5.rect(x * grid_size + (grid_size - size_mod) / 2,
                         y * grid_size + (grid_size - size_mod) / 2,
                         size_mod, size_mod)

    py5.blend_mode(py5.BLEND)

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

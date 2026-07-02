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
DURATION_SEC = 10  # 10 seconds
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global cols, rows, tile_size
    tile_size = 120
    cols = SIZE[0] // tile_size + 2
    rows = SIZE[1] // tile_size + 2

def draw():
    py5.background(10, 10, 10, 30) # slight trail effect
    py5.stroke_weight(4)
    py5.no_fill()
    
    t = py5.frame_count * 0.02
    
    for i in range(cols):
        for j in range(rows):
            x = i * tile_size
            y = j * tile_size
            
            # noise-based rotation
            n = py5.os_noise(i * 0.1, j * 0.1, t)
            
            with py5.push_matrix():
                py5.translate(x, y)
                if n > 0:
                    py5.rotate(py5.PI / 2)
                
                # Colors based on position and time
                hue = (180 + 100 * py5.os_noise(i * 0.05, j * 0.05, t * 0.5)) % 360
                py5.stroke(hue, 80, 90, 80)
                
                py5.arc(0, 0, tile_size, tile_size, 0, py5.PI / 2)
                py5.arc(tile_size, tile_size, tile_size, tile_size, py5.PI, py5.PI * 1.5)

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

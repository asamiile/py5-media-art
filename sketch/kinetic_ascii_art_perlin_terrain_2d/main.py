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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

CHARS = " .,-~:;=!*#$@"
CELL_SIZE = 16

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.text_font(py5.create_font("Courier New", CELL_SIZE))
    py5.text_align(py5.CENTER, py5.CENTER)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 20, 15)
    
    t = py5.frame_count * 0.02
    
    cols = SIZE[0] // CELL_SIZE + 2
    rows = int(SIZE[1] // (CELL_SIZE * 0.75)) + 4
    
    for y in range(rows):
        for x in range(cols):
            nx = x * 0.05
            ny = y * 0.05 - t * 0.5
            
            val = py5.os_noise(nx, ny, t * 0.1)
            
            height_offset = val * 300
            
            px = x * CELL_SIZE
            # Isometric offset: shift odd rows by half width
            if y % 2 == 1:
                px += CELL_SIZE / 2
                
            py_coord = y * CELL_SIZE * 0.75 - height_offset + 300
            
            char_idx = int(py5.remap(val, 0, 1, 0, len(CHARS)))
            char_idx = max(0, min(char_idx, len(CHARS) - 1))
            char = CHARS[char_idx]
            
            brightness = py5.remap(val, 0, 1, 50, 255)
            if val > 0.6:
                py5.fill(150, 255, 150, brightness)
            else:
                py5.fill(0, 200, 100, brightness)
                
            py5.text(char, px, py_coord)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

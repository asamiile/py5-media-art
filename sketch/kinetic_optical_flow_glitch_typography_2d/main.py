from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SPACING = 30
COLS = SIZE[0] // GRID_SPACING + 2
ROWS = SIZE[1] // GRID_SPACING + 2

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;':,./<>?"
grid_chars = np.random.choice(list(chars), size=(COLS, ROWS))

font = None

def setup():
    global font
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    font = py5.create_font("Courier New", 24)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)
    
def draw():
    py5.background(10, 10, 10)
    
    curr_frame = py5.frame_count
    t = curr_frame * 0.01
    
    for c in range(COLS):
        for r in range(ROWS):
            x = c * GRID_SPACING
            y = r * GRID_SPACING
            
            n_x = py5.os_noise(c * 0.05, r * 0.05, t)
            n_y = py5.os_noise(c * 0.05 + 100, r * 0.05 + 100, t)
            
            dx = (n_x - 0.5) * 150
            dy = (n_y - 0.5) * 150
            
            nx = x + dx
            ny = y + dy
            
            turb = abs(n_x - 0.5) + abs(n_y - 0.5)
            
            char = grid_chars[c, r]
            
            if turb > 0.35 and py5.os_noise(c, r, t*5) > 0.6:
                py5.blend_mode(py5.ADD)
                py5.fill(255, 0, 0, 200)
                py5.text(char, nx - 4, ny)
                py5.fill(0, 255, 255, 200)
                py5.text(char, nx + 4, ny)
                py5.blend_mode(py5.BLEND)
            else:
                c_val = int(py5.remap(turb, 0, 0.4, 50, 255))
                py5.fill(c_val)
                py5.text(char, nx, ny)

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

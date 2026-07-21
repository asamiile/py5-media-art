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

# Grid settings
COLS = 160
ROWS = 90
CELL_W = SIZE[0] / COLS
CELL_H = SIZE[1] / ROWS

CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=-/\\|")
grid_chars = np.random.choice(CHARS, (ROWS, COLS))
grid_melt = np.zeros((ROWS, COLS))
grid_y_offset = np.zeros((ROWS, COLS))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.text_align(py5.CENTER, py5.CENTER)
    try:
        font = py5.create_font("Courier New", CELL_H * 1.2)
        py5.text_font(font)
    except:
        py5.text_size(CELL_H * 1.2)

def draw():
    py5.background(5, 10, 5)
    
    t = py5.frame_count / 60.0
    
    # Global melt line moves down
    melt_line = (t - 2.0) / 10.0 * ROWS
    
    for r in range(ROWS):
        # Noise to make melt line irregular
        for c in range(COLS):
            noise_val = py5.os_noise(c * 0.1, r * 0.1, t * 0.5)
            if r < melt_line + noise_val * 15:
                grid_melt[r, c] = 1.0
                
            if grid_melt[r, c] > 0:
                # Flow downwards
                speed = py5.os_noise(c * 0.05, r * 0.05, t) * 3
                grid_y_offset[r, c] += speed
                # Change character randomly
                if random.random() < 0.1:
                    grid_chars[r, c] = random.choice(CHARS)

    for r in range(ROWS):
        for c in range(COLS):
            x = c * CELL_W + CELL_W / 2
            y = r * CELL_H + CELL_H / 2 + grid_y_offset[r, c]
            
            char = grid_chars[r, c]
            
            # Color
            if grid_melt[r, c] > 0:
                speed = py5.os_noise(c * 0.05, r * 0.05, t) * 3
                if speed > 2.2:
                    py5.fill(0, 255, 255) # Cyan glitch
                elif speed > 1.8:
                    py5.fill(255, 0, 255) # Magenta glitch
                else:
                    py5.fill(0, 255, 65, 200) # Bright green
            else:
                py5.fill(0, 143, 17, 150) # Dim green for static text
                
            py5.text(char, x, y)

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

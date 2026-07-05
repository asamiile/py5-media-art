from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import numpy as np
import scipy.signal
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Cellular Automata Grid
RES = 4
COLS = SIZE[0] // RES
ROWS = SIZE[1] // RES

grid = np.zeros((ROWS, COLS), dtype=np.uint8)
kernel = np.array([[1, 1, 1],
                   [1, 0, 1],
                   [1, 1, 1]], dtype=np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize a few central seeds
    cx, cy = COLS // 2, ROWS // 2
    grid[cy-2:cy+3, cx-2:cx+3] = np.random.randint(0, 2, (5, 5))

def draw():
    global grid
    
    # Run a continuous variation of Conway's Game of Life / Day & Night
    neighbors = scipy.signal.convolve2d(grid, kernel, mode='same', boundary='wrap')
    
    # Custom rule:
    # Survive if 3, 4, 6, 7, 8
    # Birth if 3, 6, 7, 8
    survive = (grid == 1) & ((neighbors == 3) | (neighbors == 4) | (neighbors == 6) | (neighbors == 7) | (neighbors == 8))
    birth = (grid == 0) & ((neighbors == 3) | (neighbors == 6) | (neighbors == 7) | (neighbors == 8))
    
    grid = (survive | birth).astype(np.uint8)
    
    # Inject new random seeds dynamically
    t = py5.frame_count * 0.1
    if py5.frame_count % 30 == 0:
        rx = int((math.sin(t) * 0.4 + 0.5) * COLS)
        ry = int((math.cos(t * 1.5) * 0.4 + 0.5) * ROWS)
        grid[ry-5:ry+5, rx-5:rx+5] = np.random.randint(0, 2, (10, 10))

    # Map to pixels
    py5.load_np_pixels()
    
    # Base gradient colors
    x_coords, y_coords = np.meshgrid(np.arange(COLS), np.arange(ROWS))
    r_color = (150 + np.sin(x_coords * 0.01 + t) * 105).astype(np.uint32)
    g_color = (150 + np.cos(y_coords * 0.01 + t) * 105).astype(np.uint32)
    b_color = (150 + np.sin((x_coords + y_coords) * 0.01 + t) * 105).astype(np.uint32)
    
    a = np.full((ROWS, COLS), 255, dtype=np.uint32)
    bg_r = np.full((ROWS, COLS), 20, dtype=np.uint32)
    bg_g = np.full((ROWS, COLS), 20, dtype=np.uint32)
    bg_b = np.full((ROWS, COLS), 25, dtype=np.uint32)
    
    # Mix based on grid mask
    mask = (grid == 1)
    
    r_out = np.where(mask, r_color, bg_r)
    g_out = np.where(mask, g_color, bg_g)
    b_out = np.where(mask, b_color, bg_b)
    
    if RES > 1:
        # Nearest neighbor scale up
        r_out = np.repeat(np.repeat(r_out, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]
        g_out = np.repeat(np.repeat(g_out, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]
        b_out = np.repeat(np.repeat(b_out, RES, axis=0), RES, axis=1)[:SIZE[1], :SIZE[0]]

    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = r_out
    py5.np_pixels[..., 2] = g_out
    py5.np_pixels[..., 3] = b_out
    
    py5.update_np_pixels()

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

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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Cyclic Cellular Automata Parameters
N_STATES = 12
SCALE = 8
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

grid = np.random.randint(0, N_STATES, (H, W), dtype=np.int32)
next_grid = np.zeros_like(grid)
colors = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    py5.color_mode(py5.HSB, N_STATES, 100, 100)
    for i in range(N_STATES):
        colors.append(py5.color(i, 80, 90))

def draw():
    global grid, next_grid
    
    # Draw current grid
    py5.background(0)
    for y in range(H):
        for x in range(W):
            py5.fill(colors[grid[y, x]])
            py5.rect(x * SCALE, y * SCALE, SCALE, SCALE)
            
    # Update logic (Cyclic Cellular Automata)
    # vectorized numpy approach for speed
    up = np.roll(grid, 1, axis=0)
    down = np.roll(grid, -1, axis=0)
    left = np.roll(grid, 1, axis=1)
    right = np.roll(grid, -1, axis=1)
    
    # A cell changes to the next state if any of its neighbors is exactly next_state
    next_state = (grid + 1) % N_STATES
    mask = (up == next_state) | (down == next_state) | (left == next_state) | (right == next_state)
    
    next_grid = np.where(mask, next_state, grid)
    
    # Add random mutations occasionally to keep it dynamic
    if py5.frame_count % 30 == 0:
        rx = random.randint(0, W-1)
        ry = random.randint(0, H-1)
        next_grid[ry-5:ry+5, rx-5:rx+5] = np.random.randint(0, N_STATES, (10, 10))
    
    grid = next_grid

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

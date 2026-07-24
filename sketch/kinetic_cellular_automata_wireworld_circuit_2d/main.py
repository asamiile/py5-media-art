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

# Wireworld grid scale (smaller grid scaled up for blocky aesthetic)
SCALE = 2
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid
    # Generate random mazes/circuits using noise thresholding
    x = np.linspace(0, 10, W)
    y = np.linspace(0, 10, H)
    X, Y = np.meshgrid(x, y)
    
    noise_grid = np.zeros((H, W))
    for iy in range(H):
        for ix in range(W):
            noise_grid[iy, ix] = py5.os_noise(X[iy, ix], Y[iy, ix])
            
    # Set conductor (3) where noise is between a certain band (creates paths)
    grid = np.zeros((H, W), dtype=np.uint8)
    grid[(noise_grid > 0.45) & (noise_grid < 0.55)] = 3
    
    # Randomly spawn electron heads (1) and tails (2) on conductors
    cond_mask = grid == 3
    cond_indices = np.argwhere(cond_mask)
    num_spawns = len(cond_indices) // 100
    
    spawn_idx = cond_indices[np.random.choice(len(cond_indices), num_spawns, replace=False)]
    for idx in spawn_idx:
        grid[idx[0], idx[1]] = 1 # head
        
    # Also add some random structures (boxes) to act as oscillators
    for _ in range(50):
        bx = random.randint(10, W - 10)
        by = random.randint(10, H - 10)
        grid[by:by+3, bx:bx+3] = 3
        grid[by+1, bx] = 1 # inject

def draw():
    global grid
    
    # 0 = Empty (0, 0, 20)
    # 1 = Head (0, 255, 255)
    # 2 = Tail (255, 0, 255)
    # 3 = Conductor (255, 200, 0)
    
    heads = (grid == 1)
    
    counts = np.zeros_like(grid, dtype=np.uint8)
    counts[:-1, :] += heads[1:, :]
    counts[1:, :] += heads[:-1, :]
    counts[:, :-1] += heads[:, 1:]
    counts[:, 1:] += heads[:, :-1]
    counts[:-1, :-1] += heads[1:, 1:]
    counts[1:, 1:] += heads[:-1, :-1]
    counts[:-1, 1:] += heads[1:, :-1]
    counts[1:, :-1] += heads[:-1, 1:]
    
    new_grid = grid.copy()
    new_grid[grid == 1] = 2
    new_grid[grid == 2] = 3
    cond = grid == 3
    turn_to_head = cond & ((counts == 1) | (counts == 2))
    new_grid[turn_to_head] = 1
    
    grid = new_grid
    
    # Render
    py5.load_np_pixels()
    
    # Color palette (ARGB) - Py5 np_pixels uses A, R, G, B
    c_empty = np.array([255, 0, 0, 20], dtype=np.uint8) 
    c_head = np.array([255, 0, 255, 255], dtype=np.uint8)
    c_tail = np.array([255, 255, 0, 255], dtype=np.uint8)
    c_cond = np.array([255, 255, 200, 0], dtype=np.uint8)
    
    img_data = np.zeros((H, W, 4), dtype=np.uint8)
    img_data[:] = c_empty
    img_data[grid == 1] = c_head
    img_data[grid == 2] = c_tail
    img_data[grid == 3] = c_cond
    
    # Repeat for nearest neighbor scaling
    if SCALE > 1:
        img_data = np.repeat(np.repeat(img_data, SCALE, axis=0), SCALE, axis=1)
        
    py5.np_pixels[:] = img_data
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
        import os
        os._exit(0)

py5.run_sketch()

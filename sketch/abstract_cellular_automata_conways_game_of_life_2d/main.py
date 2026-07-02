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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_W = 400
GRID_H = 250
CELL_SIZE = 10

grid = None
ages = None

def get_neighbors(g):
    # Shift grid to get neighbors
    n = np.zeros_like(g)
    n[:-1, :] += g[1:, :]
    n[1:, :] += g[:-1, :]
    n[:, :-1] += g[:, 1:]
    n[:, 1:] += g[:, :-1]
    n[:-1, :-1] += g[1:, 1:]
    n[1:, 1:] += g[:-1, :-1]
    n[:-1, 1:] += g[1:, :-1]
    n[1:, :-1] += g[:-1, 1:]
    return n

def setup():
    global grid, ages
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
    # Initialize random grid
    grid = np.random.choice([0, 1], size=(GRID_W, GRID_H), p=[0.8, 0.2])
    ages = np.zeros_like(grid)

def draw():
    global grid, ages
    py5.background(10, 15, 20)
    
    # Update Conway's Game of Life (Numpy approach is fast)
    neighbors = get_neighbors(grid)
    
    new_grid = grid.copy()
    new_grid[(grid == 1) & (neighbors < 2)] = 0
    new_grid[(grid == 1) & (neighbors > 3)] = 0
    new_grid[(grid == 0) & (neighbors == 3)] = 1
    
    # Update ages
    ages[new_grid == 1] += 1
    ages[new_grid == 0] = 0
    
    grid = new_grid
    
    time_val = py5.frame_count * 0.01
    zoom = 1.0 + time_val * 0.2
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    py5.scale(zoom)
    py5.translate(-SIZE[0]/2, -SIZE[1]/2)
    
    offset_x = (SIZE[0] - GRID_W * CELL_SIZE) / 2
    offset_y = (SIZE[1] - GRID_H * CELL_SIZE) / 2
    py5.translate(offset_x, offset_y)
    
    # Render alive cells
    alive_indices = np.argwhere(grid == 1)
    
    for x_idx, y_idx in alive_indices:
        age = ages[x_idx, y_idx]
        hue = (200 + age * 2) % 360
        bri = min(100, 50 + age * 5)
        
        py5.fill(hue, 80, bri)
        py5.rect(x_idx * CELL_SIZE, y_idx * CELL_SIZE, CELL_SIZE * 0.8, CELL_SIZE * 0.8)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

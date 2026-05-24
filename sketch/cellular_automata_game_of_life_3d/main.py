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
from scipy.signal import convolve

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# 3D Grid size
GRID_SIZE = 32
SPACING = 15

# Initialize 3D grid with random noise in the center
grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=int)
center = GRID_SIZE // 2
size = 6
grid[center-size:center+size, center-size:center+size, center-size:center+size] = np.random.choice([0, 1], size=(size*2, size*2, size*2), p=[0.7, 0.3])

# Track age of cells for coloring
age = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=int)

# Convolution kernel to count 26 neighbors
kernel = np.ones((3, 3, 3), dtype=int)
kernel[1, 1, 1] = 0

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global grid, age
    
    py5.background(10)
    
    # Run the cellular automata step every 4 frames (so it's not too fast to see)
    if py5.frame_count % 4 == 0:
        # Count neighbors
        neighbors = convolve(grid, kernel, mode='same')
        
        # Rule "4555" 3D Game of Life
        # Survive if 4 or 5 neighbors
        # Born if 5 neighbors
        survive = ((neighbors == 4) | (neighbors == 5)) & (grid == 1)
        born = (neighbors == 5) & (grid == 0)
        
        new_grid = (survive | born).astype(int)
        
        # Update age
        age[new_grid == 1] += 1
        age[new_grid == 0] = 0
        
        grid = new_grid
        
        # If the grid dies out, respawn it
        if np.sum(grid) < 10:
            grid[center-size:center+size, center-size:center+size, center-size:center+size] = np.random.choice([0, 1], size=(size*2, size*2, size*2), p=[0.7, 0.3])
            age[:] = 0

    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Rotate the camera
    t = py5.frame_count * 0.01
    py5.rotate_y(t)
    py5.rotate_x(t * 0.7)
    
    # Center the grid
    offset = (GRID_SIZE * SPACING) / 2
    py5.translate(-offset, -offset, -offset)
    
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(180, 100, 80, -1, -1, 1)
    
    # Render active cells
    active_indices = np.argwhere(grid == 1)
    
    py5.no_stroke()
    for x, y, z in active_indices:
        py5.push_matrix()
        py5.translate(x * SPACING, y * SPACING, z * SPACING)
        
        cell_age = age[x, y, z]
        hue = (cell_age * 10 + t * 50 + x * 2 + y * 2) % 360
        
        py5.fill(hue, 90, 100, 80)
        
        # Newly born cells start small and grow
        s = min(SPACING * 0.8, SPACING * 0.2 + cell_age * 0.1)
        py5.box(s)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

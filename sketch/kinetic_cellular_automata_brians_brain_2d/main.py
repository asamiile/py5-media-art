from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.signal import convolve2d
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

# Grid size (upscaled later)
GRID_W, GRID_H = 480, 270
grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)

# Initial random noise
grid[np.random.random((GRID_H, GRID_W)) < 0.05] = 2

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 30)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    global grid
    
    # Kernel counts firing neighbors
    kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
    
    # 2 is firing, 1 is refractory, 0 is ready
    firing = (grid == 2)
    refractory = (grid == 1)
    ready = (grid == 0)
    
    # Count firing neighbors
    neighbors = convolve2d(firing.astype(int), kernel, mode='same', boundary='wrap')
    
    # Brian's Brain rules
    new_grid = np.zeros_like(grid)
    
    # Firing becomes Refractory
    new_grid[firing] = 1
    # Refractory becomes Ready (0) -> default
    
    # Ready becomes Firing if exactly 2 neighbors are firing
    new_grid[ready & (neighbors == 2)] = 2
    
    # Randomly stimulate grid to keep it alive
    if py5.frame_count % 30 == 0:
        new_grid[np.random.random((GRID_H, GRID_W)) < 0.001] = 2
        
    grid = new_grid
    
    # Rendering
    py5.background(5, 5, 15)
    
    # We will draw this blocky but vibrant
    cell_w = py5.width / GRID_W
    cell_h = py5.height / GRID_H
    
    # Get y, x indices
    fy, fx = np.where(grid == 2)
    ry, rx = np.where(grid == 1)
    
    # Draw Refractory
    py5.fill(80, 20, 120)
    for i in range(len(rx)):
        py5.rect(rx[i] * cell_w, ry[i] * cell_h, cell_w, cell_h)
        
    # Draw Firing
    py5.fill(0, 255, 255)
    for i in range(len(fx)):
        py5.rect(fx[i] * cell_w, fy[i] * cell_h, cell_w, cell_h)

    # Post processing glowing effect
    py5.blend_mode(py5.ADD)
    py5.fill(0, 255, 255, 10)
    for i in range(len(fx)):
        py5.rect(fx[i] * cell_w - cell_w, fy[i] * cell_h - cell_h, cell_w * 3, cell_h * 3)
    py5.blend_mode(py5.BLEND)

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

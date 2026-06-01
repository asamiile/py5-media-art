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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Sand simulation setup
GRID_SCALE = 4
GRID_W = SIZE[0] // GRID_SCALE
GRID_H = SIZE[1] // GRID_SCALE

# 0: empty, 1: obstacle, >1: sand (color index)
grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)

colors = [
    (15, 15, 15),       # Background
    (40, 40, 40),       # Obstacle
    (330, 90, 100),     # Hot Pink
    (200, 90, 100),     # Electric Blue
    (45, 90, 100)       # Gold
]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    
    # Create geometric obstacles
    for i in range(5):
        cx = py5.random(0.2, 0.8) * GRID_W
        cy = py5.random(0.3, 0.8) * GRID_H
        w = py5.random(0.1, 0.3) * GRID_W
        h = py5.random(0.02, 0.05) * GRID_H
        grid[int(cy):int(cy+h), int(cx-w/2):int(cx+w/2)] = 1

def update_grid():
    global grid
    new_grid = grid.copy()
    
    # Iterate from bottom to top
    for y in range(GRID_H - 2, -1, -1):
        # Find sand particles
        sand_mask = grid[y, :] > 1
        x_indices = np.where(sand_mask)[0]
        
        # Shuffle for random falling direction (left/right)
        np.random.shuffle(x_indices)
        
        for x in x_indices:
            val = grid[y, x]
            # Try straight down
            if grid[y+1, x] == 0 and new_grid[y+1, x] == 0:
                new_grid[y, x] = 0
                new_grid[y+1, x] = val
            else:
                # Try diagonally
                left = x > 0 and grid[y+1, x-1] == 0 and new_grid[y+1, x-1] == 0
                right = x < GRID_W-1 and grid[y+1, x+1] == 0 and new_grid[y+1, x+1] == 0
                
                if left and right:
                    if py5.random() < 0.5:
                        new_grid[y, x] = 0
                        new_grid[y+1, x-1] = val
                    else:
                        new_grid[y, x] = 0
                        new_grid[y+1, x+1] = val
                elif left:
                    new_grid[y, x] = 0
                    new_grid[y+1, x-1] = val
                elif right:
                    new_grid[y, x] = 0
                    new_grid[y+1, x+1] = val

    grid = new_grid

def draw():
    py5.background(15, 15, 15)
    
    # Spawn new sand
    spawn_y = int(0.05 * GRID_H)
    for _ in range(50):
        spawn_x = int((py5.sin(py5.frame_count * 0.05) * 0.3 + 0.5) * GRID_W + py5.random(-20, 20))
        if 0 <= spawn_x < GRID_W and grid[spawn_y, spawn_x] == 0:
            color_idx = 2 + (py5.frame_count // 120) % 3  # Switch colors over time
            grid[spawn_y, spawn_x] = color_idx
            
    # Update simulation
    for _ in range(3):  # Multiple steps per frame for speed
        update_grid()
        
    # Render grid
    py5.load_np_pixels()
    
    # Map grid to pixel colors
    # We do this quickly by scaling the grid up
    for val in range(1, 5):
        if val == 1:
            py5.fill(*colors[val])
            for y in range(GRID_H):
                for x in range(GRID_W):
                    if grid[y, x] == val:
                        py5.rect(x * GRID_SCALE, y * GRID_SCALE, GRID_SCALE, GRID_SCALE)
        else:
            py5.fill(*colors[val])
            for y in range(GRID_H):
                for x in range(GRID_W):
                    if grid[y, x] == val:
                        py5.rect(x * GRID_SCALE, y * GRID_SCALE, GRID_SCALE, GRID_SCALE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

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

# 3D Grid for simple cellular automata growth
GRID_SIZE = 40
CELL_SIZE = 15

# States: 0 = empty, 1 = growing, 2 = mature
grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.int8)

# Initial seeds
grid[GRID_SIZE//2, GRID_SIZE//2, GRID_SIZE//2] = 1
grid[GRID_SIZE//3, GRID_SIZE//3, GRID_SIZE//3] = 1
grid[GRID_SIZE*2//3, GRID_SIZE*2//3, GRID_SIZE*2//3] = 1

def update_grid():
    global grid
    new_grid = grid.copy()
    
    # Very simple growth rule: if adjacent to growing, small chance to grow
    # We use vectorization by shifting arrays to count neighbors
    
    # 6-way neighbors
    neighbors_growing = (
        np.roll(grid == 1, 1, axis=0) + np.roll(grid == 1, -1, axis=0) +
        np.roll(grid == 1, 1, axis=1) + np.roll(grid == 1, -1, axis=1) +
        np.roll(grid == 1, 1, axis=2) + np.roll(grid == 1, -1, axis=2)
    )
    
    # Growth probability
    growth_prob = 0.05
    random_mask = np.random.random(grid.shape) < growth_prob
    
    # Empty cells adjacent to growing cells might grow
    new_grid[(grid == 0) & (neighbors_growing > 0) & random_mask] = 1
    
    # Mature growing cells after some time
    mature_prob = 0.02
    random_mature = np.random.random(grid.shape) < mature_prob
    new_grid[(grid == 1) & random_mature] = 2
    
    grid = new_grid

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 80, 5)
    
    py5.lights()
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(200, 80, 100, -1, -1, -1)
    
    t = py5.frame_count * 0.015
    
    # Update grid a few times per frame
    if py5.frame_count % 3 == 0:
        update_grid()
    
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    py5.rotate_x(t * 0.4)
    py5.rotate_y(t * 0.6)
    
    offset = (GRID_SIZE * CELL_SIZE) / 2
    py5.translate(-offset, -offset, -offset)
    
    py5.no_stroke()
    
    # Draw grid
    # Using instancing or batch drawing would be faster, but for 40^3 = 64k cells,
    # we only draw active ones. Let's see how many are active.
    active_indices = np.argwhere(grid > 0)
    
    for idx in active_indices:
        x, y, z = idx
        state = grid[x, y, z]
        
        px = x * CELL_SIZE
        py = y * CELL_SIZE
        pz = z * CELL_SIZE
        
        # Color based on position and state
        hue = (180 + x * 3 + y * 2 + z * 1 + t * 50) % 360
        
        if state == 1:
            py5.fill(hue, 90, 100, 80)
            sz = CELL_SIZE * 0.8
        else:
            py5.fill(hue, 60, 60, 90)
            sz = CELL_SIZE * 0.95
            
        py5.push_matrix()
        py5.translate(px, py, pz)
        py5.box(sz)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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

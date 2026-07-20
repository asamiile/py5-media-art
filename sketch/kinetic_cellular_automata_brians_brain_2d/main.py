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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

CELL_SIZE = 8
GRID_W = SIZE[0] // CELL_SIZE
GRID_H = SIZE[1] // CELL_SIZE

# States: 0 = Off, 1 = On, 2 = Dying
grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)

# Initialize randomly (seed the grid)
# To create cool structures, let's just make a random circle in the center
center_y, center_x = GRID_H // 2, GRID_W // 2
Y, X = np.ogrid[:GRID_H, :GRID_W]
dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
mask = dist_from_center < 100
random_starts = np.random.choice([0, 1, 2], size=(GRID_H, GRID_W), p=[0.7, 0.2, 0.1])
grid[mask] = random_starts[mask]

# For rendering effects: keep track of "age" (how long since it was On)
age_grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
# To avoid the grid getting static, we occasionally inject small gliders/noise
def inject_noise():
    y = random.randint(10, GRID_H - 10)
    x = random.randint(10, GRID_W - 10)
    grid[y:y+5, x:x+5] = np.random.choice([0, 1], size=(5, 5))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(280, 80, 10) # deep purple

def draw():
    global grid, age_grid
    
    # We do a few steps per frame to make it fast
    for _ in range(2):
        if random.random() < 0.02:
            inject_noise()
            
        # Count ON neighbors
        is_on = (grid == 1).astype(np.uint8)
        
        # Convolve to count neighbors using rolling sum (faster than full convolution matrix)
        # Using numpy array slicing for speed
        neighbors_on = sum(
            np.roll(np.roll(is_on, i, 0), j, 1)
            for i in (-1, 0, 1) for j in (-1, 0, 1)
            if (i != 0 or j != 0)
        )
        
        # Brian's Brain rules
        # 1. Any cell in state 1 (On) goes to state 2 (Dying)
        # 2. Any cell in state 2 (Dying) goes to state 0 (Off)
        # 3. Any cell in state 0 (Off) with exactly 2 neighbors in state 1 goes to state 1 (On)
        
        new_grid = np.zeros_like(grid)
        new_grid[grid == 1] = 2 # On -> Dying
        new_grid[(grid == 0) & (neighbors_on == 2)] = 1 # Off -> On
        # (Dying -> Off is handled by the zeros_like)
        
        grid = new_grid
        
        # Update age grid for visual trailing effects
        age_grid[grid == 1] = 1.0 # Max heat
        age_grid *= 0.96 # Decay heat over time
    
    # Rendering
    py5.background(280, 80, 10)
    
    # Instead of drawing every rectangle which is slow, we map age_grid to pixels
    # Since CELL_SIZE is 8, we can use py5.load_np_pixels()
    py5.load_np_pixels()
    
    # Map age to colors:
    # 0 -> Deep Purple (HSV: 280, 80, 10) -> RGB: ~ (15, 5, 25)
    # >0 -> Yellow/Orange (HSV: 40-60, 100, 100)
    # But since np_pixels is RGBA, we can just use a fast linear colormap
    # Or simpler: draw rects but only for age > 0.1 to save time
    
    # Actually for 3840x2160, GRID is 480x270. Drawing 129k rects is fast enough if many are 0.
    py5.no_stroke()
    
    # Get active indices
    active_y, active_x = np.where(age_grid > 0.05)
    
    for i in range(len(active_y)):
        y = active_y[i]
        x = active_x[i]
        age = age_grid[y, x]
        
        # age=1.0 is bright yellow (60)
        # age=0.0 is red/orange (0)
        hue = age * 60
        val = 10 + age * 90
        py5.fill(hue, 100, val, 100)
        py5.rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

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

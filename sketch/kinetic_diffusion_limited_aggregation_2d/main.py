from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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

# DLA Simulation properties
# We'll simulate on a lower resolution grid for performance, then scale up when drawing
GRID_SCALE = 4
GRID_W = SIZE[0] // GRID_SCALE
GRID_H = SIZE[1] // GRID_SCALE

# 0 = empty, > 0 = occupied (stores the generation/time it was attached)
grid = np.zeros((GRID_H, GRID_W), dtype=np.int32)
NUM_WALKERS = 6000
WALKS_PER_FRAME = 300 # How many simulation steps to take per frame

# Walker states
walkers_x = np.random.randint(0, GRID_W, NUM_WALKERS)
walkers_y = np.random.randint(0, GRID_H, NUM_WALKERS)

particles_attached = 0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    
    # Place initial seed in the center
    grid[GRID_H // 2, GRID_W // 2] = 1

def draw():
    global walkers_x, walkers_y, particles_attached, grid
    
    py5.background(0)
    
    # Simulation step
    # We want the fractal to grow steadily over the course of the animation.
    for _ in range(WALKS_PER_FRAME):
        # 1. Random walk
        dx = np.random.randint(-1, 2, NUM_WALKERS)
        dy = np.random.randint(-1, 2, NUM_WALKERS)
        
        walkers_x = np.clip(walkers_x + dx, 0, GRID_W - 1)
        walkers_y = np.clip(walkers_y + dy, 0, GRID_H - 1)
        
        # 2. Check collision with grid
        wx_m1 = np.clip(walkers_x - 1, 0, GRID_W - 1)
        wx_p1 = np.clip(walkers_x + 1, 0, GRID_W - 1)
        wy_m1 = np.clip(walkers_y - 1, 0, GRID_H - 1)
        wy_p1 = np.clip(walkers_y + 1, 0, GRID_H - 1)
        
        # Check if any neighbor in the 3x3 grid around walker is occupied
        attached_mask = (
            (grid[walkers_y, wx_m1] > 0) | (grid[walkers_y, wx_p1] > 0) |
            (grid[wy_m1, walkers_x] > 0) | (grid[wy_p1, walkers_x] > 0) |
            (grid[wy_m1, wx_m1] > 0)     | (grid[wy_m1, wx_p1] > 0) |
            (grid[wy_p1, wx_m1] > 0)     | (grid[wy_p1, wx_p1] > 0)
        )
        
        if np.any(attached_mask):
            attached_indices = np.where(attached_mask)[0]
            for idx in attached_indices:
                x = walkers_x[idx]
                y = walkers_y[idx]
                if grid[y, x] == 0:
                    particles_attached += 1
                    grid[y, x] = particles_attached
                    
            # Respawn attached walkers at random edges to keep them flowing inwards
            num_respawn = len(attached_indices)
            edge_choice = np.random.randint(0, 4, num_respawn)
            
            # 0: top, 1: bottom, 2: left, 3: right
            for i, idx in enumerate(attached_indices):
                if edge_choice[i] == 0:
                    walkers_x[idx] = np.random.randint(0, GRID_W)
                    walkers_y[idx] = 0
                elif edge_choice[i] == 1:
                    walkers_x[idx] = np.random.randint(0, GRID_W)
                    walkers_y[idx] = GRID_H - 1
                elif edge_choice[i] == 2:
                    walkers_x[idx] = 0
                    walkers_y[idx] = np.random.randint(0, GRID_H)
                else:
                    walkers_x[idx] = GRID_W - 1
                    walkers_y[idx] = np.random.randint(0, GRID_H)

    # Drawing
    # We want to draw the fractal up to a certain "time" so it looks like it's growing
    # We'll map the frame count to the number of particles attached
    max_particles_to_draw = int(py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 1, particles_attached + 1))
    
    # We'll extract coordinates of all occupied cells
    y_coords, x_coords = np.nonzero(grid)
    generation = grid[y_coords, x_coords]
    
    # Filter by time to animate growth
    valid_mask = generation <= max_particles_to_draw
    x_valid = x_coords[valid_mask]
    y_valid = y_coords[valid_mask]
    gen_valid = generation[valid_mask]
    
    py5.no_stroke()
    # Use points for faster rendering
    py5.stroke_weight(GRID_SCALE * 1.5)
    
    # Fast rendering logic for large number of points
    for i in range(len(x_valid)):
        x = x_valid[i]
        y = y_valid[i]
        gen = gen_valid[i]
        
        ratio = gen / max(1, float(max_particles_to_draw))
        hue = 240.0 - (ratio * 60.0)
        brightness = 50.0 + (ratio * 50.0)
        
        py5.stroke(hue, 100, brightness, 90)
        py5.point(float(x * GRID_SCALE), float(y * GRID_SCALE))

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Attached: {particles_attached}")

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

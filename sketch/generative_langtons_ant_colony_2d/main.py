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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Use half resolution for grid to give the ants some visual bulk (pixel art style)
W_INT = SIZE[0] // 2
H_INT = SIZE[1] // 2

NUM_ANTS = 5000

# Ant states and rules (Langton's generalized LRRR etc.)
NUM_STATES = 4
# Turns for each state: 1 = Right 90deg, 3 = Left 90deg (which is -1 mod 4)
# Let's use L R R L: [3, 1, 1, 3]
TURNS = np.array([3, 1, 1, 3], dtype=np.int32)
NEXT_STATE = np.array([1, 2, 3, 0], dtype=np.int32)

# DX, DY for directions: 0=UP, 1=RIGHT, 2=DOWN, 3=LEFT
DX = np.array([0, 1, 0, -1], dtype=np.int32)
DY = np.array([-1, 0, 1, 0], dtype=np.int32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, ant_x, ant_y, ant_dir, pixel_array, colors
    grid = np.zeros((H_INT, W_INT), dtype=np.int32)
    
    # Initialize ants randomly in the center
    # They start in a clump to maximize interactions and chaos
    ant_x = np.random.normal(W_INT // 2, 100, NUM_ANTS).astype(np.int32)
    ant_y = np.random.normal(H_INT // 2, 100, NUM_ANTS).astype(np.int32)
    
    # Bound them just in case
    ant_x = np.clip(ant_x, 0, W_INT - 1)
    ant_y = np.clip(ant_y, 0, H_INT - 1)
    
    ant_dir = np.random.randint(0, 4, NUM_ANTS, dtype=np.int32)
    
    # Pre-allocate RGBA buffer
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255
    
    # Color palette for the 4 states:
    # 0 = Black (0, 0, 0)
    # 1 = Deep Purple (50, 0, 100)
    # 2 = Neon Pink (255, 50, 150)
    # 3 = Bright Cyan (50, 255, 255)
    colors = np.array([
        [10, 5, 20],        # Darkest blue/black
        [50, 0, 100],       # Purple
        [255, 50, 150],     # Pink
        [50, 255, 255]      # Cyan
    ], dtype=np.uint8)

def draw():
    global grid, ant_x, ant_y, ant_dir, pixel_array
    
    # Run the simulation for multiple steps per frame to speed up the visual growth
    STEPS_PER_FRAME = 150
    
    for _ in range(STEPS_PER_FRAME):
        # Read the current states at ant positions
        current_states = grid[ant_y, ant_x]
        
        # Turn ants
        ant_dir = (ant_dir + TURNS[current_states]) % 4
        
        # Change state on the grid
        grid[ant_y, ant_x] = NEXT_STATE[current_states]
        
        # Move ants
        ant_x += DX[ant_dir]
        ant_y += DY[ant_dir]
        
        # Wrap around edges (toroidal array)
        ant_x = ant_x % W_INT
        ant_y = ant_y % H_INT

    # Map the grid states to colors using advanced indexing
    pixel_array[:, :, 0:3] = colors[grid]
    
    # Draw the ants themselves as bright white dots
    pixel_array[ant_y, ant_x, 0:3] = [255, 255, 255]
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Draw scaled up to full size (nearest neighbor since py5.no_smooth() is on)
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

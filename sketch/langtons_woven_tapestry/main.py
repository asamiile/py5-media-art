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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

# Langton's Ant Parameters
N_ANTS = 200000
STEPS_PER_FRAME = 150

# Generalized rule: R L R R L R L L R L L (11 states)
# +1 for Right, -1 for Left
rules = np.array([1, -1, 1, 1, -1, 1, -1, -1, 1, -1, -1], dtype=np.int8)
NUM_STATES = len(rules)

# Palette mapping (11 states + 1 background)
# Background: Obsidian #0F0F14
palette = np.zeros((NUM_STATES, 3), dtype=np.uint8)
palette[0] = [15, 15, 20]      # Obsidian
palette[1] = [0, 255, 255]     # Neon Cyan
palette[2] = [255, 215, 0]     # Gold
palette[3] = [220, 20, 60]     # Crimson
palette[4] = [138, 43, 226]    # Royal Purple
palette[5] = [255, 140, 0]     # Dark Orange
palette[6] = [0, 250, 154]     # Medium Spring Green
palette[7] = [255, 20, 147]    # Deep Pink
palette[8] = [30, 144, 255]    # Dodger Blue
palette[9] = [255, 255, 255]   # White
palette[10] = [50, 205, 50]    # Lime Green

grid = np.zeros((H, W), dtype=np.uint8)

# Initialize ants grouped in 5 central clusters
x = np.zeros(N_ANTS, dtype=np.int32)
y = np.zeros(N_ANTS, dtype=np.int32)

cluster_size = N_ANTS // 5
for i in range(5):
    cx = W // 2 + int((W // 4) * np.cos(i * 2 * np.pi / 5))
    cy = H // 2 + int((H // 4) * np.sin(i * 2 * np.pi / 5))
    start_idx = i * cluster_size
    end_idx = start_idx + cluster_size
    
    # Gaussian distribution around clusters
    x[start_idx:end_idx] = np.random.normal(cx, 100, cluster_size).astype(np.int32) % W
    y[start_idx:end_idx] = np.random.normal(cy, 100, cluster_size).astype(np.int32) % H

d = np.random.randint(0, 4, N_ANTS, dtype=np.int8)

# Direction lookup tables
# 0: Up, 1: Right, 2: Down, 3: Left
dx_lut = np.array([0, 1, 0, -1], dtype=np.int32)
dy_lut = np.array([-1, 0, 1, 0], dtype=np.int32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global x, y, d, grid
    
    for _ in range(STEPS_PER_FRAME):
        # Read states
        states = grid[y, x]
        
        # Turn
        turns = rules[states]
        d = (d + turns) % 4
        
        # Update grid
        new_states = (states + 1) % NUM_STATES
        grid[y, x] = new_states
        
        # Move
        x = (x + dx_lut[d]) % W
        y = (y + dy_lut[d]) % H
        
    # Render
    rgb = palette[grid]
    
    alpha = np.full((H, W, 1), 255, dtype=np.uint8)
    argb = np.concatenate((alpha, rgb), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
    py5.update_np_pixels()
    
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

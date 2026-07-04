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

# Cellular Automaton Parameters
NUM_STATES = 16
THRESHOLD = 1 # Number of neighbors needed to advance to next state

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.load_np_pixels()
    actual_height, actual_width = py5.np_pixels.shape[:2]
    
    global grid, cmap
    
    # Initialize low-res random grid and scale it up to create macroscopic structures faster
    scale = 16
    low_res = np.random.randint(0, NUM_STATES, size=(actual_height//scale, actual_width//scale), dtype=np.uint8)
    grid = np.repeat(np.repeat(low_res, scale, axis=0), scale, axis=1)
    
    # Pad to match exact screen dimensions
    pad_h = actual_height - grid.shape[0]
    pad_w = actual_width - grid.shape[1]
    grid = np.pad(grid, ((0, pad_h), (0, pad_w)), mode='edge')
    
    # Precompute color map
    # Let's create a beautiful neon gradient
    cmap = np.zeros((NUM_STATES, 4), dtype=np.uint8)
    for i in range(NUM_STATES):
        # We can use HSB to RGB math
        hue = i / NUM_STATES * 360
        # A simple sine wave mapping to create iridescent waves
        r = int((np.sin(i / NUM_STATES * np.pi * 2) * 0.5 + 0.5) * 255)
        g = int((np.sin(i / NUM_STATES * np.pi * 2 + 2) * 0.5 + 0.5) * 255)
        b = int((np.sin(i / NUM_STATES * np.pi * 2 + 4) * 0.5 + 0.5) * 255)
        
        # py5 np_pixels format is ARGB
        cmap[i] = [255, r, g, b]

def draw():
    global grid
    
    next_target = (grid + 1) % NUM_STATES
    
    # Count neighbors using fast roll operations
    # Using np.int8 to save memory bandwidth
    counts = np.zeros_like(grid, dtype=np.int8)
    
    counts += (np.roll(grid, 1, axis=0) == next_target).astype(np.int8)
    counts += (np.roll(grid, -1, axis=0) == next_target).astype(np.int8)
    counts += (np.roll(grid, 1, axis=1) == next_target).astype(np.int8)
    counts += (np.roll(grid, -1, axis=1) == next_target).astype(np.int8)
    counts += (np.roll(grid, (1, 1), axis=(0, 1)) == next_target).astype(np.int8)
    counts += (np.roll(grid, (1, -1), axis=(0, 1)) == next_target).astype(np.int8)
    counts += (np.roll(grid, (-1, 1), axis=(0, 1)) == next_target).astype(np.int8)
    counts += (np.roll(grid, (-1, -1), axis=(0, 1)) == next_target).astype(np.int8)
    
    # Update grid where threshold is met
    will_change = counts >= THRESHOLD
    grid[will_change] = next_target[will_change]
    
    # Fast rendering using numpy fancy indexing
    py5.load_np_pixels()
    py5.np_pixels[:] = cmap[grid]
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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

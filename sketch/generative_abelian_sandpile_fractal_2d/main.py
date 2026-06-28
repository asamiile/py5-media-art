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

# Use half-resolution to ensure the physics and toppling spread fast enough visually
W_INT = SIZE[0] // 2
H_INT = SIZE[1] // 2

def setup():
    py5.size(*SIZE)
    py5.no_smooth()  # Keep pixel art aesthetics crisp
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, pixel_array, colors
    grid = np.zeros((H_INT, W_INT), dtype=np.int32)
    
    # Pre-allocate RGBA buffer
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255
    
    # Custom color palette for the 4 stable states (0, 1, 2, 3)
    # 0 = Deep Space Blue
    # 1 = Neon Pink
    # 2 = Bright Orange
    # 3 = Electric Cyan
    colors = np.array([
        [10, 5, 25],
        [255, 50, 150],
        [255, 150, 0],
        [0, 255, 255]
    ], dtype=np.uint8)

def draw():
    global grid, pixel_array
    
    # Add a massive amount of sand to the center each frame
    # We want it to grow rapidly to fill the screen within 450 frames
    grid[H_INT // 2, W_INT // 2] += 5000
    
    # Run the toppling vectorized logic multiple times per frame
    # A standard while loop is best for actual physics, but for constant 
    # animation speed, we fix the number of topple steps per frame.
    STEPS = 250
    
    for _ in range(STEPS):
        # Find cells that need to topple
        toppling = (grid >= 4)
        
        # If no cells are toppling, we can break early to save computation
        if not np.any(toppling):
            break
            
        # Subtract 4 from toppling cells
        grid[toppling] -= 4
        
        # Add 1 to all 4 neighbors using np.roll
        # We cast toppling to int32 because boolean arrays sum differently
        toppling_int = toppling.astype(np.int32)
        
        N = np.roll(toppling_int, 1, axis=0)
        S = np.roll(toppling_int, -1, axis=0)
        E = np.roll(toppling_int, 1, axis=1)
        W = np.roll(toppling_int, -1, axis=1)
        
        # To avoid wrapping around the edges (toroidal), we zero out the edges
        N[0, :] = 0
        S[-1, :] = 0
        E[:, 0] = 0
        W[:, -1] = 0
        
        grid += N + S + E + W

    # Render the grid to colors
    # Any cell temporarily >= 4 (unstable) will just be capped at 3 for rendering
    render_grid = np.clip(grid, 0, 3)
    
    pixel_array[:, :, 0:3] = colors[render_grid]
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Draw scaled up to full 4K size with nearest neighbor scaling
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} (Center height: {grid[H_INT // 2, W_INT // 2]})")

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

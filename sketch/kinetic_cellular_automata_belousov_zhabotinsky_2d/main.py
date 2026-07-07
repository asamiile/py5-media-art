from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid resolution (scaled down for performance)
GW = SIZE[0] // 4
GH = SIZE[1] // 4

N_STATES = 24
THRESHOLD = 2

grid = None
cmap_r = None
cmap_g = None
cmap_b = None
img = None

def setup():
    global grid, cmap_r, cmap_g, cmap_b, img
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize grid randomly
    grid = np.random.randint(0, N_STATES, size=(GH, GW), dtype=np.uint8)
    
    # Create colormap
    cmap_r = np.zeros(N_STATES, dtype=np.uint8)
    cmap_g = np.zeros(N_STATES, dtype=np.uint8)
    cmap_b = np.zeros(N_STATES, dtype=np.uint8)
    
    for i in range(N_STATES):
        # Fluorescent biological palette (Deep purple to cyan and yellow)
        t = i / float(N_STATES - 1)
        if t < 0.33:
            # Dark purple to bright purple
            r = py5.lerp(10, 150, t * 3.0)
            g = py5.lerp(0, 0, t * 3.0)
            b = py5.lerp(20, 255, t * 3.0)
        elif t < 0.66:
            # Bright purple to Cyan
            r = py5.lerp(150, 0, (t - 0.33) * 3.0)
            g = py5.lerp(0, 255, (t - 0.33) * 3.0)
            b = py5.lerp(255, 255, (t - 0.33) * 3.0)
        else:
            # Cyan to Electric Yellow
            r = py5.lerp(0, 255, (t - 0.66) * 3.0)
            g = py5.lerp(255, 255, (t - 0.66) * 3.0)
            b = py5.lerp(255, 0, (t - 0.66) * 3.0)
            
        cmap_r[i] = int(py5.constrain(r, 0, 255))
        cmap_g[i] = int(py5.constrain(g, 0, 255))
        cmap_b[i] = int(py5.constrain(b, 0, 255))
        
    # Py5 Image buffer
    img = py5.create_image(GW, GH, py5.RGB)
    
    # To speed up the start of the simulation, we'll "warm up" the grid
    # BZ spirals take a few iterations to form nicely
    for _ in range(50):
        update_grid()

def update_grid():
    global grid
    next_state = (grid + 1) % N_STATES
    
    # Count Moore neighborhood (8 neighbors)
    count = np.zeros_like(grid, dtype=np.uint8)
    
    # Orthogonal
    count += (np.roll(grid, 1, axis=0) == next_state)
    count += (np.roll(grid, -1, axis=0) == next_state)
    count += (np.roll(grid, 1, axis=1) == next_state)
    count += (np.roll(grid, -1, axis=1) == next_state)
    
    # Diagonal
    count += (np.roll(np.roll(grid, 1, axis=0), 1, axis=1) == next_state)
    count += (np.roll(np.roll(grid, 1, axis=0), -1, axis=1) == next_state)
    count += (np.roll(np.roll(grid, -1, axis=0), 1, axis=1) == next_state)
    count += (np.roll(np.roll(grid, -1, axis=0), -1, axis=1) == next_state)
    
    # Update where count >= THRESHOLD
    grid = np.where(count >= THRESHOLD, next_state, grid)
    
    # Introduce tiny amounts of noise (mutations) to keep the system chaotic and prevent it from dying out
    if random.random() < 0.2:
        rx = random.randint(0, GW-1)
        ry = random.randint(0, GH-1)
        grid[ry, rx] = random.randint(0, N_STATES-1)

def draw():
    # Update the CA
    # Run a few steps per frame so the waves move visibly fast
    for _ in range(2):
        update_grid()
        
    # Map to colors
    img.load_np_pixels()
    
    # img.np_pixels is (H, W, 4) in RGBA format
    img.np_pixels[:, :, 0] = cmap_r[grid]
    img.np_pixels[:, :, 1] = cmap_g[grid]
    img.np_pixels[:, :, 2] = cmap_b[grid]
    img.np_pixels[:, :, 3] = 255
    
    img.update_np_pixels()
    
    # Draw scaled up
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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

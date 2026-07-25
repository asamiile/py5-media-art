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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid size for Ising Model (use lower resolution for chunky aesthetic, then upscale)
SCALE = 4
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 15

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid, mask_even, mask_odd, exp_table
    
    # Initialize random spins (-1 or 1)
    grid = np.random.choice([-1, 1], size=(H, W)).astype(np.int8)
    
    # Checkerboard masks for vectorized Metropolis update
    y, x = np.ogrid[0:H, 0:W]
    mask_even = (x + y) % 2 == 0
    mask_odd = ~mask_even

def ising_step(beta):
    global grid
    
    # Pre-calculate possible flip probabilities
    # dE can only be -8, -4, 0, 4, 8
    # Actually dE = 2 * spin * sum(neighbors).
    # sum(neighbors) is in [-4, -2, 0, 2, 4]
    # spin is +/- 1. So spin * sum(neighbors) is in [-4, 4].
    # dE = 2 * [-4, 4] = [-8, 8].
    # We can pre-calculate np.exp(-beta * dE) for the positive dE values (4, 8)
    # Since beta changes every frame, we compute it inside the step.
    
    exp_4 = np.exp(-beta * 4)
    exp_8 = np.exp(-beta * 8)
    
    for mask in [mask_even, mask_odd]:
        # Calculate sum of neighbors (periodic boundaries)
        neighbors = (
            np.roll(grid, 1, axis=0) +
            np.roll(grid, -1, axis=0) +
            np.roll(grid, 1, axis=1) +
            np.roll(grid, -1, axis=1)
        )
        
        # Change in energy if we flip the spin
        dE = 2 * grid * neighbors
        
        # Metropolis acceptance criterion
        # If dE <= 0, we always flip.
        # If dE == 4, flip with probability exp(-beta * 4)
        # If dE == 8, flip with probability exp(-beta * 8)
        
        # Vectorized random choice
        rand = np.random.rand(H, W)
        
        flip = (dE <= 0) | \
               ((dE == 4) & (rand < exp_4)) | \
               ((dE == 8) & (rand < exp_8))
               
        grid[mask & flip] *= -1

def draw():
    global grid
    
    # Oscillate temperature around the critical point T_c = 2.269
    # T goes from 1.5 (ordered domains) to 3.5 (high temperature chaos)
    t = py5.frame_count / TOTAL_FRAMES * py5.TWO_PI
    T = 2.269 + 1.2 * np.sin(t)
    beta = 1.0 / T
    
    for _ in range(STEPS_PER_FRAME):
        ising_step(beta)
        
    py5.load_np_pixels()
    
    # Map spins to colors
    # +1 -> Cyan (0, 255, 255)
    # -1 -> Magenta (255, 0, 255)
    img_data = np.zeros((H, W, 4), dtype=np.uint8)
    img_data[:, :, 0] = 255 # Alpha
    
    # Up spins (+1)
    up = grid == 1
    img_data[up, 1] = 0
    img_data[up, 2] = 255
    img_data[up, 3] = 255
    
    # Down spins (-1)
    down = grid == -1
    img_data[down, 1] = 255
    img_data[down, 2] = 0
    img_data[down, 3] = 255
    
    # Scale up
    if SCALE > 1:
        img_data = np.repeat(np.repeat(img_data, SCALE, axis=0), SCALE, axis=1)
        
    py5.np_pixels[:] = img_data
    py5.update_np_pixels()

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

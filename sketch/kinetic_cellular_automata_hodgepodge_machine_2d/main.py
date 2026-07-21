from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.signal import convolve2d

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

# Hodgepodge Machine simulation parameters
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# Constants for Hodgepodge machine
# 0 = healthy
# N-1 = ill
# 1 to N-2 = infected
N = 100
k1 = 2
k2 = 3
g = 34

# Initialize state with noise
A = np.random.randint(0, N, (ROWS, COLS), dtype=np.int32)

kernel = np.array([
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 1]
], dtype=np.int32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A
    
    # We step the simulation multiple times per frame
    for _ in range(1): # It is very fast moving, so 1 step per frame is better
        # Calculate neighborhood sums
        S = convolve2d(A, kernel, mode='same', boundary='wrap')
        
        # Count infected (0 < state < N-1)
        infected_mask = (A > 0) & (A < N - 1)
        I = convolve2d(infected_mask.astype(np.int32), kernel, mode='same', boundary='wrap')
        
        # Count ill (state == N-1)
        ill_mask = (A == N - 1)
        Q = convolve2d(ill_mask.astype(np.int32), kernel, mode='same', boundary='wrap')
        
        A_next = np.zeros_like(A)
        
        # Healthy cells get infected
        mask_healthy = (A == 0)
        A_next[mask_healthy] = np.floor(I[mask_healthy] / k1) + np.floor(Q[mask_healthy] / k2)
        
        # Infected cells get sicker
        mask_infected = infected_mask
        # to avoid division by zero if I+Q == 0, we can use np.where or add epsilon.
        # usually 9 neighbors means I+Q is at most 9, but if 0, then sum is 0
        sum_neighbors = I[mask_infected] + Q[mask_infected]
        sum_states = S[mask_infected]
        
        # A_next = floor(S / (I+Q+1)) + g
        A_next[mask_infected] = np.floor(sum_states / (sum_neighbors + 1)) + g
        
        # Ill cells become healthy
        mask_ill = ill_mask
        A_next[mask_ill] = 0
        
        # Clip to max N-1
        A = np.clip(A_next, 0, N - 1)
        
    # Render
    py5.load_np_pixels()
    
    # Palette: Neon Synthwave
    # mapped to a sine wave for smooth cycling colors
    
    # Normalized state
    v = A.astype(np.float32) / (N - 1)
    
    r_out = (np.sin(v * 2 * np.pi) * 0.5 + 0.5) * 255
    g_out = (np.sin(v * 2 * np.pi + 2.09) * 0.5 + 0.5) * 200 # Cyan/pink offset
    b_out = (np.sin(v * 2 * np.pi + 4.18) * 0.5 + 0.5) * 255
    
    # Boost contrast/darkness
    # Healthy (v=0) and Ill (v=1) should be dark
    dark_mask = (v == 0) | (v == 1)
    r_out[dark_mask] = 10
    g_out[dark_mask] = 5
    b_out[dark_mask] = 20
    
    r_out = np.clip(r_out, 0, 255).astype(np.uint8)
    g_out = np.clip(g_out, 0, 255).astype(np.uint8)
    b_out = np.clip(b_out, 0, 255).astype(np.uint8)
    
    # Upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # Crop to screen
    r_scaled = r_scaled[:py5.height, :py5.width]
    g_scaled = g_scaled[:py5.height, :py5.width]
    b_scaled = b_scaled[:py5.height, :py5.width]
    
    # In py5, np_pixels is shape (height, width, 4) in ARGB format on Mac
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r_scaled # Red
    py5.np_pixels[:, :, 2] = g_scaled # Green
    py5.np_pixels[:, :, 3] = b_scaled # Blue
    
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

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

# BZ Reaction parameters
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# Three chemical concentrations
A = np.random.rand(ROWS, COLS).astype(np.float32)
B = np.random.rand(ROWS, COLS).astype(np.float32)
C = np.random.rand(ROWS, COLS).astype(np.float32)

alpha = 1.0
beta = 1.0
gamma = 1.0
diffusion_rate = 0.2

# 3x3 Laplacian kernel for diffusion
kernel = np.array([
    [0.05, 0.2, 0.05],
    [0.2, -1.0, 0.2],
    [0.05, 0.2, 0.05]
], dtype=np.float32)

def bz_step():
    global A, B, C
    
    # Calculate diffusion using symmetric padding
    # Using scipy.signal.convolve2d is fast for small 3x3 kernels
    lapA = convolve2d(A, kernel, mode='same', boundary='wrap')
    lapB = convolve2d(B, kernel, mode='same', boundary='wrap')
    lapC = convolve2d(C, kernel, mode='same', boundary='wrap')
    
    # Reaction rules (Continuous BZ model)
    dA = A * (alpha * B - gamma * C) + diffusion_rate * lapA
    dB = B * (beta * C - alpha * A) + diffusion_rate * lapB
    dC = C * (gamma * A - beta * B) + diffusion_rate * lapC
    
    # Update and constrain to [0, 1]
    A = np.clip(A + dA, 0.0, 1.0)
    B = np.clip(B + dB, 0.0, 1.0)
    C = np.clip(C + dC, 0.0, 1.0)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A, B, C
    
    # Step simulation multiple times per frame to speed up visuals
    for _ in range(3):
        bz_step()
        
    py5.load_np_pixels()
    
    # The sum of A+B+C is usually roughly 1, but we can visualize using their components
    # We want a Radioactive Neon palette: Lime green, electric magenta, and deep indigo.
    # We can map A to Red, B to Green, C to Blue (as a base), then color correct.
    
    # Base mapping
    r = A * 255
    g = B * 255
    b = C * 255
    
    # Palette transformation (matrix multiplication for color styling)
    # Magenta-ish from A
    r_out = A * 255 + C * 100
    g_out = B * 255 + C * 50
    b_out = C * 255 + A * 150
    
    r_out = np.clip(r_out, 0, 255).astype(np.uint8)
    g_out = np.clip(g_out, 0, 255).astype(np.uint8)
    b_out = np.clip(b_out, 0, 255).astype(np.uint8)
    
    # Upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # Crop just in case
    r_scaled = r_scaled[:py5.height, :py5.width]
    g_scaled = g_scaled[:py5.height, :py5.width]
    b_scaled = b_scaled[:py5.height, :py5.width]
    
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

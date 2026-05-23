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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Render at reduced resolution for dense NN evaluation
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

# Neural Network Architecture
# We use a simple 2-layer MLP: 2 -> 32 -> 32 -> 3
W1 = np.random.randn(2, 32).astype(np.float32)
b1 = np.random.randn(32).astype(np.float32)

W2 = np.random.randn(32, 32).astype(np.float32)
b2 = np.random.randn(32).astype(np.float32)

W3 = np.random.randn(32, 3).astype(np.float32)
b3 = np.random.randn(3).astype(np.float32)

# Random matrices to smoothly rotate the weights
R1 = np.random.randn(32, 32).astype(np.float32)
R1 = (R1 - R1.T) * 0.05  # Skew-symmetric for rotation
R2 = np.random.randn(32, 32).astype(np.float32)
R2 = (R2 - R2.T) * 0.05

# Input grid (X, Y plane)
x_range = np.linspace(-3.0, 3.0, SIM_W, dtype=np.float32)
y_range = np.linspace(-3.0, 3.0, SIM_H, dtype=np.float32)
xv, yv = np.meshgrid(x_range, y_range)

# Flatten for batch processing
X_in = np.stack([xv.flatten(), yv.flatten()], axis=-1)

def relu(x):
    return np.maximum(0, x)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global W1, W2, W3
    
    # Smoothly rotate the hidden weights over time
    # This simulates walking through the high-dimensional latent space
    # W_new = W + dW
    W1 += np.dot(W1, R1) * 0.01
    W2 += np.dot(W2, R2) * 0.01
    
    # Forward pass on the entire screen grid
    Z1 = np.dot(X_in, W1) + b1
    A1 = relu(Z1)
    
    Z2 = np.dot(A1, W2) + b2
    A2 = relu(Z2)
    
    Z3 = np.dot(A2, W3) + b3
    
    # Apply a smooth periodic activation at the end for bands
    out = np.sin(Z3 * 0.5)
    
    # Map to colors
    # out is roughly [-1, 1]
    # We map to HSL conceptually, but directly output RGB
    r = ((out[:, 0] + 1) * 127).astype(np.uint8).reshape((SIM_H, SIM_W))
    g = ((out[:, 1] + 1) * 127).astype(np.uint8).reshape((SIM_H, SIM_W))
    b = ((out[:, 2] + 1) * 127).astype(np.uint8).reshape((SIM_H, SIM_W))
    
    # Upscale 2x
    r_up = np.kron(r, np.ones((2, 2), dtype=np.uint8))
    g_up = np.kron(g, np.ones((2, 2), dtype=np.uint8))
    b_up = np.kron(b, np.ones((2, 2), dtype=np.uint8))
    
    r_up = r_up[:SIZE[1], :SIZE[0]]
    g_up = g_up[:SIZE[1], :SIZE[0]]
    b_up = b_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = r_up
    pixels[:, :, 2] = g_up
    pixels[:, :, 3] = b_up
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

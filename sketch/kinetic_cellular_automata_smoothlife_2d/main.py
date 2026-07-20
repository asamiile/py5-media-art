from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.signal import fftconvolve

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

# SmoothLife parameters
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# radii for inner (m) and outer (n) neighborhoods
Ra = 21.0
Ri = Ra / 3.0

b1 = 0.278
b2 = 0.365
d1 = 0.267
d2 = 0.445
alpha_n = 0.028
alpha_m = 0.147
dt = 0.1

def sigmoid(x, a, alpha):
    # Avoid overflow in exp by clipping
    arg = np.clip(-(x - a) * 4 / alpha, -100, 100)
    return 1.0 / (1.0 + np.exp(arg))

def sigmoid_interval(x, a, b, alpha):
    return sigmoid(x, a, alpha) * (1.0 - sigmoid(x, b, alpha))

def transition_function(n, m):
    # s is the transition
    return sigmoid_interval(n, np.interp(m, [0, 1], [b1, d1]), np.interp(m, [0, 1], [b2, d2]), alpha_n)

# generate kernels
y, x = np.ogrid[-int(Ra):int(Ra)+1, -int(Ra):int(Ra)+1]
r = np.sqrt(x**2 + y**2)

# Anti-aliased kernels for smooth space
K_m = 1.0 - sigmoid(r, Ri, 0.5)
K_n = sigmoid(r, Ri, 0.5) * (1.0 - sigmoid(r, Ra, 0.5))

# Normalize kernels
K_m /= np.sum(K_m)
K_n /= np.sum(K_n)

# Initialize grid with noise in a circle
A = np.zeros((ROWS, COLS), dtype=np.float32)
y_idx, x_idx = np.ogrid[:ROWS, :COLS]
mask = (x_idx - COLS//2)**2 + (y_idx - ROWS//2)**2 < (min(COLS, ROWS)*0.3)**2
A[mask] = np.random.rand(np.sum(mask)).astype(np.float32)

def smoothlife_step():
    global A
    # Wrap padding for FFT convolve
    pad_r = int(Ra)
    A_pad = np.pad(A, pad_width=pad_r, mode='wrap')
    
    # Calculate m and n (inner and outer neighborhood averages)
    m = fftconvolve(A_pad, K_m, mode='valid')
    n = fftconvolve(A_pad, K_n, mode='valid')
    
    # S transition
    q = transition_function(n, m)
    
    # Update rule
    # In pure continuous time: A = A + dt * (q - A)
    # But usually it's written as 2*q-1 or A + dt*(2q - 1 - something)
    # the classic smoothlife uses: A(t+1) = A(t) + dt*(2 * q - 1) clipped to 0, 1
    
    # Actually, a simpler continuous update is standard:
    A = np.clip(A + dt * (2.0 * q - 1.0), 0, 1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A
    
    for _ in range(4):
        smoothlife_step()
        
    py5.load_np_pixels()
    
    # Palette: Micro-organic alien bioluminescence
    # Deep abyssal indigo background (low A)
    # Soft glowing mint green amoebas (high A)
    
    v = A
    
    r_out = v**2 * 100 + (1-v) * 10
    g_out = v * 255 + (1-v) * 10
    b_out = v**0.5 * 200 + (1-v) * 40
    
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

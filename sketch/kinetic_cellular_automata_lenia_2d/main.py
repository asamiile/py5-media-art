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

# Lenia simulation parameters
# Using 4x scale to keep it very fast and get macro structures
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# Lenia params (Orbium / Glider like)
R = 15 # kernel radius
T = 10 # time step denominator (dt = 1/T)
mu = 0.15 # growth center
sigma = 0.017 # growth width
beta = np.array([1]) # single ring

# Initialize state with noise in the center
A = np.zeros((ROWS, COLS), dtype=np.float32)
cx, cy = COLS // 2, ROWS // 2
s = 40
A[cy-s:cy+s, cx-s:cx+s] = np.random.rand(2*s, 2*s).astype(np.float32)

# Build the kernel K
y, x = np.ogrid[-R:R+1, -R:R+1]
r = np.sqrt(x**2 + y**2) / R
# core of Lenia: kernel is a bell shape
# avoid division by zero or invalid sqrt
with np.errstate(divide='ignore', invalid='ignore'):
    K = np.exp(4 - 4 / (1 - (r - 0.5)**2)) * (r < 1)
K[np.isnan(K)] = 0
K = K / np.sum(K) # normalize

def lenia_step():
    global A
    # Pad A for wrapping
    A_pad = np.pad(A, pad_width=R, mode='wrap')
    # Convolve
    U = fftconvolve(A_pad, K, mode='valid')
    # Ensure U is same shape as A. 
    # valid mode on (H+2R, W+2R) with (2R+1, 2R+1) gives (H, W).
    
    # Growth function: bell-shaped around mu
    G = 2 * np.exp(-((U - mu)**2) / (2 * sigma**2)) - 1
    
    # Update state
    A = np.clip(A + (1.0 / T) * G, 0, 1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A
    
    # Step simulation
    for _ in range(4):
        lenia_step()
    
    # Render
    py5.load_np_pixels()
    
    # Palette: Vibrant lime green, bright yellow on dark forest green background
    # A=0: Forest green (10, 30, 10)
    # A=0.5: Lime green (150, 255, 50)
    # A=1: Bright yellow (255, 255, 100)
    
    r_out = A**2 * 255 + A * (1-A) * 300 + (1-A) * 10
    g_out = A**2 * 255 + A * (1-A) * 510 + (1-A) * 30
    b_out = A**2 * 100 + A * (1-A) * 100 + (1-A) * 10
    
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

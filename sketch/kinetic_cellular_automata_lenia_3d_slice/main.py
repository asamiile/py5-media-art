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

# 3D Lenia parameters
GRID_SCALE = 32
COLS = int(np.ceil(SIZE[0] / GRID_SCALE))
ROWS = int(np.ceil(SIZE[1] / GRID_SCALE))
DEPTH = 32 # Z-axis depth

R = 5.0 # radius
mu = 0.15 # growth center
sigma = 0.017 # growth width
dt = 0.1 # time step

# Generate 3D spherical kernel
z, y, x = np.ogrid[-int(R):int(R)+1, -int(R):int(R)+1, -int(R):int(R)+1]
r = np.sqrt(x**2 + y**2 + z**2) / R
# Bell-shaped kernel K(r) = exp( 4 - 4 / (1 - r^2) ) if r < 1 else 0
K = np.zeros_like(r)
mask = r < 1.0
K[mask] = np.exp(4.0 - 4.0 / (1.0 - r[mask]**2))
K /= np.sum(K)

# Initialize grid with noise in a central sphere
A = np.zeros((DEPTH, ROWS, COLS), dtype=np.float32)
z_idx, y_idx, x_idx = np.ogrid[:DEPTH, :ROWS, :COLS]
mask_init = (x_idx - COLS//2)**2 + (y_idx - ROWS//2)**2 + (z_idx - DEPTH//2)**2 < (min(COLS, ROWS, DEPTH)*0.3)**2
A[mask_init] = np.random.rand(np.sum(mask_init)).astype(np.float32)

def growth_function(U):
    # G(U) = 2 * exp( - (U - mu)^2 / (2 * sigma^2) ) - 1
    return 2.0 * np.exp(-((U - mu)**2) / (2.0 * sigma**2)) - 1.0

def lenia_step():
    global A
    # Wrap padding for FFT convolve
    pad_r = int(R)
    A_pad = np.pad(A, pad_width=pad_r, mode='wrap')
    
    # Calculate potential U
    U = fftconvolve(A_pad, K, mode='valid')
    
    # Calculate growth G
    G = growth_function(U)
    
    # Update state
    A = np.clip(A + dt * G, 0, 1)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A
    
    # Step simulation
    lenia_step()
        
    py5.load_np_pixels()
    
    # Render a 2D slice
    # Z pans up and down like a sonar scan
    z_slice = int((np.sin(py5.frame_count * 0.05) * 0.5 + 0.5) * (DEPTH - 1))
    
    slice_2d = A[z_slice, :, :]
    
    # Palette: Deep Ocean Scan (Sonar-like aesthetics)
    # Dark teal background (low A)
    # Glowing bright cyan and seafoam green structures (high A)
    
    v = slice_2d
    
    # R: 0 -> 0
    # G: 20 -> 255
    # B: 40 -> 200
    r_out = v * 0 + (1-v) * 0
    g_out = v * 255 + (1-v) * 20
    b_out = v * 200 + (1-v) * 40
    
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

    # Draw scanning line indicator
    py5.stroke(160, 80, 100, 50) # Cyan line
    py5.stroke_weight(4)
    # Map z_slice to y-coordinate (just a visual HUD)
    hud_y = py5.height - 100 + (z_slice / DEPTH) * 80
    py5.line(50, hud_y, 150, hud_y)
    py5.no_stroke()
    py5.fill(160, 80, 100, 30)
    py5.rect(50, py5.height - 100, 100, 80)

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

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

# Reaction-Diffusion parameters
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# Two chemical concentrations: U (prey) and V (predator)
U = np.ones((ROWS, COLS), dtype=np.float32)
V = np.zeros((ROWS, COLS), dtype=np.float32)

# Seed a few small squares of V to start the reaction
num_seeds = 100
for _ in range(num_seeds):
    cx = random.randint(10, COLS-10)
    cy = random.randint(10, ROWS-10)
    V[cy-5:cy+5, cx-5:cx+5] = 1.0

# Gray-Scott Model parameters for "Coral" / "Maze" patterns
Ru = 1.0     # Diffusion rate of U
Rv = 0.5     # Diffusion rate of V
F = 0.0545   # Feed rate
k = 0.0620   # Kill rate
dt = 1.0     # Time step

# 3x3 Laplacian kernel for diffusion
kernel = np.array([
    [0.05, 0.2, 0.05],
    [0.2, -1.0, 0.2],
    [0.05, 0.2, 0.05]
], dtype=np.float32)

def rd_step():
    global U, V
    
    lapU = convolve2d(U, kernel, mode='same', boundary='wrap')
    lapV = convolve2d(V, kernel, mode='same', boundary='wrap')
    
    uvv = U * V * V
    
    dU = Ru * lapU - uvv + F * (1.0 - U)
    dV = Rv * lapV + uvv - (F + k) * V
    
    U = np.clip(U + dU * dt, 0.0, 1.0)
    V = np.clip(V + dV * dt, 0.0, 1.0)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global U, V
    
    # Step simulation multiple times per frame for speed
    for _ in range(12):
        rd_step()
        
    py5.load_np_pixels()
    
    # Bio-luminescent Deep Sea palette
    # Dark indigo background (High U, Low V)
    # Glowing aquamarine and golden coral patterns (Low U, High V)
    
    # V is the pattern we care about mostly (it's the coral/stripes)
    v_norm = V / (np.max(V) + 1e-8)
    
    # Map to colors
    # Background: Indigo (R: 20, G: 0, B: 60)
    # Pattern Edge: Aquamarine (R: 0, G: 255, B: 200)
    # Pattern Core: Gold (R: 255, G: 200, B: 0)
    
    r_out = (1 - v_norm) * 20 + (v_norm < 0.5) * v_norm * 2 * 0 + (v_norm >= 0.5) * (v_norm * 255)
    g_out = (1 - v_norm) * 0 + (v_norm < 0.5) * v_norm * 2 * 255 + (v_norm >= 0.5) * (v_norm * 200)
    b_out = (1 - v_norm) * 60 + (v_norm < 0.5) * v_norm * 2 * 200 + (v_norm >= 0.5) * (v_norm * 0)
    
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

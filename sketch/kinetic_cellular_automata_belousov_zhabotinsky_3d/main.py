from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.ndimage import convolve

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

# BZ Reaction parameters (3D)
GRID_SCALE = 8 # Larger scale because 3D is heavy
COLS = int(np.ceil(SIZE[0] / GRID_SCALE))
ROWS = int(np.ceil(SIZE[1] / GRID_SCALE))
DEPTH = 40 # Z-axis depth

# Three chemical concentrations
A = np.random.rand(DEPTH, ROWS, COLS).astype(np.float32)
B = np.random.rand(DEPTH, ROWS, COLS).astype(np.float32)
C = np.random.rand(DEPTH, ROWS, COLS).astype(np.float32)

alpha = 1.0
beta = 1.0
gamma = 1.0
diffusion_rate = 0.2

# 3D Laplacian kernel (3x3x3)
kernel = np.zeros((3, 3, 3), dtype=np.float32)
kernel[1, 1, 1] = -1.0
# 6 nearest neighbors (faces)
kernel[0, 1, 1] = 0.1
kernel[2, 1, 1] = 0.1
kernel[1, 0, 1] = 0.1
kernel[1, 2, 1] = 0.1
kernel[1, 1, 0] = 0.1
kernel[1, 1, 2] = 0.1
# 12 edge neighbors
for i, j, k in [(0,0,1), (0,2,1), (2,0,1), (2,2,1), (0,1,0), (0,1,2), (2,1,0), (2,1,2), (1,0,0), (1,0,2), (1,2,0), (1,2,2)]:
    kernel[i, j, k] = 0.025
# 8 corner neighbors
for i in [0, 2]:
    for j in [0, 2]:
        for k in [0, 2]:
            kernel[i, j, k] = 0.0125

def bz_step():
    global A, B, C
    
    # Calculate diffusion using symmetric padding
    lapA = convolve(A, kernel, mode='wrap')
    lapB = convolve(B, kernel, mode='wrap')
    lapC = convolve(C, kernel, mode='wrap')
    
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
    for _ in range(2):
        bz_step()
        
    py5.load_np_pixels()
    
    # Render a 2D slice
    # Z pans up and down like a sonar scan
    z_slice = int((np.sin(py5.frame_count * 0.05) * 0.5 + 0.5) * (DEPTH - 1))
    
    slice_A = A[z_slice, :, :]
    slice_B = B[z_slice, :, :]
    slice_C = C[z_slice, :, :]
    
    # Toxic Bio-luminescence palette: Chartreuse/yellow-green and acid-blue
    # A mapped to green, B to blue, C to red
    
    r = slice_C * 200 + slice_A * 50
    g = slice_A * 255 + slice_B * 100
    b = slice_B * 255 + slice_C * 150
    
    r_out = np.clip(r, 0, 255).astype(np.uint8)
    g_out = np.clip(g, 0, 255).astype(np.uint8)
    b_out = np.clip(b, 0, 255).astype(np.uint8)
    
    # Upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # Crop to screen
    r_scaled = r_scaled[:py5.height, :py5.width]
    g_scaled = g_scaled[:py5.height, :py5.width]
    b_scaled = b_scaled[:py5.height, :py5.width]
    
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r_scaled # Red
    py5.np_pixels[:, :, 2] = g_scaled # Green
    py5.np_pixels[:, :, 3] = b_scaled # Blue
    
    py5.update_np_pixels()
    
    # Draw scanning line indicator
    py5.stroke(100, 80, 100, 50) # Green line
    py5.stroke_weight(4)
    hud_y = py5.height - 100 + (z_slice / DEPTH) * 80
    py5.line(50, hud_y, 150, hud_y)
    py5.no_stroke()
    py5.fill(100, 80, 100, 30)
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

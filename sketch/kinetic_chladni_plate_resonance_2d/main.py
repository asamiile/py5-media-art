from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation state
N = 250000
# Initial points
x = np.random.uniform(0, 1, N).astype(np.float32)
y = np.random.uniform(0, 1, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def chladni_grad(x, y, m, n):
    # The Chladni equation for a square plate is roughly:
    # Z = a * sin(m * pi * x) * sin(n * pi * y) + b * sin(n * pi * x) * sin(m * pi * y)
    # We want particles to move TOWARDS the nodal lines (where Z = 0 or Z^2 is minimum)
    # So we take the gradient of Z^2, which is 2 * Z * grad(Z), and move in the negative direction.
    
    pi = np.pi
    
    sin_mx = np.sin(m * pi * x)
    sin_ny = np.sin(n * pi * y)
    sin_nx = np.sin(n * pi * x)
    sin_my = np.sin(m * pi * y)
    
    cos_mx = np.cos(m * pi * x)
    cos_ny = np.cos(n * pi * y)
    cos_nx = np.cos(n * pi * x)
    cos_my = np.cos(m * pi * y)
    
    Z = sin_mx * sin_ny - sin_nx * sin_my  # using a=1, b=-1 is common
    
    dZ_dx = m * pi * cos_mx * sin_ny - n * pi * cos_nx * sin_my
    dZ_dy = n * pi * sin_mx * cos_ny - m * pi * sin_nx * cos_my
    
    # Gradient of Z^2
    grad_x = 2 * Z * dZ_dx
    grad_y = 2 * Z * dZ_dy
    
    return grad_x, grad_y

def step_chladni(m, n):
    global x, y
    grad_x, grad_y = chladni_grad(x, y, m, n)
    
    # Move particles towards nodes (negative gradient of Z^2) with some noise
    # The force scales with distance, but we clamp it to prevent explosions
    force_x = -grad_x * 0.005
    force_y = -grad_y * 0.005
    
    # Add brownian noise to keep them active
    noise_x = np.random.normal(0, 0.001, N)
    noise_y = np.random.normal(0, 0.001, N)
    
    x_new = x + force_x + noise_x
    y_new = y + force_y + noise_y
    
    # Bounce off walls
    mask_x0 = x_new < 0
    mask_x1 = x_new > 1
    x_new[mask_x0] *= -1
    x_new[mask_x1] = 2.0 - x_new[mask_x1]
    
    mask_y0 = y_new < 0
    mask_y1 = y_new > 1
    y_new[mask_y0] *= -1
    y_new[mask_y1] = 2.0 - y_new[mask_y1]
    
    x[:] = x_new
    y[:] = y_new

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Modulate mode parameters m and n continuously
    # Transitioning from m=3, n=5 to m=7, n=4
    m = 5.0 + 2.0 * np.sin(t)
    n = 4.5 + 1.5 * np.cos(t * 2)
    
    # Run steps to settle onto nodes
    for _ in range(5):
        step_chladni(m, n)
        
    # Map to screen
    screen_x = x * SIZE[0]
    screen_y = y * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.7 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Shimmering gold sand over a deep velvet crimson plate
    # Plate: Crimson [50, 0, 10]
    # Sand: Gold [255, 200, 50]
    density_norm = np.clip(density_buffer / 8.0, 0, 1)
    
    r = 50 + 205 * density_norm
    g = 0 + 200 * density_norm
    b = 10 + 40 * density_norm
    
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b.astype(np.uint8)
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

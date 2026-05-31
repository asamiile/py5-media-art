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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

NUM_PARTICLES = 500000
particles = None
velocities = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 10, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, velocities
    # Initialize random positions
    particles = np.random.rand(NUM_PARTICLES, 2)
    particles[:, 0] *= W
    particles[:, 1] *= H
    
    velocities = np.zeros((NUM_PARTICLES, 2))

def calculate_chladni_gradients(p, n, m):
    # Map points to -1 to 1 space
    x = (p[:, 0] / W) * 2.0 - 1.0
    y = (p[:, 1] / H) * 2.0 - 1.0
    
    pi = np.pi
    
    # Partial derivative of Chladni equation w.r.t x
    # Z = cos(n*pi*x)*cos(m*pi*y) - cos(m*pi*x)*cos(n*pi*y)
    # dZ/dx = -n*pi*sin(n*pi*x)*cos(m*pi*y) + m*pi*sin(m*pi*x)*cos(n*pi*y)
    dz_dx = -n * pi * np.sin(n * pi * x) * np.cos(m * pi * y) + \
             m * pi * np.sin(m * pi * x) * np.cos(n * pi * y)
             
    # Partial derivative of Chladni equation w.r.t y
    # dZ/dy = -m*pi*cos(n*pi*x)*sin(m*pi*y) + n*pi*cos(m*pi*x)*sin(n*pi*y)
    dz_dy = -m * pi * np.cos(n * pi * x) * np.sin(m * pi * y) + \
             n * pi * np.cos(m * pi * x) * np.sin(n * pi * y)
             
    # Value itself (used for determining distance from nodal lines)
    Z = np.cos(n * pi * x) * np.cos(m * pi * y) - np.cos(m * pi * x) * np.cos(n * pi * y)
    
    # The gradient vector of abs(Z). We want particles to move towards Z=0 (nodal lines).
    # So we move in the opposite direction of the gradient of Z^2.
    # d(Z^2)/dx = 2*Z * dZ/dx
    grad_x = -Z * dz_dx
    grad_y = -Z * dz_dy
    
    return np.column_stack((grad_x, grad_y)), Z

def draw():
    # Fade background slightly for motion blur
    py5.fill(10, 10, 15, 30)
    py5.no_stroke()
    py5.rect(0, 0, W, H)
    
    global particles, velocities
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Smoothly transition n and m parameters to morph the standing waves
    # n goes from 2 to 7, m goes from 3 to 11
    n = 2.0 + 5.0 * (1.0 - np.cos(t * np.pi * 2)) / 2.0
    m = 3.0 + 8.0 * (1.0 - np.cos(t * np.pi * 4)) / 2.0
    
    # Get gradients
    grads, Z_vals = calculate_chladni_gradients(particles, n, m)
    
    # Update velocities based on gradients
    velocities += grads * 5.0
    
    # Add random jitter (Brownian motion) based on vibration amplitude (Z value)
    # At nodes (Z=0), vibration is 0.
    vibration = np.abs(Z_vals)
    jitter = np.random.randn(NUM_PARTICLES, 2) * vibration[:, np.newaxis] * 8.0
    
    # Friction
    velocities *= 0.8
    
    # Update positions
    particles += velocities + jitter
    
    # Wrap around edges
    particles[:, 0] %= W
    particles[:, 1] %= H
    
    # Draw points using numpy pixels for extreme speed
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Fast drawing: convert to integer coordinates
    coords = particles.astype(np.int32)
    
    # Valid mask
    valid = (coords[:, 0] >= 0) & (coords[:, 0] < W) & (coords[:, 1] >= 0) & (coords[:, 1] < H)
    valid_coords = coords[valid]
    
    # Golden sand color
    R, G, B = 255, 200, 100
    
    # Draw directly into pixel array
    pixels[valid_coords[:, 1], valid_coords[:, 0]] = [255, R, G, B]
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

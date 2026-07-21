from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import sobel

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

# Lenia parameters (2D)
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

R = 13.0
mu = 0.15
sigma = 0.017
dt = 0.1

# Generate 2D ring kernel
y, x = np.ogrid[-int(R):int(R)+1, -int(R):int(R)+1]
r = np.sqrt(x**2 + y**2) / R
K = np.zeros_like(r)
mask = r < 1.0
K[mask] = np.exp(4.0 - 4.0 / (1.0 - r[mask]**2))
K /= np.sum(K)

# Initialize grid with noise in a circle
A = np.zeros((ROWS, COLS), dtype=np.float32)
y_idx, x_idx = np.ogrid[:ROWS, :COLS]
mask_init = (x_idx - COLS//2)**2 + (y_idx - ROWS//2)**2 < (min(COLS, ROWS)*0.3)**2
A[mask_init] = np.random.rand(np.sum(mask_init)).astype(np.float32)

def growth_function(U):
    return 2.0 * np.exp(-((U - mu)**2) / (2.0 * sigma**2)) - 1.0

def lenia_step():
    global A
    pad_r = int(R)
    A_pad = np.pad(A, pad_width=pad_r, mode='wrap')
    U = fftconvolve(A_pad, K, mode='valid')
    G = growth_function(U)
    A = np.clip(A + dt * G, 0, 1)

# Flow field particles
NUM_PARTICLES = 30000
particles = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
particles[:, 0] *= py5.width
particles[:, 1] *= py5.height
velocities = np.zeros_like(particles)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(270, 90, 10) # Dark violet

def draw():
    global A, particles, velocities
    
    # 1. Step Lenia twice for speed
    for _ in range(2):
        lenia_step()
        
    # 2. Compute gradients of A to get a vector field
    # We use Sobel filters to find the derivative in x and y
    dx = sobel(A, axis=1) / 8.0
    dy = sobel(A, axis=0) / 8.0
    
    # The gradient points towards higher concentration.
    # To make a flow field, we can rotate the gradient by 90 degrees to make particles orbit the creatures!
    # Vector (dx, dy) rotated 90 deg -> (-dy, dx)
    flow_u = -dy
    flow_v = dx
    
    # Also add a slight attractive force towards higher concentrations
    flow_u += dx * 0.5
    flow_v += dy * 0.5
    
    # 3. Fade background for trails
    py5.no_stroke()
    py5.fill(270, 90, 10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    # 4. Update and draw particles
    # Map particle positions to grid indices
    px = np.clip((particles[:, 0] / GRID_SCALE).astype(np.int32), 0, COLS - 1)
    py = np.clip((particles[:, 1] / GRID_SCALE).astype(np.int32), 0, ROWS - 1)
    
    # Get flow forces at particle positions
    force_x = flow_u[py, px]
    force_y = flow_v[py, px]
    
    # Add noise to prevent them from getting stuck
    force_x += (np.random.rand(NUM_PARTICLES) - 0.5) * 0.05
    force_y += (np.random.rand(NUM_PARTICLES) - 0.5) * 0.05
    
    # Update velocities
    velocities[:, 0] = velocities[:, 0] * 0.95 + force_x * 40.0
    velocities[:, 1] = velocities[:, 1] * 0.95 + force_y * 40.0
    
    # Max speed limit
    speeds = np.linalg.norm(velocities, axis=1, keepdims=True)
    max_speed = 6.0
    velocities = np.where(speeds > max_speed, (velocities / (speeds + 1e-8)) * max_speed, velocities)
    
    # Update positions
    particles += velocities
    
    # Wrap around screen
    particles[:, 0] %= py5.width
    particles[:, 1] %= py5.height
    
    # Render particles directly
    # To render 30k particles fast, we can use points or lines
    # We use Py5 shape API
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_PARTICLES):
        # Color based on speed
        spd = speeds[i, 0]
        # Pink for slow, Cyan for fast
        hue = 320 if spd < 2.0 else 180
        
        py5.stroke(hue, 90, 100, 80)
        
        x, y = particles[i]
        vx, vy = velocities[i]
        
        py5.vertex(x, y)
        py5.vertex(x - vx*2, y - vy*2) # Trail behind
        
    py5.end_shape()

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

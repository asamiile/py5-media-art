from pathlib import Path
import shutil
import subprocess
import sys
import math
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 100_000

# Global numpy arrays for particle positions and velocities
px = None
py = None
vx = None
vy = None

def setup():
    global px, py, vx, vy
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 5, 16)
    
    # Initialize particles randomly across the screen
    px = np.random.uniform(0, py5.width, NUM_PARTICLES)
    py = np.random.uniform(0, py5.height, NUM_PARTICLES)
    vx = np.zeros(NUM_PARTICLES)
    vy = np.zeros(NUM_PARTICLES)
    
def get_chladni_gradients(x, y, n, m):
    # Normalized coordinates from -1 to 1
    nx = (x / py5.width) * 2 - 1
    ny = (y / py5.height) * 2 - 1
    
    # The Chladni equation
    # C(x,y) = cos(n*pi*x)*cos(m*pi*y) - cos(m*pi*x)*cos(n*pi*y)
    
    # We want gradients to push particles towards C(x,y) = 0
    # The gradient of C^2 is 2*C * gradient(C)
    
    pi_nx = np.pi * nx
    pi_ny = np.pi * ny
    
    cos_n_nx = np.cos(n * pi_nx)
    cos_m_ny = np.cos(m * pi_ny)
    cos_m_nx = np.cos(m * pi_nx)
    cos_n_ny = np.cos(n * pi_ny)
    
    sin_n_nx = np.sin(n * pi_nx)
    sin_m_ny = np.sin(m * pi_ny)
    sin_m_nx = np.sin(m * pi_nx)
    sin_n_ny = np.sin(n * pi_ny)
    
    C = cos_n_nx * cos_m_ny - cos_m_nx * cos_n_ny
    
    # Partial derivatives
    dC_dnx = -n * np.pi * sin_n_nx * cos_m_ny + m * np.pi * sin_m_nx * cos_n_ny
    dC_dny = -m * np.pi * cos_n_nx * sin_m_ny + n * np.pi * cos_m_nx * sin_n_ny
    
    # Gradient of C^2
    grad_x = 2 * C * dC_dnx
    grad_y = 2 * C * dC_dny
    
    return grad_x, grad_y

def draw():
    global px, py, vx, vy
    
    # Motion blur / fading
    py5.fill(5, 5, 16, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Smoothly interpolate between (n, m) pairs
    # Pair 1: (3, 5) -> Pair 2: (4, 7) -> Pair 3: (5, 9)
    # We'll use continuous functions for n and m
    n = 3.5 + 2.0 * math.sin(t * math.pi * 2)
    m = 5.5 + 3.0 * math.cos(t * math.pi * 2)
    
    grad_x, grad_y = get_chladni_gradients(px, py, n, m)
    
    # Force towards nodes (negative gradient of C^2)
    # Plus some random noise/vibration
    force_magnitude = 15.0
    vibration = 2.0
    
    # Update velocities
    vx -= grad_x * force_magnitude
    vy -= grad_y * force_magnitude
    
    # Damping
    vx *= 0.8
    vy *= 0.8
    
    # Add vibration (Brownian motion)
    vx += np.random.normal(0, vibration, NUM_PARTICLES)
    vy += np.random.normal(0, vibration, NUM_PARTICLES)
    
    # Update positions
    px += vx
    py += vy
    
    # Boundary wrap
    px = np.mod(px, py5.width)
    py = np.mod(py, py5.height)
    
    # Draw particles using points
    # We use multiple pass for glowing
    py5.stroke(230, 194, 128, 150) # Golden Sand
    py5.stroke_weight(2)
    py5.points(np.column_stack((px, py)))
    
    py5.stroke(255, 255, 255, 200) # White core
    py5.stroke_weight(1)
    py5.points(np.column_stack((px, py)))
    
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

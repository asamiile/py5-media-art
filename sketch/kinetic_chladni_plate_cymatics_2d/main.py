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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_PARTICLES = 300000

# State
points = np.random.uniform(-1, 1, (NUM_PARTICLES, 2))
velocities = np.zeros((NUM_PARTICLES, 2))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global points, velocities
    # Motion blur using semi-transparent background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 30) # Very dark grey/blue
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # We interpolate between different Chladni modes (m, n)
    # This simulates a plate changing resonant frequencies
    m = 3.0 + 2.0 * np.sin(t * 0.5)
    n = 5.0 + 3.0 * np.cos(t * 0.3)
    a = 1.0
    b = 1.0 * np.sin(t * 0.7)
    
    x = points[:, 0]
    y = points[:, 1]
    
    # The amplitude of the Chladni standing wave is:
    # Z = a * sin(n*pi*x)*sin(m*pi*y) + b * sin(m*pi*x)*sin(n*pi*y)
    # Particles (sand) collect at the nodal lines where Z = 0
    # So we want particles to move towards lower Z^2.
    # We can compute the gradient of Z^2 and move particles in the negative gradient direction.
    # Gradient of Z^2 is 2 * Z * grad(Z)
    
    px = np.pi * x
    py_ = np.pi * y
    
    # Compute Z
    term1 = a * np.sin(n * px) * np.sin(m * py_)
    term2 = b * np.sin(m * px) * np.sin(n * py_)
    Z = term1 + term2
    
    # Compute grad(Z)
    dZdx = a * n * np.pi * np.cos(n * px) * np.sin(m * py_) + b * m * np.pi * np.cos(m * px) * np.sin(n * py_)
    dZdy = a * m * np.pi * np.sin(n * px) * np.cos(m * py_) + b * n * np.pi * np.sin(m * px) * np.cos(n * py_)
    
    # Force towards Z=0 is proportional to - Z * grad(Z)
    force_x = -Z * dZdx
    force_y = -Z * dZdy
    
    # Update velocities and positions
    # We add some random jitter to simulate the bouncing of the sand
    jitter = np.random.normal(0, 0.002, (NUM_PARTICLES, 2))
    
    velocities[:, 0] += force_x * 0.005 + jitter[:, 0]
    velocities[:, 1] += force_y * 0.005 + jitter[:, 1]
    
    # Friction
    velocities *= 0.85
    
    points += velocities
    
    # Wrap particles that fly off the plate
    mask_out = (points[:, 0] < -1) | (points[:, 0] > 1) | (points[:, 1] < -1) | (points[:, 1] > 1)
    if np.any(mask_out):
        points[mask_out, 0] = np.random.uniform(-1, 1, np.sum(mask_out))
        points[mask_out, 1] = np.random.uniform(-1, 1, np.sum(mask_out))
        velocities[mask_out] = 0

    # Scale to screen
    # Map [-1, 1] to the screen
    scale = min(SIZE[0], SIZE[1]) * 0.45
    x2d = points[:, 0] * scale + SIZE[0]/2
    y2d = points[:, 1] * scale + SIZE[1]/2
    
    # Color based on speed and position
    speed = np.linalg.norm(velocities, axis=1)
    
    # Slower particles (settled on nodes) are bright gold/white
    # Faster particles (bouncing) are dim blue/purple
    
    py5.stroke_weight(1.5)
    
    # Settled sand
    mask_slow = speed < 0.01
    if np.any(mask_slow):
        py5.stroke(255, 220, 150, 40)
        pts = np.column_stack((x2d[mask_slow], y2d[mask_slow]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Moving sand
    mask_fast = speed >= 0.01
    if np.any(mask_fast):
        py5.stroke(100, 150, 255, 15)
        pts = np.column_stack((x2d[mask_fast], y2d[mask_fast]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

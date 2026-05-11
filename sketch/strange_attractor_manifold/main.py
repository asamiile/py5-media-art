import numpy as np
import py5
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 150000
# [x, y, z]
particles = np.random.uniform(-4.0, 4.0, (NUM_PARTICLES, 3)).astype(np.float32)
# Colors
colors = np.zeros((NUM_PARTICLES, 4), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 0)
    
    # Initialize colors based on starting z
    h = np.random.uniform(300, 340, NUM_PARTICLES)
    mask = np.random.rand(NUM_PARTICLES) < 0.6
    h[mask] = np.random.uniform(20, 40, np.sum(mask))
    
    colors[:, 0] = h
    colors[:, 1] = 90
    colors[:, 2] = 100
    colors[:, 3] = 40

def draw():
    global particles
    
    # Motion trails effect
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -300)
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_y(py5.frame_count * 0.005)
    
    # Thomas' cyclically symmetric attractor equations
    # dx/dt = sin(y) - b*x
    # dy/dt = sin(z) - b*y
    # dz/dt = sin(x) - b*z
    # We slowly drift parameter b
    t = py5.frame_count / float(TOTAL_FRAMES)
    b = 0.19 + np.sin(t * np.pi * 2) * 0.02
    dt = 0.05
    
    x = particles[:, 0]
    y = particles[:, 1]
    z = particles[:, 2]
    
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    
    particles[:, 0] += dx * dt
    particles[:, 1] += dy * dt
    particles[:, 2] += dz * dt
    
    scale = 80.0
    
    # Randomly respawn some particles to keep the flow alive
    respawn_mask = np.random.rand(NUM_PARTICLES) < 0.005
    particles[respawn_mask] = np.random.uniform(-4.0, 4.0, (np.sum(respawn_mask), 3))
    
    # We can draw the particles efficiently as points
    py5.stroke_weight(2.0)
    
    # Vectorized drawing using masks for the two color groups
    c1_mask = colors[:, 0] < 100  # Orange
    c2_mask = colors[:, 0] >= 100 # Fuchsia
    
    if np.any(c1_mask):
        py5.stroke(30, 100, 90, 15)
        py5.points(particles[c1_mask] * scale)
        
    if np.any(c2_mask):
        py5.stroke(320, 100, 100, 15)
        py5.points(particles[c2_mask] * scale)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

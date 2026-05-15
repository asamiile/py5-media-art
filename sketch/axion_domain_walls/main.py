from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 100000
PARTICLE_POS = np.random.uniform(-500, 500, (NUM_PARTICLES, 3))

def get_field(pos, t):
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    # Shifting planes
    f1 = np.sin(x * 0.005 + t * 0.02)
    f2 = np.sin(y * 0.005 + z * 0.002 + t * 0.01)
    f3 = np.cos(z * 0.005 - x * 0.002 + t * 0.015)
    return f1 + f2 + f3

def get_grad(pos, t):
    eps = 1.0
    # Central difference
    v0 = get_field(pos, t)
    vx = get_field(pos + [eps, 0, 0], t) - v0
    vy = get_field(pos + [0, eps, 0], t) - v0
    vz = get_field(pos + [0, 0, eps], t) - v0
    return np.stack([vx, vy, vz], axis=-1)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(10, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global PARTICLE_POS
    t = py5.frame_count
    
    py5.background(5, 5, 5)
    
    # Physics
    field_val = get_field(PARTICLE_POS, t * 0.05)
    grad = get_grad(PARTICLE_POS, t * 0.05)
    
    # Move towards isosurface (field_val = 0)
    # Velocity = - field_val * grad
    vel = -field_val[:, np.newaxis] * grad * 5.0
    
    # Add drift along the surface
    drift = np.cross(grad, [0, 1, 0]) * 2.0
    
    PARTICLE_POS += vel + drift
    
    # Boundary wrap
    PARTICLE_POS = (PARTICLE_POS + 600) % 1200 - 600
    
    # Rendering
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.003)
    py5.rotate_x(t * 0.001)
    
    py5.blend_mode(py5.ADD)
    
    # Color: Oxide Red (200, 50, 50) and Chrome Silver (200, 200, 220)
    py5.stroke_weight(2.5)
    
    # Split particles for two colors
    mask = field_val > 0
    
    py5.stroke(220, 80, 60, 120)
    py5.points(PARTICLE_POS[mask][::2])
    
    py5.stroke(200, 210, 230, 100)
    py5.points(PARTICLE_POS[~mask][::2])
    
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

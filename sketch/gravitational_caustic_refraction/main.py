from pathlib import Path
import subprocess
import sys
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_RAYS = 150_000
NUM_STARS = 12_000

# State
rays = None # x, y, z, phase
stars = None
lenses = None # x, y, z, mass

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global rays, stars, lenses
    
    # Initialize Rays in a jittered sheet
    grid_size = int(np.sqrt(NUM_RAYS))
    x = np.linspace(-1400, 1400, grid_size)
    y = np.linspace(-900, 900, grid_size)
    xv, yv = np.meshgrid(x, y)
    
    rays = np.zeros((grid_size * grid_size, 4))
    rays[:, 0] = xv.flatten() + np.random.normal(0, 5, len(rays))
    rays[:, 1] = yv.flatten() + np.random.normal(0, 5, len(rays))
    rays[:, 2] = np.random.uniform(-1500, -1200, len(rays))
    rays[:, 3] = np.random.uniform(0, np.pi * 2, len(rays))
    
    # Initialize Stars
    star_pos = np.random.uniform(-3000, 3000, (NUM_STARS, 3))
    stars = star_pos
    
    # Initialize Lenses
    lenses = np.zeros((4, 4)) # 4 lenses
    lenses[:, 3] = np.random.uniform(200, 500, 4)

def update_physics():
    global rays, lenses
    t = py5.frame_count / FPS
    
    # Move lenses in complex orbits
    lenses[0, 0] = 500 * np.sin(t * 0.4)
    lenses[0, 1] = 400 * np.cos(t * 0.3)
    lenses[1, 0] = -500 * np.cos(t * 0.5)
    lenses[1, 2] = 300 * np.sin(t * 0.2)
    lenses[2, 1] = -400 * np.sin(t * 0.6)
    lenses[2, 2] = -300 * np.cos(t * 0.4)
    lenses[3, 0] = 300 * np.cos(t * 0.7)
    lenses[3, 1] = 300 * np.sin(t * 0.5)
    
    # Move rays along Z
    rays[:, 2] += 14.0
    
    # Apply Gravitational Deflection (Vectorized)
    for i in range(len(lenses)):
        lx, ly, lz, mass = lenses[i]
        dx = rays[:, 0] - lx
        dy = rays[:, 1] - ly
        dz = rays[:, 2] - lz
        dist_sq = dx**2 + dy**2 + dz**2 + 1000
        
        # Stronger nonlinear deflection
        strength = mass * 120.0 / dist_sq
        rays[:, 0] -= dx * strength
        rays[:, 1] -= dy * strength
        rays[:, 2] -= dz * strength * 0.2

    # Reset rays
    mask = rays[:, 2] > 1800
    num_reset = np.sum(mask)
    if num_reset > 0:
        rays[mask, 2] = -1400
        rays[mask, 0] = np.random.uniform(-1400, 1400, num_reset)
        rays[mask, 1] = np.random.uniform(-900, 900, num_reset)

def draw():
    update_physics()
    
    py5.background(2, 2, 8)
    
    py5.translate(py5.width/2, py5.height/2, -800)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.001)
    
    # Draw Stars
    py5.stroke_weight(1.1)
    py5.stroke(220, 235, 255, 90)
    py5.points(stars)
    
    # Draw Lensed Rays
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 1.0)
    
    # Type Grouped Rendering for Speed
    # Group 1: Nebula Gold
    py5.stroke_weight(1.6)
    mask1 = (np.arange(len(rays)) % 3 == 0)
    py5.stroke(48, 85, 100, 0.22)
    py5.points(rays[mask1, :3])
    
    # Group 2: Electric Azure
    py5.stroke_weight(1.4)
    mask2 = (np.arange(len(rays)) % 3 == 1)
    py5.stroke(205, 75, 100, 0.2)
    py5.points(rays[mask2, :3])
    
    # Group 3: Diamond White
    py5.stroke_weight(1.2)
    mask3 = (np.arange(len(rays)) % 3 == 2)
    py5.stroke(200, 10, 100, 0.35)
    py5.points(rays[mask3, :3])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        py5.blend_mode(py5.BLEND)
        py5.color_mode(py5.RGB, 255)
        
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()

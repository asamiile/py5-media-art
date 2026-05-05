from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation parameters
NUM_PARTICLES = 80000
NUM_CENTERS = 12
# [x, y, z, vx, vy, vz]
particles = np.zeros((NUM_PARTICLES, 6))
# [x, y, z, mass]
centers = np.zeros((NUM_CENTERS, 4))

def setup():
    global particles, centers
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 8)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles in a large cloud
    particles[:, 0:3] = np.random.uniform(-600, 600, (NUM_PARTICLES, 3))
    particles[:, 3:6] = np.random.uniform(-0.5, 0.5, (NUM_PARTICLES, 3))
    
    # Initialize centers
    centers[:, 0:3] = np.random.uniform(-400, 400, (NUM_CENTERS, 3))
    centers[:, 3] = np.random.uniform(5.0, 15.0, NUM_CENTERS)

def draw():
    global particles, centers
    py5.background(0, 0, 3)
    
    t = py5.frame_count / FPS
    
    # Background starfield
    np.random.seed(42)
    for _ in range(400):
        x_s, y_s = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
        z_s = np.random.uniform(-1500, -500)
        s = np.random.uniform(0.5, 2.0)
        py5.stroke(0, 0, 100, 40)
        py5.stroke_weight(s)
        py5.point(x_s, y_s, z_s)
    np.random.seed(None)

    # Move centers using noise
    for i in range(NUM_CENTERS):
        nx = py5.noise(i * 10, t * 0.2) - 0.5
        ny = py5.noise(i * 10 + 1, t * 0.2) - 0.5
        nz = py5.noise(i * 10 + 2, t * 0.2) - 0.5
        centers[i, 0:3] += np.array([nx, ny, nz]) * 5.0
        
    # Gravity simulation (Vectorized)
    # For each particle, calculate attraction to all centers
    # pos: (N, 3), centers: (C, 3)
    pos = particles[:, 0:3]
    c_pos = centers[:, 0:3]
    
    # diffs: (C, N, 3)
    diffs = c_pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
    # dists: (C, N)
    dists = np.linalg.norm(diffs, axis=2)
    # Avoid division by zero
    dists = np.maximum(dists, 50.0)
    
    # force_mag: (C, N) = G * M / r^2
    force_mag = (centers[:, 3, np.newaxis] * 0.1) / (dists**1.5) # Softened gravity
    # forces: (C, N, 3)
    forces = force_mag[:, :, np.newaxis] * (diffs / dists[:, :, np.newaxis])
    
    # Total force on each particle
    total_force = np.sum(forces, axis=0)
    
    # Update velocity and position
    particles[:, 3:6] += total_force
    particles[:, 3:6] *= 0.95 # Drag
    particles[:, 0:3] += particles[:, 3:6]
    
    # Calculate min distance to any center
    min_dists = np.min(dists, axis=0)
    
    # Rendering
    py5.push_matrix()
    py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
    py5.rotate_y(t * 0.08)
    py5.rotate_x(py5.radians(10))
    
    # Main dust and star layer
    # Hue: 300 (Magenta) to 190 (Cyan)
    hues = py5.remap(min_dists, 40, 500, 190, 300)
    brights = py5.remap(min_dists, 40, 500, 100, 20)
    
    # Background "gas" layer (large, faint particles)
    # Using a small subset for speed
    gas_indices = np.linspace(0, NUM_PARTICLES-1, 5000, dtype=int)
    py5.stroke_weight(12.0)
    for h_target in [280, 300, 320]:
        mask = (hues[gas_indices] >= h_target - 20) & (hues[gas_indices] < h_target + 20)
        if np.any(mask):
            py5.stroke(h_target % 360, 60, 20, 2)
            py5.points(particles[gas_indices[mask], 0:3])
    
    for h_target in range(190, 301, 20):
        mask = (hues >= h_target) & (hues < h_target + 20)
        if np.any(mask):
            b_val = np.mean(brights[mask])
            # Nebula glow
            py5.stroke(h_target, 90, b_val, 12)
            py5.stroke_weight(4.0)
            py5.points(particles[mask, 0:3])
            
            # Dust core
            py5.stroke(h_target, 50, 100, 40)
            py5.stroke_weight(1.0)
            py5.points(particles[mask, 0:3])
            
            # Protostar centers (white-hot)
            star_mask = mask & (min_dists < 60)
            if np.any(star_mask):
                py5.stroke(190, 20, 100, 80)
                py5.stroke_weight(2.0)
                py5.points(particles[star_mask, 0:3])
            
    py5.pop_matrix()

    # Save frames and exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

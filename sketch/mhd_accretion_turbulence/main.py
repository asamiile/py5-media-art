from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

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

# Simulation Constants
NUM_PARTICLES = 180_000
DAMPING = 0.98
JITTER = 0.05
INNER_RADIUS = 200
OUTER_RADIUS = 1000

# State
particles = None
velocities = None
stars = None

def setup():
    global particles, velocities, stars
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 5)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles in a thin disk
    r = np.random.uniform(INNER_RADIUS, OUTER_RADIUS, NUM_PARTICLES)
    theta = np.random.uniform(0, 2*np.pi, NUM_PARTICLES)
    z = np.random.normal(0, 30, NUM_PARTICLES)
    
    particles = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    particles[:, 0] = r * np.cos(theta)
    particles[:, 1] = r * np.sin(theta)
    particles[:, 2] = z
    
    # Initial Keplerian velocity
    # v = sqrt(GM/r), so omega = v/r = sqrt(GM)/r^1.5
    # Let GM = 10^7
    omega = 2000.0 / (r**1.5)
    velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    velocities[:, 0] = -particles[:, 1] * omega
    velocities[:, 1] = particles[:, 0] * omega
    
    # Starfield
    stars = np.random.uniform(-2500, 2500, (15000, 3)).astype(np.float32)

def update_physics():
    global particles, velocities
    
    # Radius
    r_sq = np.sum(particles[:, :2]**2, axis=1)
    r = np.sqrt(r_sq)
    r = np.maximum(r, 10.0)
    
    # Central gravity (Newtonian)
    # F = GM/r^2
    grav_mag = 5000.0 / (r_sq + 1000.0)
    accel = -particles * (grav_mag / r)[:, np.newaxis]
    
    # MHD Turbulence proxy (MRI)
    # We'll use a time-varying noise field to perturb the velocities
    t = py5.frame_count * 0.03
    
    # Simplified MRI: magnetic tension and shear
    # We'll add some radial and vertical oscillations modulated by noise
    noise_scale = 0.005
    # Use radial distance and angle for noise coordinates
    theta = np.arctan2(particles[:, 1], particles[:, 0])
    
    # Add some turbulence
    jitter = np.random.normal(0, JITTER, (NUM_PARTICLES, 3))
    
    # Magnetic "ropes" effect: sinusoidal radial force
    mag_force = np.sin(r * 0.02 + t) * 0.05
    accel[:, 0] += particles[:, 0] * (mag_force / r)
    accel[:, 1] += particles[:, 1] * (mag_force / r)
    
    velocities += accel + jitter
    velocities *= DAMPING
    particles += velocities

def draw():
    update_physics()
    
    py5.background(2, 2, 8)
    
    py5.translate(py5.width / 2, py5.height / 2, -1000)
    py5.rotate_x(1.2)  # View from edge-on
    py5.rotate_z(py5.frame_count * 0.002)
    
    # Draw starfield
    py5.stroke(255, 255, 255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Speed magnitude for coloring
    v_mag = np.sqrt(np.sum(velocities**2, axis=1))
    v_norm = np.clip(v_mag * 0.1, 0, 1)
    
    # Multi-pass rendering
    hot_mask = v_norm > 0.6
    mid_mask = (v_norm <= 0.6) & (v_norm > 0.2)
    cold_mask = v_norm <= 0.2
    
    # Low speed: Plasma Blue
    py5.stroke(100, 150, 255, 70)
    py5.stroke_weight(1)
    py5.points(particles[cold_mask])
    
    # Mid speed: Magenta/Purple
    py5.stroke(200, 50, 255, 120)
    py5.stroke_weight(1.5)
    py5.points(particles[mid_mask])
    
    # High speed (Inner disk): Incandescent Orange
    py5.stroke(255, 160, 50, 200)
    py5.stroke_weight(2.5)
    py5.points(particles[hot_mask])
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

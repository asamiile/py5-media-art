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
NUM_PARTICLES = 150_000
NUM_HUBS = 12
HUB_STRENGTH = 0.12
DAMPING = 0.96
JITTER = 0.015
OSCILLATION_FREQ = 0.04
STARFIELD_COUNT = 12_000

# State
particles = None
velocities = None
hubs = None
hub_velocities = None
stars = None

def setup():
    global particles, velocities, hubs, hub_velocities, stars
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 10)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles
    particles = np.random.uniform(-900, 900, (NUM_PARTICLES, 3)).astype(np.float32)
    velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    
    # Initialize hubs with slow drift
    hubs = np.random.uniform(-600, 600, (NUM_HUBS, 3)).astype(np.float32)
    hub_velocities = np.random.uniform(-0.5, 0.5, (NUM_HUBS, 3)).astype(np.float32)
    
    # Initialize starfield
    stars = np.random.uniform(-1600, 1600, (STARFIELD_COUNT, 3)).astype(np.float32)

def update_physics():
    global particles, velocities, hubs
    
    # Hub drift
    hubs += hub_velocities
    # Bounce hubs
    mask = np.abs(hubs) > 700
    hub_velocities[mask] *= -1
    
    # Vectorized force calculation (loop over hubs for memory efficiency)
    total_force = np.zeros_like(particles)
    for hub in hubs:
        diff = hub - particles
        dist_sq = np.sum(diff**2, axis=1)
        dist = np.sqrt(dist_sq)
        dist = np.maximum(dist, 20.0)
        
        # Softened gravity force
        force_mag = HUB_STRENGTH / (dist**1.2)
        total_force += (diff / dist[:, np.newaxis]) * force_mag[:, np.newaxis]
    
    # Primordial oscillation
    phase = py5.frame_count * OSCILLATION_FREQ
    osc_factor = np.sin(phase) * 0.005
    total_force -= particles * osc_factor
    
    # Noise
    jitter = np.random.normal(0, JITTER, (NUM_PARTICLES, 3))
    
    velocities += total_force + jitter
    velocities *= DAMPING
    particles += velocities

def draw():
    update_physics()
    
    py5.background(3, 3, 12)
    
    py5.translate(py5.width / 2, py5.height / 2, -600)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.0015)
    
    # Draw starfield
    py5.stroke_weight(1)
    py5.stroke(255, 255, 255, 150)
    py5.points(stars)

    # Calculate density proxy
    # We'll use the distance to the nearest hub as density proxy
    min_dist_sq = np.full(NUM_PARTICLES, np.inf)
    for hub in hubs:
        d_sq = np.sum((hub - particles)**2, axis=1)
        min_dist_sq = np.minimum(min_dist_sq, d_sq)
    
    density = 1200.0 / (np.sqrt(min_dist_sq) + 40.0)
    d_norm = np.clip(density / 10.0, 0, 1)

    # Multi-pass rendering simulation using point categories
    hot_mask = d_norm > 0.75
    mid_mask = (d_norm <= 0.75) & (d_norm > 0.35)
    cold_mask = d_norm <= 0.35

    # Low density: Deep Cobalt
    py5.stroke(60, 110, 255, 50)
    py5.stroke_weight(1)
    py5.points(particles[cold_mask])

    # Medium density: Ionized Magenta
    py5.stroke(240, 60, 180, 110)
    py5.stroke_weight(1.5)
    py5.points(particles[mid_mask])

    # High density: Crystalline White
    py5.stroke(255, 255, 255, 180)
    py5.stroke_weight(2.2)
    py5.points(particles[hot_mask])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Create MP4
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        # Create Preview
        mid_frame = TOTAL_FRAMES // 2
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

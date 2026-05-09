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
NUM_CORES = 9
CORE_SPACING = 500
DAMPING = 0.94
JITTER = 0.02

# State
particles = None
velocities = None
cores = None
core_phases = None
stars = None

def setup():
    global particles, velocities, cores, core_phases, stars
    py5.size(*SIZE, py5.P3D)
    py5.background(3, 3, 10)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles in a large disk/cylinder
    r = np.random.uniform(0, 1200, NUM_PARTICLES)
    theta = np.random.uniform(0, 2*np.pi, NUM_PARTICLES)
    z = np.random.uniform(-400, 400, NUM_PARTICLES)
    
    particles = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    particles[:, 0] = r * np.cos(theta)
    particles[:, 1] = r * np.sin(theta)
    particles[:, 2] = z
    
    velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    
    # 3x3 Lattice of cores
    cores = []
    for x in [-CORE_SPACING, 0, CORE_SPACING]:
        for y in [-CORE_SPACING, 0, CORE_SPACING]:
            cores.append([x, y, 0])
    cores = np.array(cores, dtype=np.float32)
    core_phases = np.random.uniform(0, 2*np.pi, NUM_CORES)
    
    # Starfield
    stars = np.random.uniform(-2000, 2000, (12000, 3)).astype(np.float32)

def update_physics():
    global particles, velocities, cores
    
    t = py5.frame_count * 0.02
    
    # Modulate cores
    curr_cores = cores.copy()
    curr_cores[:, 0] += np.sin(t + core_phases) * 30.0
    curr_cores[:, 1] += np.cos(t * 0.7 + core_phases) * 30.0
    
    # Vectorized field calculation
    # For each particle, find the nearest core
    # We'll sum contributions from all cores weighted by 1/r^2
    total_v = np.zeros_like(particles)
    
    for core in curr_cores:
        diff = particles - core
        d_sq = np.sum(diff**2, axis=1)
        d = np.sqrt(d_sq)
        d = np.maximum(d, 20.0)
        
        # Vortex velocity: cross product of (0,0,1) and diff
        v_vortex = np.zeros_like(diff)
        v_vortex[:, 0] = -diff[:, 1]
        v_vortex[:, 1] = diff[:, 0]
        
        # Radial "Skyrmion" twist: n_z component
        # n_z = cos(theta(r))
        v_twist = np.zeros_like(diff)
        v_twist[:, 2] = np.sin(d * 0.01) * 5.0
        
        weight = 1.0 / (d**1.5)
        total_v += (v_vortex * 0.1 + v_twist) * weight[:, np.newaxis] * 500.0
    
    velocities += total_v * 0.5
    velocities += np.random.normal(0, JITTER, (NUM_PARTICLES, 3))
    velocities *= DAMPING
    particles += velocities

def draw():
    update_physics()
    
    py5.background(2, 2, 8)
    
    py5.translate(py5.width / 2, py5.height / 2, -600)
    py5.rotate_x(py5.frame_count * 0.002)
    py5.rotate_y(py5.frame_count * 0.003)
    
    # Draw starfield
    py5.stroke(255, 255, 255, 100)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Calculate colors based on local field strength (vortex intensity)
    # We'll use the velocity magnitude as a proxy for topological density
    v_mag = np.sqrt(np.sum(velocities**2, axis=1))
    v_norm = np.clip(v_mag * 0.2, 0, 1)
    
    # Multi-pass rendering
    hot_mask = v_norm > 0.7
    mid_mask = (v_norm <= 0.7) & (v_norm > 0.3)
    cold_mask = v_norm <= 0.3
    
    # Low intensity: Deep Violet
    py5.stroke(140, 50, 255, 60)
    py5.stroke_weight(1)
    py5.points(particles[cold_mask])
    
    # Mid intensity: Emerald Green
    py5.stroke(50, 255, 160, 110)
    py5.stroke_weight(1.5)
    py5.points(particles[mid_mask])
    
    # High intensity: Burnished Gold
    py5.stroke(255, 220, 80, 180)
    py5.stroke_weight(2.5)
    py5.points(particles[hot_mask])
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "24",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

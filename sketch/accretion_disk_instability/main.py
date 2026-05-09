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
DURATION_SEC = 25
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_PARTICLES = 180_000
NUM_STARS = 12_000

# State
particles = None # x, y, z, r, theta, type
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, stars
    
    # Initialize Particles in a disk
    particles = np.zeros((NUM_PARTICLES, 6))
    
    # Random Radius (Power law distribution for more density near center)
    r = 200 + 1000 * np.random.power(2, NUM_PARTICLES)
    theta = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)
    
    particles[:, 3] = r
    particles[:, 4] = theta
    
    # Disk coordinates
    particles[:, 0] = r * np.cos(theta)
    particles[:, 1] = np.random.normal(0, r * 0.05, NUM_PARTICLES) # Thickness proportional to radius
    particles[:, 2] = r * np.sin(theta)
    
    # Particle types: 0 = Inner Disk, 1 = Outer Disk, 2 = Jets
    particles[:, 5] = np.where(r < 500, 0, 1)
    
    # Reassign some to Jets
    jet_mask = np.random.random(NUM_PARTICLES) < 0.05
    particles[jet_mask, 5] = 2
    particles[jet_mask, 3] = np.random.uniform(0, 50, np.sum(jet_mask)) # Jet particles stay near axis
    
    # Initialize Stars
    stars = np.random.uniform(-4000, 4000, (NUM_STARS, 3))

def update_physics():
    global particles
    t = py5.frame_count / FPS
    
    # Disk Particles
    disk_mask = (particles[:, 5] < 2)
    r = particles[disk_mask, 3]
    theta = particles[disk_mask, 4]
    
    # Keplerian Velocity v_theta = k / sqrt(r)
    v_theta = 4.0 / np.sqrt(r * 0.01)
    theta += v_theta * 0.05
    particles[disk_mask, 4] = theta
    
    # Turbulence (Noise based on position and time)
    # Simplified: add a bit of noise to radius and Y
    freq = 0.005
    noise_r = np.sin(r * freq + t * 0.5) * 5.0
    noise_y = np.sin(theta * 2.0 + t) * (r * 0.02)
    
    curr_r = r + noise_r
    particles[disk_mask, 0] = curr_r * np.cos(theta)
    particles[disk_mask, 1] = np.random.normal(0, curr_r * 0.04, np.sum(disk_mask)) + noise_y
    particles[disk_mask, 2] = curr_r * np.sin(theta)
    
    # Jet Particles
    jet_mask = (particles[:, 5] == 2)
    # Jets shoot out along Y axis
    particles[jet_mask, 1] += np.where(particles[jet_mask, 1] >= 0, 15.0, -15.0)
    # Slow spiral
    particles[jet_mask, 4] += 0.2
    # Reset jets
    reset_mask = np.abs(particles[jet_mask, 1]) > 2000
    if np.any(reset_mask):
        indices = np.where(jet_mask)[0][reset_mask]
        particles[indices, 1] = np.random.normal(0, 10, len(indices))
        particles[indices, 3] = np.random.uniform(0, 30, len(indices))

def draw():
    update_physics()
    
    py5.background(2, 1, 4) # Very deep space purple
    
    py5.translate(py5.width/2, py5.height/2, -1000)
    py5.rotate_x(0.8) # Tilt the disk
    py5.rotate_z(py5.frame_count * 0.002)
    
    # Draw Stars
    py5.stroke(200, 220, 255, 80)
    py5.stroke_weight(1.0)
    py5.points(stars)
    
    # Draw Accretion Disk
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 1.0)
    
    # Inner Disk: Hot Orange/White
    mask0 = (particles[:, 5] == 0)
    py5.stroke_weight(2.0)
    py5.stroke(35, 95, 100, 0.35)
    py5.points(particles[mask0, :3])
    
    # Outer Disk: Deep Red
    mask1 = (particles[:, 5] == 1)
    py5.stroke_weight(1.6)
    py5.stroke(5, 90, 80, 0.25)
    py5.points(particles[mask1, :3])
    
    # Jets: Ultraviolet Indigo (More visible)
    mask2 = (particles[:, 5] == 2)
    py5.stroke_weight(2.2)
    py5.stroke(275, 80, 100, 0.45)
    # Give jets a bit of jitter to look "fuzzy/plasma-like"
    jet_points = particles[mask2, :3].copy()
    jet_points[:, 0] += np.random.normal(0, 5, len(jet_points))
    jet_points[:, 2] += np.random.normal(0, 5, len(jet_points))
    py5.points(jet_points)

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

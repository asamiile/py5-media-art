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
NUM_PARTICLES = 150_000
NUM_STARS = 10_000

# State
particles = None
stars = None

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles, stars
    
    # Initialize Stars
    star_pos = np.random.uniform(-2000, 2000, (NUM_STARS, 3))
    star_bright = np.random.uniform(50, 180, NUM_STARS)
    stars = np.column_stack((star_pos, star_bright))
    
    # Initialize 2 Vortex Rings
    # Particles are sampled around two circular filaments
    particles = np.zeros((NUM_PARTICLES, 8)) # x, y, z, vx, vy, vz, type, phase
    
    half = NUM_PARTICLES // 2
    
    # Ring 1 (Vertical)
    angle1 = np.random.uniform(0, np.pi * 2, half)
    r1 = 300
    particles[:half, 0] = r1 * np.cos(angle1)
    particles[:half, 1] = r1 * np.sin(angle1)
    particles[:half, 2] = -150
    particles[:half, 6] = 0 # Type 0
    
    # Ring 2 (Horizontal)
    angle2 = np.random.uniform(0, np.pi * 2, half)
    r2 = 300
    particles[half:, 0] = r2 * np.cos(angle2)
    particles[half:, 1] = 150
    particles[half:, 2] = r2 * np.sin(angle2)
    particles[half:, 6] = 1 # Type 1
    
    # Add random thickness to rings
    particles[:, :3] += np.random.normal(0, 15, (NUM_PARTICLES, 3))
    particles[:, 7] = np.random.uniform(0, np.pi * 2, NUM_PARTICLES)

def update_physics():
    global particles
    t = py5.frame_count / FPS
    
    # Move rings towards each other
    # Slow down as they collide
    collision_speed = 0.5 * (1.0 - np.exp(-(py5.frame_count - 600)**2 / 20000)) if py5.frame_count > 600 else 0.5
    particles[:NUM_PARTICLES//2, 2] += collision_speed
    particles[NUM_PARTICLES//2:, 1] -= collision_speed
    
    # Biot-Savart-like velocity field (Simplified)
    # Ring 1 Rotation
    mask1 = particles[:, 6] == 0
    p1 = particles[mask1, :3]
    dx = p1[:, 0]
    dy = p1[:, 1]
    dist = np.sqrt(dx**2 + dy**2)
    v_theta = 8.0 / (1.0 + np.abs(dist - 300) * 0.05)
    p1[:, 0] -= dy * v_theta * 0.012
    p1[:, 1] += dx * v_theta * 0.012
    particles[mask1, :3] = p1
    
    # Ring 2 Rotation
    mask2 = particles[:, 6] == 1
    p2 = particles[mask2, :3]
    dx2 = p2[:, 0]
    dz2 = p2[:, 2]
    dist2 = np.sqrt(dx2**2 + dz2**2)
    v_theta2 = 8.0 / (1.0 + np.abs(dist2 - 300) * 0.05)
    p2[:, 0] -= dz2 * v_theta2 * 0.012
    p2[:, 2] += dx2 * v_theta2 * 0.012
    particles[mask2, :3] = p2
    
    # Turbulence field (Sine wave based for speed)
    freq = 0.01
    amp = 0.8
    particles[:, 0] += np.sin(particles[:, 1] * freq + t) * amp
    particles[:, 1] += np.sin(particles[:, 2] * freq + t * 0.8) * amp
    particles[:, 2] += np.sin(particles[:, 0] * freq + t * 1.2) * amp

def draw():
    update_physics()
    
    py5.background(1, 1, 6) # Deep obsidian blue
    
    py5.translate(py5.width/2, py5.height/2, -600)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_z(py5.frame_count * 0.002)
    
    # Draw Stars
    py5.stroke(220, 230, 255, 100)
    py5.stroke_weight(1.2)
    py5.points(stars[:, :3])
    
    # Draw Vortex Particles
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 1.0)
    py5.stroke_weight(1.4)
    
    # Type 0: Electric Cyan
    mask0 = particles[:, 6] == 0
    py5.stroke(185, 75, 100, 0.25)
    py5.points(particles[mask0, :3])
    
    # Type 1: Royal Violet
    mask1 = particles[:, 6] == 1
    py5.stroke(275, 65, 100, 0.25)
    py5.points(particles[mask1, :3])
    
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

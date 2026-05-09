from pathlib import Path
import subprocess
import sys
import numpy as np
import py5
from scipy.interpolate import RegularGridInterpolator

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
NUM_PARTICLES = 160_000
NOISE_RES = 32
SPACE_SIZE = 1000
DAMPING = 0.92
SPEED = 2.0

# State
particles = None
velocities = None
lifetimes = None
noise_vol = None
interpolator = None
stars = None

def setup():
    global particles, velocities, lifetimes, noise_vol, interpolator, stars
    py5.size(*SIZE, py5.P3D)
    py5.background(2, 2, 5)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Precompute noise volume
    noise_vol = np.random.uniform(0, 1, (NOISE_RES, NOISE_RES, NOISE_RES)).astype(np.float32)
    # Smooth the noise volume slightly
    from scipy.ndimage import gaussian_filter
    noise_vol = gaussian_filter(noise_vol, sigma=1.5)
    
    # Setup interpolator for the noise volume
    coords = np.linspace(-SPACE_SIZE, SPACE_SIZE, NOISE_RES)
    interpolator = RegularGridInterpolator((coords, coords, coords), noise_vol, bounds_error=False, fill_value=0)
    
    # Initialize particles
    particles = np.random.uniform(-SPACE_SIZE, SPACE_SIZE, (NUM_PARTICLES, 3)).astype(np.float32)
    velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
    lifetimes = np.random.uniform(0, 1, NUM_PARTICLES).astype(np.float32)
    
    # Starfield
    stars = np.random.uniform(-SPACE_SIZE*2, SPACE_SIZE*2, (10000, 3)).astype(np.float32)

def update_physics():
    global particles, velocities, lifetimes, noise_vol
    
    # Update lifetimes
    lifetimes -= 0.02
    
    # Respawn dead particles
    dead_mask = lifetimes <= 0
    num_dead = np.sum(dead_mask)
    if num_dead > 0:
        particles[dead_mask] = np.random.uniform(-SPACE_SIZE, SPACE_SIZE, (num_dead, 3))
        velocities[dead_mask] = 0
        lifetimes[dead_mask] = np.random.uniform(0.5, 1.5, num_dead)
        
    # Get noise values and gradients at particle positions
    # Approximate gradient using small offsets
    eps = 10.0
    val = interpolator(particles)
    
    # We'll use the noise value itself to drive a "jittery" field
    # For a more "Planck foam" look, we use the noise to modulate velocity
    
    # Random walk influenced by noise intensity
    jitter = np.random.normal(0, 0.5, (NUM_PARTICLES, 3))
    velocities += jitter * (1.0 + val[:, np.newaxis] * 5.0)
    velocities *= DAMPING
    particles += velocities * SPEED

def draw():
    update_physics()
    
    py5.background(5, 5, 15)
    
    py5.translate(py5.width / 2, py5.height / 2, -800)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.002)
    
    # Draw starfield
    py5.stroke(255, 255, 255, 120)
    py5.stroke_weight(1)
    py5.points(stars)
    
    # Get noise values for coloring
    vals = interpolator(particles)
    
    # Filter particles for categorical rendering
    # High noise (Gold), Mid (Cyan), Low (Ultraviolet)
    hot_mask = vals > 0.7
    mid_mask = (vals <= 0.7) & (vals > 0.4)
    cold_mask = (vals <= 0.4)
    
    # Apply lifetime alpha modulation
    alpha_mod = np.clip(lifetimes * 255, 0, 255).astype(np.uint8)
    
    # To use individual alphas with py5.points(), we either batch by alpha or use a shader.
    # We'll batch by 5 alpha levels for efficiency.
    for a_level in range(5):
        alpha_min = a_level * 51
        alpha_max = (a_level + 1) * 51
        a_mask = (alpha_mod >= alpha_min) & (alpha_mod < alpha_max)
        
        # Cold (Ultraviolet/Deep Indigo)
        py5.stroke(120, 50, 255, alpha_max)
        py5.stroke_weight(1)
        py5.points(particles[cold_mask & a_mask])
        
        # Mid (Electric Cyan)
        py5.stroke(50, 220, 255, alpha_max)
        py5.stroke_weight(1.5)
        py5.points(particles[mid_mask & a_mask])
        
        # Hot (Solar Gold)
        py5.stroke(255, 200, 50, alpha_max)
        py5.stroke_weight(2.5)
        py5.points(particles[hot_mask & a_mask])

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

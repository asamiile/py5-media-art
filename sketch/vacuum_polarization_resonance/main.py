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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_PARTICLES = 200000
LIFESPAN = 120
SPEED = 2.5
DIPOLE_STRENGTH = 8000
NOISE_SCALE = 0.005

# State
pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
life = np.zeros(NUM_PARTICLES, dtype=np.int32)
hue = np.zeros(NUM_PARTICLES, dtype=np.float32)

# Starfield
NUM_STARS = 12000
star_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)
star_size = np.zeros(NUM_STARS, dtype=np.float32)

def init_particles(indices):
    count = len(indices)
    # Emit from a central region
    pos[indices] = (np.random.rand(count, 3) - 0.5) * 100
    # Initial velocity: radial + some jitter
    r = np.linalg.norm(pos[indices], axis=1, keepdims=True)
    r[r == 0] = 1
    vel[indices] = (pos[indices] / r) * SPEED + (np.random.rand(count, 3) - 0.5) * 1.5
    life[indices] = np.random.randint(LIFESPAN // 2, LIFESPAN, size=count)
    # Spectral palette: Cyan/Amethyst/Indigo (approx HSB)
    # 180 (Cyan) to 280 (Amethyst/Violet)
    hue[indices] = np.random.uniform(180, 280, size=count)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize stars
    global star_pos, star_size
    star_pos = (np.random.rand(NUM_STARS, 3) - 0.5) * 4000
    star_size = np.random.uniform(0.5, 2.5, size=NUM_STARS)
    
    # Initial particles
    init_particles(np.arange(NUM_PARTICLES))

def update():
    global pos, vel, life
    
    # 1. Dipole field advection
    # Dipole centers at (+d, 0, 0) and (-d, 0, 0)
    d = 200 * np.sin(py5.frame_count * 0.02)
    p1 = np.array([d, 0, 0], dtype=np.float32)
    p2 = np.array([-d, 0, 0], dtype=np.float32)
    
    r1 = pos - p1
    r2 = pos - p2
    d1 = np.linalg.norm(r1, axis=1, keepdims=True) + 10
    d2 = np.linalg.norm(r2, axis=1, keepdims=True) + 10
    
    # E field approx: q/r^2
    e1 = r1 / (d1**3) * DIPOLE_STRENGTH
    e2 = -r2 / (d2**3) * DIPOLE_STRENGTH
    e_field = e1 + e2
    
    # 2. Update physics
    vel += e_field
    # Add some noise-driven turbulence
    t = py5.frame_count * 0.01
    noise_x = py5.os_noise(pos[:, 0] * NOISE_SCALE, pos[:, 1] * NOISE_SCALE, t)
    noise_y = py5.os_noise(pos[:, 1] * NOISE_SCALE, pos[:, 2] * NOISE_SCALE, t)
    noise_z = py5.os_noise(pos[:, 2] * NOISE_SCALE, pos[:, 0] * NOISE_SCALE, t)
    vel += (np.stack([noise_x, noise_y, noise_z], axis=1) - 0.5) * 0.2
    
    pos += vel
    life -= 1
    
    # 3. Recycle dead particles
    dead_indices = np.where(life <= 0)[0]
    if len(dead_indices) > 0:
        init_particles(dead_indices)

def draw():
    update()
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    cam_dist = 800 + 200 * np.cos(py5.frame_count * 0.005)
    py5.camera(cam_dist * np.sin(py5.frame_count * 0.005), 
               -200 * np.sin(py5.frame_count * 0.008), 
               cam_dist * np.cos(py5.frame_count * 0.005), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    # Vectorized star rendering is faster but py5.points is limited in HSB/Alpha sometimes in P3D
    # Let's use a simple loop or vectorized points if possible
    # For 12k stars, points is fine
    py5.stroke(0, 0, 100, 40)
    py5.points(star_pos)
    
    # Draw Particles
    # Calculate alpha based on life and distance
    # Pulse near core
    dist_from_origin = np.linalg.norm(pos, axis=1)
    alpha = np.clip((life / LIFESPAN) * 100 * (1 - dist_from_origin / 1500), 0, 100)
    
    # Multi-pass rendering simulation:
    # We'll use py5.points() for speed and additive blending
    py5.blend_mode(py5.ADD)
    
    # Core highlights (Gold)
    gold_mask = (dist_from_origin < 150) & (np.random.rand(NUM_PARTICLES) < 0.1)
    if np.any(gold_mask):
        py5.stroke_weight(2)
        # Use average alpha for the gold highlight group
        avg_gold_alpha = float(np.mean(alpha[gold_mask]) * 0.5)
        py5.stroke(45, 80, 100, avg_gold_alpha)
        py5.points(pos[gold_mask])
    
    # Main filaments (Cyan/Amethyst)
    py5.stroke_weight(1.2)
    # Chunk by hue to allow different colors while staying vectorized
    num_chunks = 8
    hue_indices = np.argsort(hue)
    chunks = np.array_split(hue_indices, num_chunks)
    for chunk in chunks:
        if len(chunk) == 0: continue
        avg_h = float(np.mean(hue[chunk]))
        avg_a = float(np.mean(alpha[chunk]) * 0.25) # Lower alpha for dense feel
        py5.stroke(avg_h, 70, 90, avg_a)
        py5.points(pos[chunk])

    # Final frame management
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure we are in the right directory for ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-crf", "24", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid_frame = TOTAL_FRAMES // 2
        mid = str(FRAMES_DIR / f"frame-{mid_frame:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()

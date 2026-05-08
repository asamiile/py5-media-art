from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

# Add project root to path for lib imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

# Configuration
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 250000
# Exponential expansion factor: r(t) = r0 * exp(k * t)
# We want it to fill the screen but keep some detail
K_EXPANSION = 0.4 
INITIAL_R = 10.0

# State
particles_theta = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES).astype(np.float32)
particles_phi = np.arccos(np.random.uniform(-1, 1, NUM_PARTICLES)).astype(np.float32)
particles_r_factor = np.random.uniform(0.01, 1.0, NUM_PARTICLES).astype(np.float32)

# Seeding noise for filaments (multi-harmonic interference)
p1 = np.sin(particles_theta * 3) * np.cos(particles_phi * 5)
p2 = np.sin(particles_theta * 7) * np.sin(particles_phi * 3)
p3 = np.cos(particles_theta * 11 + particles_phi * 4)
particles_r_factor += 0.1 * (p1 + p2 + p3)
particles_r_factor = np.clip(particles_r_factor, 0.01, 1.5)

# Background stars (outside expansion)
NUM_STARS = 6000
stars_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize distant stars
    stars_pos[:, 0] = np.random.uniform(-py5.width * 5, py5.width * 5, NUM_STARS)
    stars_pos[:, 1] = np.random.uniform(-py5.height * 5, py5.height * 5, NUM_STARS)
    stars_pos[:, 2] = np.random.uniform(-5000, -2000, NUM_STARS)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    # Non-linear expansion: very fast at start, then slowing down (inflationary curve)
    # We'll use a sigmoid-like curve for the expansion factor to make it visual
    # t_exp ranges from ~0 to ~2000 pixels
    expansion_factor = INITIAL_R + 3000 * (1.0 - np.exp(-K_EXPANSION * py5.frame_count / 10))
    
    py5.background(5, 5, 15) # Deep cosmic indigo
    
    # Camera
    py5.translate(py5.width / 2, py5.height / 2, -1200)
    # Slow rotation as we "fly through"
    py5.rotate_y(py5.frame_count * 0.004)
    py5.rotate_z(py5.frame_count * 0.002)
    
    # 0. Draw Background Stars
    py5.stroke(255, 255, 255, 100)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    for p in stars_pos:
        py5.vertex(*p)
    py5.end_shape()
    
    # Calculate global positions
    # r = r_factor * expansion_factor
    r = (particles_r_factor * expansion_factor)
    
    x = r * np.sin(particles_phi) * np.cos(particles_theta)
    y = r * np.sin(particles_phi) * np.sin(particles_theta)
    z = r * np.cos(particles_phi)
    
    # Temperature/Color Mapping
    # Early (t small): White -> Yellow -> Cyan -> Violet -> Indigo
    if t < 0.1:
        # Blinding flash phase
        lerp_t = t / 0.1
        col_r = py5.lerp(255, 255, lerp_t)
        col_g = py5.lerp(255, 200, lerp_t)
        col_b = py5.lerp(255, 150, lerp_t)
    elif t < 0.4:
        # Hot plasma phase (Yellow to Cyan)
        lerp_t = (t - 0.1) / 0.3
        col_r = py5.lerp(255, 50, lerp_t)
        col_g = py5.lerp(200, 255, lerp_t)
        col_b = py5.lerp(150, 255, lerp_t)
    else:
        # Cooling to cosmic web (Cyan to Amethyst/Indigo)
        lerp_t = (t - 0.4) / 0.6
        col_r = py5.lerp(50, 150, lerp_t)
        col_g = py5.lerp(255, 50, lerp_t)
        col_b = py5.lerp(255, 255, lerp_t)

    # Render particles
    # Using a subset for performance if needed, but 250k points() should be okay on modern GPUs
    # We'll vary alpha by distance to create depth
    py5.begin_shape(py5.POINTS)
    for i in range(0, NUM_PARTICLES, 2):
        d = r[i] / (expansion_factor + 1)
        # Brighter, more persistent filaments
        alpha = (1.0 - d) * 255 * (1.1 - t) + 40
        py5.stroke(col_r, col_g, col_b, alpha)
        # Vary stroke weight based on filament density
        sw = 1.0 + 0.5 * (particles_r_factor[i] > 1.1)
        py5.stroke_weight(sw if t < 0.3 else sw * 0.8)
        py5.vertex(x[i], y[i], z[i])
    py5.end_shape()
    
    # Central Core Glow (The Singularity)
    if t < 0.3:
        core_alpha = (1.0 - t/0.3) * 255
        py5.push_matrix()
        py5.no_stroke()
        py5.fill(255, 255, 255, core_alpha)
        py5.sphere(50 * (1.0 - t/0.3))
        py5.pop_matrix()

    # Video & Preview Save
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error during video encoding: {e}")

if __name__ == "__main__":
    py5.run_sketch()

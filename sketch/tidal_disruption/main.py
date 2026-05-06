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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation constants
NUM_PARTICLES = 160000
G = 1500.0
BH_MASS = 6000.0
STAR_RADIUS = 35.0
STAR_POS = np.array([450.0, 50.0, 0.0])
STAR_VEL = np.array([-15.0, 45.0, 10.0]) # Targeted flyby

# Starfield
NUM_STARS = 4000
star_pos = np.zeros((NUM_STARS, 3))

# State
pos = np.zeros((NUM_PARTICLES, 3))
vel = np.zeros((NUM_PARTICLES, 3))

def setup():
    global pos, vel, star_pos
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize star as a sphere of particles
    phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    costheta = np.random.uniform(-1, 1, NUM_PARTICLES)
    u = np.random.uniform(0, 1, NUM_PARTICLES)
    
    theta = np.arccos(costheta)
    r = STAR_RADIUS * (u**(1/3))
    
    pos[:, 0] = r * np.sin(theta) * np.cos(phi) + STAR_POS[0]
    pos[:, 1] = r * np.sin(theta) * np.sin(phi) + STAR_POS[1]
    pos[:, 2] = r * np.cos(theta) + STAR_POS[2]
    
    # Initial velocity
    vel[:] = STAR_VEL
    vel[:, 0] += np.random.normal(0, 0.5, NUM_PARTICLES)
    vel[:, 1] += np.random.normal(0, 0.5, NUM_PARTICLES)
    vel[:, 2] += np.random.normal(0, 0.5, NUM_PARTICLES)

    # Initialize starfield
    for i in range(NUM_STARS):
        r_star = np.random.uniform(1000, 3000)
        phi_star = np.random.uniform(0, 2 * np.pi)
        costheta_star = np.random.uniform(-1, 1)
        theta_star = np.arccos(costheta_star)
        star_pos[i, 0] = r_star * np.sin(theta_star) * np.cos(phi_star)
        star_pos[i, 1] = r_star * np.sin(theta_star) * np.sin(phi_star)
        star_pos[i, 2] = r_star * np.cos(theta_star)

def draw():
    global pos, vel
    py5.background(0)
    
    # Camera - tighter and dynamic
    rot = py5.frame_count * 0.003
    py5.camera(550 * np.cos(rot), -250, 550 * np.sin(rot), 0, 0, 0, 0, 1, 0)
    
    # Draw starfield - more visible
    py5.stroke(255, 120)
    py5.stroke_weight(1.2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_STARS):
        py5.vertex(star_pos[i, 0], star_pos[i, 1], star_pos[i, 2])
    py5.end_shape()
    
    # Update physics (Vectorized)
    dist_sq = np.sum(pos**2, axis=1)
    dist = np.sqrt(dist_sq)
    dist = np.clip(dist, 12, 3000)
    
    # Newton's Gravity + Relativistic Boost
    force_mag = G * BH_MASS / (dist**2)
    force_mag *= (1.0 + 250.0 / dist) # Even stronger tidal effect
    
    force_vec = -pos * (force_mag / dist)[:, np.newaxis]
    
    vel += force_vec
    pos += vel
    
    # Rendering optimization: Group by hue
    speed = np.sqrt(np.sum(vel**2, axis=1))
    
    # Hue: 190 (Cyan) for fast, 20 (Amber) for slow
    hues = np.interp(speed, [20, 200], [20, 220]) % 360
    brits = np.interp(dist, [20, 800], [100, 40])
    
    # Use 15 color buckets for efficiency
    num_buckets = 15
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for b in range(num_buckets):
        hue_val = 20 + b * (200 / num_buckets)
        mask = (hues >= hue_val) & (hues < hue_val + (200 / num_buckets))
        if np.any(mask):
            avg_brit = np.mean(brits[mask])
            p_bucket = pos[mask]
            
            # Sub-glow pass
            py5.stroke(hue_val, 70, avg_brit, 30)
            py5.stroke_weight(4.0)
            py5.points(p_bucket)
            
            # Core particle pass
            py5.stroke(hue_val, 80, 100, 90)
            py5.stroke_weight(1.8)
            py5.points(p_bucket)

    # Draw Black Hole
    py5.no_stroke()
    py5.fill(0)
    py5.sphere(12)
    
    # Additive core glow (multi-pass)
    py5.push_matrix()
    for i in range(6):
        alpha = 25 - i * 4
        size = 18 + i * 12
        py5.fill(60, 15, 100, alpha) # White-Gold
        py5.sphere(size)
    py5.pop_matrix()
    
    # Save frame
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

if __name__ == "__main__":
    py5.run_sketch()

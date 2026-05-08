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
NUM_PARTICLES = 120000
LIFESPAN = 120
SPEED = 3.0
RADIUS = 400
NUM_STARS = 12000

# State
part_pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_life = np.zeros(NUM_PARTICLES, dtype=np.int32)
part_hue = np.zeros(NUM_PARTICLES, dtype=np.float32)

star_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

# Magnetic dipoles
NUM_DIPOLES = 8
dipole_pos = np.zeros((NUM_DIPOLES, 3), dtype=np.float32)
dipole_mom = np.zeros((NUM_DIPOLES, 3), dtype=np.float32)

def init_particles(indices):
    count = len(indices)
    # Emit from a hemispherical base
    phi = np.random.uniform(0, np.pi * 2, size=count)
    theta = np.arccos(np.random.uniform(0, 1, size=count)) # Hemisphere
    r = RADIUS + np.random.uniform(-10, 10, size=count)
    part_pos[indices, 0] = r * np.sin(theta) * np.cos(phi)
    part_pos[indices, 1] = r * np.sin(theta) * np.sin(phi)
    part_pos[indices, 2] = r * np.cos(theta) - RADIUS * 0.5
    
    # Spicule-like initial velocity (vertical + jitter)
    normals = part_pos[indices] / np.linalg.norm(part_pos[indices], axis=1, keepdims=True)
    part_vel[indices] = normals * SPEED + (np.random.rand(count, 3) - 0.5) * 1.5
    
    part_life[indices] = np.random.randint(LIFESPAN // 2, LIFESPAN, size=count)
    # Palette: Amber/Gold/Orange (20-50) and Violet (260-300)
    if np.random.rand() < 0.8:
        part_hue[indices] = np.random.uniform(20, 50, size=count)
    else:
        part_hue[indices] = np.random.uniform(260, 300, size=count)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize stars
    global star_pos
    star_pos = (np.random.rand(NUM_STARS, 3) - 0.5) * 5000
    
    # Initialize dipoles
    for i in range(NUM_DIPOLES):
        phi = i * (2 * np.pi / NUM_DIPOLES)
        dipole_pos[i] = [RADIUS * np.cos(phi), RADIUS * np.sin(phi), 0]
        dipole_mom[i] = [0, 0, 10000000]
    
    init_particles(np.arange(NUM_PARTICLES))

def update():
    global part_pos, part_vel, part_life, dipole_pos
    
    # Update dipoles
    t = py5.frame_count * 0.02
    for i in range(NUM_DIPOLES):
        dipole_pos[i, 2] = 100 * np.sin(t + i)
    
    # Magnetic Field B = sum( 3n(n.m) - m ) / r^3
    b_total = np.zeros_like(part_pos)
    for i in range(NUM_DIPOLES):
        r_vec = part_pos - dipole_pos[i]
        dist = np.linalg.norm(r_vec, axis=1, keepdims=True) + 10.0
        n = r_vec / dist
        dot = np.sum(n * dipole_mom[i], axis=1, keepdims=True)
        b_total += (3 * n * dot - dipole_mom[i]) / (dist**3) * 10.0
        
    # Flare event (magnetic reconnection)
    flare = np.maximum(0, py5.os_noise(t * 0.5, 0) * 3.0 - 2.0)
    
    # Update physics
    # Lorentz-ish force + vertical gravity
    part_vel += b_total * 0.5
    part_vel[:, 2] -= 0.05 # Solar gravity approx
    
    # Flare acceleration
    if flare > 0:
        part_vel *= (1.0 + flare * 0.1)
    
    part_pos += part_vel
    part_life -= 1
    
    # Recycle
    dead_indices = np.where(part_life <= 0)[0]
    if len(dead_indices) > 0:
        init_particles(dead_indices)

def draw():
    update()
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    cam_dist = 1200 + 200 * np.cos(py5.frame_count * 0.01)
    py5.camera(cam_dist * np.sin(py5.frame_count * 0.005), 
               cam_dist * np.cos(py5.frame_count * 0.005), 
               cam_dist * np.sin(py5.frame_count * 0.007), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(0, 0, 100, 30)
    py5.stroke_weight(1)
    py5.points(star_pos)
    
    py5.blend_mode(py5.ADD)
    
    # Draw Particles
    num_chunks = 8
    hue_indices = np.argsort(part_hue)
    chunks = np.array_split(hue_indices, num_chunks)
    
    dist_from_origin = np.linalg.norm(part_pos, axis=1)
    alpha = np.clip((part_life / LIFESPAN) * 100 * (1 - (dist_from_origin - RADIUS) / 2000), 0, 100)
    
    py5.stroke_weight(1.5)
    for chunk in chunks:
        if len(chunk) == 0: continue
        avg_h = float(np.mean(part_hue[chunk]))
        avg_a = float(np.mean(alpha[chunk]) * 0.2)
        
        # Flare modulation
        t = py5.frame_count * 0.02
        flare = np.maximum(0, py5.os_noise(t * 0.5, 0) * 3.0 - 2.0)
        
        py5.stroke(avg_h, 80, 100, avg_a * (1.0 + flare))
        py5.points(part_pos[chunk])

    # Final frame management
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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

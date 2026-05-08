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
NUM_PARTICLES = 150000
LIFESPAN = 150
SPEED = 3.0
RADIUS = 250
NUM_STARS = 12000

# State
part_pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_vel = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_life = np.zeros(NUM_PARTICLES, dtype=np.int32)
part_hue = np.zeros(NUM_PARTICLES, dtype=np.float32)

star_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

# Fracture stress points
NUM_FRACTURES = 8
fracture_points = np.zeros((NUM_FRACTURES, 3), dtype=np.float32)
fracture_intensity = np.zeros(NUM_FRACTURES, dtype=np.float32)

def init_particles(indices):
    count = len(indices)
    # Pick a random fracture point
    f_idx = np.random.randint(0, NUM_FRACTURES, size=count)
    bases = fracture_points[f_idx]
    
    # Emit from fracture with some normal + random velocity
    # Normal is approx bases / RADIUS
    normals = bases / np.linalg.norm(bases, axis=1, keepdims=True)
    part_pos[indices] = bases + normals * np.random.uniform(0, 10, size=(count, 1))
    
    # Helical/Normal velocity
    v_norm = normals * SPEED
    v_rand = (np.random.rand(count, 3) - 0.5) * 2.0
    part_vel[indices] = v_norm + v_rand
    
    part_life[indices] = np.random.randint(LIFESPAN // 2, LIFESPAN, size=count)
    part_hue[indices] = np.random.uniform(200, 260, size=count) # Cobalt to Purple

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize stars
    global star_pos, fracture_points
    star_pos = (np.random.rand(NUM_STARS, 3) - 0.5) * 5000
    
    # Initialize fractures on a sphere
    for i in range(NUM_FRACTURES):
        phi = np.random.uniform(0, np.pi * 2)
        theta = np.arccos(np.random.uniform(-1, 1))
        fracture_points[i] = [
            RADIUS * np.sin(theta) * np.cos(phi),
            RADIUS * np.sin(theta) * np.sin(phi),
            RADIUS * np.cos(theta)
        ]
    
    init_particles(np.arange(NUM_PARTICLES))

def update():
    global part_pos, part_vel, part_life, fracture_intensity
    
    # Update fracture intensities (pulsing starquake)
    t = py5.frame_count * 0.05
    for i in range(NUM_FRACTURES):
        fracture_intensity[i] = np.maximum(0, py5.os_noise(i, t) * 2.0 - 0.8)
    
    # Update particles
    # Magnetic field approx: Dipole + some twist
    # Central dipole at z axis
    m = np.array([0, 0, 1], dtype=np.float32)
    r = part_pos
    d = np.linalg.norm(r, axis=1, keepdims=True) + 1e-6
    n = r / d
    # B = 3n(n.m) - m
    dot = np.sum(n * m, axis=1, keepdims=True)
    b_field = (3 * n * dot - m) / (d**2) * 5000000
    
    # Add helical force
    v_twist = np.cross(part_vel, n) * 0.1
    part_vel += b_field * 0.01 + v_twist
    part_pos += part_vel
    part_life -= 1
    
    # Recycle
    dead_indices = np.where(part_life <= 0)[0]
    if len(dead_indices) > 0:
        # Only emit if nearby fractures are active? 
        # Or just emit normally with lower probability if inactive
        init_particles(dead_indices)

def draw():
    update()
    
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # Camera
    cam_dist = 1000 + 100 * np.sin(py5.frame_count * 0.01)
    py5.camera(cam_dist * np.cos(py5.frame_count * 0.004), 
               300 * np.sin(py5.frame_count * 0.007), 
               cam_dist * np.sin(py5.frame_count * 0.004), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(0, 0, 100, 30)
    py5.stroke_weight(1)
    py5.points(star_pos)
    
    # Draw Neutron Star Body
    py5.push_matrix()
    py5.no_stroke()
    py5.fill(0, 0, 5) # Dark obsidian
    py5.sphere_detail(40)
    py5.sphere(RADIUS * 0.98)
    py5.pop_matrix()
    
    py5.blend_mode(py5.ADD)
    
    # Draw Fractures
    for i in range(NUM_FRACTURES):
        if fracture_intensity[i] > 0:
            p = fracture_points[i]
            # Draw a glowing spot
            py5.stroke(45, 60, 100, fracture_intensity[i] * 100)
            py5.stroke_weight(10 + fracture_intensity[i] * 20)
            py5.point(*p)
            # Subtle volumetric glow
            py5.stroke(45, 80, 100, fracture_intensity[i] * 20)
            py5.stroke_weight(50)
            py5.point(*p)

    # Draw Particles
    # Group by hue
    num_chunks = 6
    hue_indices = np.argsort(part_hue)
    chunks = np.array_split(hue_indices, num_chunks)
    
    dist_from_origin = np.linalg.norm(part_pos, axis=1)
    alpha = np.clip((part_life / LIFESPAN) * 100 * (1 - (dist_from_origin - RADIUS) / 2000), 0, 100)
    
    py5.stroke_weight(1.5)
    for chunk in chunks:
        if len(chunk) == 0: continue
        avg_h = float(np.mean(part_hue[chunk]))
        avg_a = float(np.mean(alpha[chunk]) * 0.3)
        py5.stroke(avg_h, 80, 100, avg_a)
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

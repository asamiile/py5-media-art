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
LIFESPAN = 120
SPEED = 1.5
NUM_STARS = 12000
KNOT_SAMPLES = 200

# State
part_pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_life = np.zeros(NUM_PARTICLES, dtype=np.int32)
part_hue = np.zeros(NUM_PARTICLES, dtype=np.float32)

star_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

def trefoil_knot(t, scale=200):
    # Trefoil knot: x = sin(t)+2sin(2t), y = cos(t)-2cos(2t), z = -sin(3t)
    x = scale * (np.sin(t) + 2 * np.sin(2 * t))
    y = scale * (np.cos(t) - 2 * np.cos(2 * t))
    z = scale * -np.sin(3 * t)
    return np.stack([x, y, z], axis=1)

def init_particles(indices):
    count = len(indices)
    # Randomly distribute around the knot
    t = np.random.uniform(0, 2 * np.pi, size=count)
    bases = trefoil_knot(t)
    offsets = (np.random.rand(count, 3) - 0.5) * 150
    part_pos[indices] = bases + offsets
    part_life[indices] = np.random.randint(LIFESPAN // 2, LIFESPAN, size=count)
    part_hue[indices] = np.random.uniform(120, 240, size=count) # Emerald to Indigo

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize stars
    global star_pos
    star_pos = (np.random.rand(NUM_STARS, 3) - 0.5) * 5000
    
    init_particles(np.arange(NUM_PARTICLES))

def update():
    global part_pos, part_life
    
    # Knot points for Biot-Savart
    t_knot = np.linspace(0, 2 * np.pi, KNOT_SAMPLES, endpoint=False)
    knot_p = trefoil_knot(t_knot + py5.frame_count * 0.01)
    
    # Segment vectors dL
    dl = np.roll(knot_p, -1, axis=0) - knot_p
    
    # Biot-Savart Velocity field: V = sum( dL x r / r^3 )
    # To keep it fast, we'll only use a subset of particles or a more efficient approach
    # Let's use a subset of knot points for each particle chunk
    num_knot_sub = 40
    knot_idx = np.random.choice(KNOT_SAMPLES, num_knot_sub, replace=False)
    sub_p = knot_p[knot_idx]
    sub_dl = dl[knot_idx]
    
    # Vectorized Biot-Savart for current part_pos
    # Reshape for broadcasting: part_pos (N, 1, 3), sub_p (1, M, 3)
    r = part_pos[:, np.newaxis, :] - sub_p[np.newaxis, :, :]
    dist = np.linalg.norm(r, axis=2, keepdims=True) + 10.0
    
    # Velocity contribution: sub_dl x r / dist^3
    v_cont = np.cross(sub_dl[np.newaxis, :, :], r) / (dist**3)
    vel = np.sum(v_cont, axis=1) * 200000.0
    
    part_pos += vel + (np.random.rand(NUM_PARTICLES, 3) - 0.5) * 0.5
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
    cam_dist = 1000 + 100 * np.sin(py5.frame_count * 0.008)
    py5.camera(cam_dist * np.cos(py5.frame_count * 0.005), 
               cam_dist * np.sin(py5.frame_count * 0.004), 
               cam_dist * np.sin(py5.frame_count * 0.005), 
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
    alpha = np.clip((part_life / LIFESPAN) * 100 * (1 - dist_from_origin / 2500), 0, 100)
    
    py5.stroke_weight(1.3)
    for chunk in chunks:
        if len(chunk) == 0: continue
        avg_h = float(np.mean(part_hue[chunk]))
        avg_a = float(np.mean(alpha[chunk]) * 0.25)
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

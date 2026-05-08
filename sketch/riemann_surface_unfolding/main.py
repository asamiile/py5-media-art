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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Constants
NUM_PARTICLES = 180000
LIFESPAN = 180
SPEED = 2.0
NUM_STARS = 12000
GRID_RES = 60

# State
part_pos = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
part_life = np.zeros(NUM_PARTICLES, dtype=np.int32)
part_hue = np.zeros(NUM_PARTICLES, dtype=np.float32)

star_pos = np.zeros((NUM_STARS, 3), dtype=np.float32)

def complex_func(z):
    # Riemann surface for w^2 = z^3 - z
    return np.sqrt(z**3 - z)

def init_particles(indices):
    count = len(indices)
    # Start in a 2D plane z = x + iy
    x = np.random.uniform(-3, 3, size=count)
    y = np.random.uniform(-3, 3, size=count)
    z = x + 1j * y
    
    # Calculate w (two sheets)
    w = complex_func(z)
    sheet = np.random.choice([-1, 1], size=count)
    w_val = w * sheet
    
    # Map to 3D: (x, y, real(w)) or similar
    part_pos[indices, 0] = x * 150
    part_pos[indices, 1] = y * 150
    part_pos[indices, 2] = np.real(w_val) * 100
    
    part_life[indices] = np.random.randint(LIFESPAN // 2, LIFESPAN, size=count)
    # Hue based on phase of w
    part_hue[indices] = (np.angle(w_val) / np.pi * 180 + 360) % 360

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
    
    # Advect particles along phase gradient
    # Convert pos back to complex z
    x = part_pos[:, 0] / 150.0
    y = part_pos[:, 1] / 150.0
    z = x + 1j * y
    
    # Perturb z
    t = py5.frame_count * 0.01
    dz = (np.exp(1j * (np.angle(z) + t)) * 0.02)
    z_new = z + dz
    
    # Calculate new w
    w = complex_func(z_new)
    # Maintain sheet (approximate via continuity)
    # For simplicity, we just recalculate and add some noise
    sheet = np.where(part_pos[:, 2] >= 0, 1, -1)
    w_val = w * sheet
    
    part_pos[:, 0] = np.real(z_new) * 150
    part_pos[:, 1] = np.imag(z_new) * 150
    part_pos[:, 2] = np.real(w_val) * 100 + np.sin(t + part_pos[:, 0] * 0.01) * 20
    
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
    cam_dist = 1200 + 200 * np.cos(py5.frame_count * 0.003)
    py5.camera(cam_dist * np.sin(py5.frame_count * 0.004), 
               cam_dist * np.cos(py5.frame_count * 0.005), 
               cam_dist * np.cos(py5.frame_count * 0.004), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke(0, 0, 100, 30)
    py5.stroke_weight(1)
    py5.points(star_pos)
    
    py5.blend_mode(py5.ADD)
    
    # Draw Particles
    # Group by hue
    num_chunks = 10
    hue_indices = np.argsort(part_hue)
    chunks = np.array_split(hue_indices, num_chunks)
    
    dist_from_origin = np.linalg.norm(part_pos, axis=1)
    alpha = np.clip((part_life / LIFESPAN) * 100 * (1 - dist_from_origin / 2000), 0, 100)
    
    py5.stroke_weight(1.2)
    for chunk in chunks:
        if len(chunk) == 0: continue
        avg_h = float(np.mean(part_hue[chunk]))
        avg_a = float(np.mean(alpha[chunk]) * 0.2)
        py5.stroke(avg_h, 70, 100, avg_a)
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

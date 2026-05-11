from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 60_000
L = 1200.0
U = 3.2
DELTA = 55.0
B_STRENGTH = 0.45
K = 2.0 * np.pi / L

# Particle state
pos = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
colors = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)

def init_particles():
    global pos, colors
    pos[:, 0] = np.random.uniform(-L, L, NUM_PARTICLES)
    pos[:, 1] = np.random.normal(0, DELTA * 2.0, NUM_PARTICLES)
    
    y_norm = np.clip(pos[:, 1] / (DELTA * 3.0), -1, 1)
    teal = np.array([0.0, 0.8, 0.8])
    gold = np.array([1.0, 0.8, 0.1])
    amethyst = np.array([0.6, 0.3, 0.9])
    
    mask_pos = y_norm > 0
    colors[mask_pos] = teal + (gold - teal) * y_norm[mask_pos][:, np.newaxis]
    colors[~mask_pos] = teal + (amethyst - teal) * (-y_norm[~mask_pos])[:, np.newaxis]
    colors += np.random.uniform(-0.05, 0.05, (NUM_PARTICLES, 3))
    colors = np.clip(colors, 0, 1)

def update_physics():
    global pos
    x, y = pos[:, 0], pos[:, 1]
    vx = U * np.tanh(y / DELTA)
    t = py5.frame_count * 0.04
    vy = 0.35 * U * np.sin(K * x + t) * np.exp(-np.abs(y) / (DELTA * 1.5))
    vy -= B_STRENGTH * (y / DELTA) * 0.2
    pos[:, 0] += vx * 3.2
    pos[:, 1] += vy * 3.2
    pos[:, 0] += np.random.normal(0, 0.2, NUM_PARTICLES)
    pos[:, 1] += np.random.normal(0, 0.2, NUM_PARTICLES)
    
    mask_right = pos[:, 0] > L
    pos[mask_right, 0] -= 2 * L
    mask_left = pos[:, 0] < -L
    pos[mask_left, 0] += 2 * L

stars = None
def draw_stars():
    global stars
    if stars is None:
        num_stars = 8000
        stars = np.random.uniform(0, py5.width, (num_stars, 2))
        stars[:, 1] = np.random.uniform(0, py5.height, num_stars)
    py5.stroke(220, 230, 255, 150)
    py5.stroke_weight(1)
    py5.points(stars)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(5, 2, 10)
    init_particles()

def draw():
    update_physics()
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 2, 10, 35) # Fade
    py5.rect(0, 0, py5.width, py5.height)
    
    draw_stars()
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    
    py5.blend_mode(py5.ADD)
    
    num_batches = 12
    batch_size = NUM_PARTICLES // num_batches
    for i in range(num_batches):
        start = i * batch_size
        end = (i + 1) * batch_size
        c = colors[start]
        py5.stroke(c[0]*255, c[1]*255, c[2]*255, 25) # Safe alpha
        py5.stroke_weight(1.2)
        py5.points(pos[start:end])
    
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

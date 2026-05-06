import numpy as np
from pathlib import Path
import subprocess
import sys
import py5

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

# Simulation Parameters
NUM_VORTICES = 120
NUM_PARTICLES = 120000
VORTEX_STRENGTH = 2000.0
CORE_RADIUS = 30.0

# State
v_pos = None
v_circ = None
p_pos = None
starfield = None

def setup():
    global v_pos, v_circ, p_pos, starfield
    py5.size(*SIZE, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Random vortices
    v_pos = np.random.uniform(0, max(py5.width, py5.height), (NUM_VORTICES, 2)).astype(np.float32)
    v_circ = np.random.choice([-1, 1], NUM_VORTICES).astype(np.float32) * VORTEX_STRENGTH
    
    # Particles
    p_pos = np.random.uniform(0, py5.width, (NUM_PARTICLES, 2)).astype(np.float32)
    p_pos[:, 1] *= (py5.height / py5.width)
    
    # Starfield
    num_stars = 2000
    sx = np.random.uniform(0, py5.width, num_stars)
    sy = np.random.uniform(0, py5.height, num_stars)
    sb = np.random.uniform(10, 60, num_stars)
    starfield = np.stack([sx, sy, sb], axis=-1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global v_pos, p_pos
    
    # 1. Move Vortices (Self-advection)
    v_vel = np.zeros_like(v_pos)
    for i in range(NUM_VORTICES):
        diff = v_pos[i] - v_pos
        dist_sq = np.sum(diff**2, axis=-1) + CORE_RADIUS**2
        v_vel[i, 0] = np.sum(-diff[:, 1] * v_circ / (2 * np.pi * dist_sq))
        v_vel[i, 1] = np.sum(diff[:, 0] * v_circ / (2 * np.pi * dist_sq))
    
    v_pos += v_vel
    
    # 2. Move Particles (Advection)
    p_vel = np.zeros_like(p_pos)
    # Vectorized over vortices to keep it fast
    for i in range(NUM_VORTICES):
        diff = p_pos - v_pos[i]
        dist_sq = np.sum(diff**2, axis=-1) + CORE_RADIUS**2
        p_vel[:, 0] += -diff[:, 1] * v_circ[i] / (2 * np.pi * dist_sq)
        p_vel[:, 1] += diff[:, 0] * v_circ[i] / (2 * np.pi * dist_sq)
    
    p_pos += p_vel
    
    # Boundary handling (wrap)
    p_pos[:, 0] %= py5.width
    p_pos[:, 1] %= py5.height
    v_pos[:, 0] %= py5.width
    v_pos[:, 1] %= py5.height

    # Render with trails
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw Static Stars (subtle)
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[2], 40)
        py5.point(s[0], s[1])
    
    # Speed-based coloring
    speed = np.sqrt(np.sum(p_vel**2, axis=-1))
    
    # High speed: Cyan
    mask_high = speed > 6.0
    py5.stroke_weight(1.5)
    py5.stroke(185, 80, 100, 70)
    py5.points(p_pos[mask_high])
    
    # Medium speed: Ice Blue
    mask_med = (speed <= 6.0) & (speed > 2.0)
    py5.stroke_weight(1.2)
    py5.stroke(200, 60, 90, 45)
    py5.points(p_pos[mask_med])
    
    # Low speed: Muted Indigo
    mask_low = speed <= 2.0
    py5.stroke_weight(1.0)
    py5.stroke(220, 40, 70, 25)
    py5.points(p_pos[mask_low])

    # Vortex centers (subtle white glow)
    py5.stroke_weight(2)
    py5.stroke(0, 0, 100, 40)
    py5.points(v_pos)

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

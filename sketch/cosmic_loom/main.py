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
NUM_PARTICLES = 100000
FRICTION = 0.94

# State
pos = None
vel = None
starfield = None
attractors = None

def get_bezier_point(p0, p1, p2, p3, t):
    # Vectorized bezier point
    t = t[:, np.newaxis]
    return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3

def setup():
    global pos, vel, starfield, attractors
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    pos = np.random.uniform(-1000, 1000, (NUM_PARTICLES, 3)).astype(np.float32)
    vel = np.zeros_like(pos)
    
    # 3 Splines (each with 4 control points)
    attractors = np.random.uniform(-600, 600, (3, 4, 3)).astype(np.float32)
    
    # Starfield
    num_stars = 4000
    sx = np.random.uniform(-py5.width*2, py5.width*2, num_stars)
    sy = np.random.uniform(-py5.height*2, py5.height*2, num_stars)
    sz = np.random.uniform(-4000, 1000, num_stars)
    sb = np.random.uniform(10, 70, num_stars)
    starfield = np.stack([sx, sy, sz, sb], axis=-1)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global pos, vel, attractors
    
    # 1. Update Attractors (Harmonic motion)
    t_phase = py5.frame_count * 0.015
    for i in range(3):
        for j in range(4):
            attractors[i, j, 0] += np.sin(t_phase * (i+1) + j) * 8.0
            attractors[i, j, 1] += np.cos(t_phase * (j+1) + i) * 8.0
            attractors[i, j, 2] += np.sin(t_phase * (i+j)) * 6.0
    
    # 2. Physics: Particles attracted to splines
    num_samples = 12
    sample_t = np.linspace(0, 1, num_samples)
    
    target_points = []
    for i in range(3):
        p0, p1, p2, p3 = attractors[i]
        target_points.append(get_bezier_point(p0, p1, p2, p3, sample_t))
    
    targets = np.vstack(target_points)
    
    # Vectorized attraction to targets
    for target in targets:
        diff = target - pos
        dist_sq = np.sum(diff**2, axis=-1) + 400.0
        dist = np.sqrt(dist_sq)
        vel += (diff / dist[:, np.newaxis]) * 0.25
        
    vel *= FRICTION
    pos += vel
    
    # 3. Render
    py5.background(0)
    
    # Starfield
    py5.push_matrix()
    py5.stroke_weight(1)
    for s in starfield:
        py5.stroke(0, 0, s[3], 45)
        py5.point(s[0], s[1], s[2])
    py5.pop_matrix()
    
    py5.translate(py5.width/2, py5.height/2, -1200)
    py5.rotate_y(py5.frame_count * 0.004)
    py5.rotate_x(py5.frame_count * 0.001)
    
    # Particles
    # Color based on proximity to center
    dist_center = np.linalg.norm(pos, axis=-1)
    
    # Band 1: Royal Amethyst (Core)
    mask1 = dist_center < 500
    py5.stroke_weight(1.8)
    py5.stroke(285, 80, 100, 75)
    py5.points(pos[mask1])
    
    # Band 2: Electric Indigo (Outer)
    mask2 = (dist_center >= 500) & (dist_center < 900)
    py5.stroke_weight(1.4)
    py5.stroke(260, 70, 85, 45)
    py5.points(pos[mask2])
    
    # Band 3: Faint Violet (Extreme)
    mask3 = dist_center >= 900
    py5.stroke_weight(1.0)
    py5.stroke(270, 50, 60, 20)
    py5.points(pos[mask3])

    # Draw "Loom Star" highlights
    for i in range(3):
        py5.stroke_weight(10)
        py5.stroke(45, 40, 100, 50) # Gold
        py5.points(attractors[i])

    if py5.frame_count % 60 == 0:
        print(f"Frame {py5.frame_count}/{TOTAL_FRAMES}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

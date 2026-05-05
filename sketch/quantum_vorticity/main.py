from pathlib import Path
import subprocess
import sys
import numpy as np
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

# Constants
NUM_PARTICLES = 30000
NUM_VORTICES = 8
STAR_COUNT = 1200
ADVECTION_STEP = 2.0
DAMPING = 0.94

class Vortex:
    def __init__(self):
        self.pos = np.array([np.random.uniform(200, SIZE[0]-200), np.random.uniform(200, SIZE[1]-200)])
        self.vel = np.random.uniform(-1, 1, 2)
        self.strength = np.random.choice([-1, 1]) * 50.0
        
    def update(self):
        self.pos += self.vel
        if self.pos[0] < 100 or self.pos[0] > SIZE[0]-100: self.vel[0] *= -1
        if self.pos[1] < 100 or self.pos[1] > SIZE[1]-100: self.vel[1] *= -1

particles = np.random.uniform(0, [SIZE[0], SIZE[1]], (NUM_PARTICLES, 2)).astype(np.float32)
p_vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
p_age = np.random.uniform(0, 150, NUM_PARTICLES).astype(np.float32)
vortices = [Vortex() for _ in range(NUM_VORTICES)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(60, 180)))
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    global particles, p_vel, p_age
    
    # 1. Update Vortices
    for v in vortices:
        v.update()
        
    # 2. Vectorized Velocity Field (Biot-Savart Point Vortices)
    # v = sum( strength * (r x z_hat) / r^2 )
    v_field = np.zeros_like(particles)
    for v in vortices:
        r_vec = particles - v.pos
        dist_sq = np.sum(r_vec**2, axis=1, keepdims=True)
        dist_sq = np.maximum(dist_sq, 50.0) # avoid division by zero
        
        # velocity is perpendicular to r: (-ry, rx)
        v_field[:, 0] += -v.strength * r_vec[:, 1] / dist_sq[:, 0]
        v_field[:, 1] += v.strength * r_vec[:, 0] / dist_sq[:, 0]

    p_vel = p_vel * DAMPING + v_field * ADVECTION_STEP
    particles += p_vel
    p_age += 1
    
    # Reset dead/OOB
    dead = (p_age > 150) | (particles[:,0] < 0) | (particles[:,0] > SIZE[0]) | (particles[:,1] < 0) | (particles[:,1] > SIZE[1])
    num_dead = np.sum(dead)
    if num_dead > 0:
        particles[dead] = np.random.uniform(0, [SIZE[0], SIZE[1]], (num_dead, 2))
        p_vel[dead] = 0
        p_age[dead] = 0

    # 3. Render
    py5.background(2, 2, 8)
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)
        
    # Superfluid Filaments
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Split into 3 color groups
    for g in range(3):
        mask = (np.arange(NUM_PARTICLES) % 3 == g)
        # Map velocity magnitude to alpha
        speed = np.linalg.norm(p_vel[mask], axis=1)
        alpha = np.clip(speed * 20, 2, 40)
        
        if g == 0: # Cyan
            py5.stroke(190, 80, 100, np.mean(alpha))
        elif g == 1: # Amethyst
            py5.stroke(280, 70, 100, np.mean(alpha))
        else: # Gold
            py5.stroke(45, 90, 100, np.mean(alpha))
            
        py5.stroke_weight(1.0)
        py5.points(particles[mask])
        
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.blend_mode(py5.BLEND)

    # 4. Capture
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.7):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

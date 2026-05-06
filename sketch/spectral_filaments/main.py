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
NUM_PARTICLES = 40000
NUM_SOURCES = 4
STAR_COUNT = 1500
ADVECTION_STEP = 0.8
DAMPING = 0.96

class Source:
    def __init__(self):
        self.pos = np.array([np.random.uniform(200, SIZE[0]-200), np.random.uniform(200, SIZE[1]-200)])
        self.vel = np.random.uniform(-1.5, 1.5, 2)
        self.moment = np.random.uniform(-1, 1, 2)
        self.moment /= np.linalg.norm(self.moment)
        self.rot_speed = np.random.uniform(-0.04, 0.04)
        
    def update(self):
        self.pos += self.vel
        if self.pos[0] < 100 or self.pos[0] > SIZE[0]-100: self.vel[0] *= -1
        if self.pos[1] < 100 or self.pos[1] > SIZE[1]-100: self.vel[1] *= -1
        
        c, s = np.cos(self.rot_speed), np.sin(self.rot_speed)
        m = self.moment
        self.moment = np.array([m[0]*c - m[1]*s, m[0]*s + m[1]*c])

particles = np.random.uniform(0, [SIZE[0], SIZE[1]], (NUM_PARTICLES, 2)).astype(np.float32)
p_vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
p_age = np.random.uniform(0, 150, NUM_PARTICLES).astype(np.float32)
sources = [Source() for _ in range(NUM_SOURCES)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(60, 180)))
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    global particles, p_vel, p_age
    
    # 1. Update Sources
    for s in sources:
        s.update()
        
    # 2. Vectorized Field Calculation
    field = np.zeros_like(particles)
    for s in sources:
        r_vec = particles - s.pos
        dist_sq = np.sum(r_vec**2, axis=1, keepdims=True)
        dist = np.sqrt(dist_sq)
        dist = np.maximum(dist, 10.0) # avoid division by zero
        r_hat = r_vec / dist
        
        # B = (3*r_hat*(m . r_hat) - m) / r^2
        m_dot_r = np.sum(s.moment * r_hat, axis=1, keepdims=True)
        b = (3 * r_hat * m_dot_r - s.moment) / dist_sq
        field += b

    p_vel = p_vel * DAMPING + field * ADVECTION_STEP
    particles += p_vel
    p_age += 1
    
    # Reset dead/OOB particles
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
        
    # Filaments
    py5.blend_mode(py5.ADD)
    
    # We'll use HSB but set it once for groups of particles to speed up
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # To keep it fast, we'll draw points.
    # We can use a single py5.points() if we have fixed colors, but we want variety.
    # Let's split into 3 color groups
    for g in range(3):
        mask = (np.arange(NUM_PARTICLES) % 3 == g)
        speed = np.linalg.norm(p_vel[mask], axis=1)
        alpha = np.clip(speed * 30, 2, 35)
        
        if g == 0: # Emerald
            py5.stroke(150, 70, 100, np.mean(alpha))
        elif g == 1: # Gold
            py5.stroke(45, 80, 100, np.mean(alpha))
        else: # Cobalt
            py5.stroke(210, 80, 100, np.mean(alpha))
            
        py5.stroke_weight(1.0)
        # Using py5.points() with a numpy array of coordinates
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
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.8):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

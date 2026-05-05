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
NUM_FRAGMENTS = 5000
STAR_COUNT = 1500
MAGNETIC_STRENGTH = 0.02

class Fragment:
    def __init__(self, x, y, angle, speed):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([np.cos(angle), np.sin(angle)]) * speed
        self.age = 0
        self.max_age = np.random.uniform(30, 120)
        self.charge = np.random.choice([-1, 1])
        self.active = True
        
    def update(self):
        if not self.active: return
        
        # Lorentz-like force: v is perpendicular to B (into screen)
        # F = q * (v x B) -> force is perpendicular to velocity
        force_dir = np.array([-self.vel[1], self.vel[0]])
        self.vel += force_dir * MAGNETIC_STRENGTH * self.charge
        
        self.pos += self.vel
        self.age += 1
        if self.age > self.max_age:
            self.active = False

fragments = []
stars = []

def trigger_collision():
    fragments.clear()
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    for _ in range(NUM_FRAGMENTS):
        angle = np.random.uniform(0, py5.TWO_PI)
        speed = np.random.uniform(2, 10)
        fragments.append(Fragment(cx, cy, angle, speed))

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(80, 200)))
        
    trigger_collision()
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # Rhythmic collision events (every 2 seconds)
    if py5.frame_count % (FPS * 2) == 0:
        trigger_collision()
        
    # 1. Update Fragments
    for f in fragments:
        f.update()
        
    # 2. Draw Background
    py5.background(2, 2, 5) # Darkest navy
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Fragments (Collision)
    py5.blend_mode(py5.ADD)
    for f in fragments:
        if not f.active: continue
        
        # Spectral decay color
        life_ratio = f.age / f.max_age
        if life_ratio < 0.2:
            # White-Gold core
            py5.stroke(255, 255, 200, 200)
        elif life_ratio < 0.6:
            # Electric Cyan
            py5.stroke(50, 255, 255, 150)
        else:
            # Royal Magenta
            py5.stroke(255, 50, 200, 100)
            
        py5.stroke_weight(py5.remap(life_ratio, 0, 1, 2, 0.5))
        # Draw a small streak
        py5.line(f.pos[0], f.pos[1], f.pos[0] - f.vel[0] * 2, f.pos[1] - f.vel[1] * 2)
        
    # Central Flare
    flare_alpha = py5.remap(py5.frame_count % (FPS * 2), 0, 20, 255, 0)
    if flare_alpha > 0:
        py5.no_stroke()
        for r in range(10, 0, -1):
            py5.fill(255, 255, 255, flare_alpha / (r + 1))
            py5.circle(SIZE[0]/2, SIZE[1]/2, r * 10)

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
        # Select preview frame (peak of a collision)
        mid = str(FRAMES_DIR / f"frame-{int(FPS * 0.2):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

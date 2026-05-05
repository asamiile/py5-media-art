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
STAR_COUNT = 1000
NUM_RAYS = 20
MAX_BOUNCES = 5

class Ray:
    def __init__(self, x, y, angle, hue):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([np.cos(angle), np.sin(angle)]) * 10
        self.hue = hue
        self.path = [self.pos.copy()]
        self.active = True
        self.bounces = 0
        
    def update(self):
        if not self.active: return
        
        self.pos += self.vel
        self.path.append(self.pos.copy())
        
        # Simple boundary bounce (simulating resonator)
        # Resonator is a circle at center
        cx, cy = SIZE[0]/2, SIZE[1]/2
        r_dist = np.sqrt((self.pos[0]-cx)**2 + (self.pos[1]-cy)**2)
        if r_dist > 350:
            # Reflect
            normal = (self.pos - np.array([cx, cy])) / r_dist
            self.vel = self.vel - 2 * np.dot(self.vel, normal) * normal
            # Nudge inside
            self.pos = np.array([cx, cy]) + normal * 349
            self.bounces += 1
            if self.bounces > MAX_BOUNCES:
                self.active = False

rays = []
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    global rays
    # 1. Update/Spawn Rays
    if py5.frame_count % 10 == 0:
        for _ in range(3):
            # Spawn at center with random angle and chromatic dispersion
            angle = np.random.uniform(0, py5.TWO_PI)
            # Dispersion: slight angle shift based on hue
            for h in [180, 200, 280]: # Cyan, Cobalt, Amethyst
                d_angle = angle + (h - 200) * 0.0005
                rays.append(Ray(SIZE[0]/2, SIZE[1]/2, d_angle, h))
                
    for r in rays:
        r.update()
        
    # Remove dead rays
    rays = [r for r in rays if r.active and len(r.path) < 1000]
    if len(rays) > 200:
        rays = rays[-200:]
        
    # 2. Draw Background
    # Persistence
    py5.fill(5, 5, 10, 20)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Rays
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    for r in rays:
        if len(r.path) < 2: continue
        py5.stroke(r.hue, 80, 100, 30)
        py5.stroke_weight(1.5)
        py5.line(r.path[-2][0], r.path[-2][1], r.path[-1][0], r.path[-1][1])
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

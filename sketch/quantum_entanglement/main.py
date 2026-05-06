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
NUM_PAIRS = 40

class ParticlePair:
    def __init__(self, index):
        self.index = index
        self.p1 = np.array([SIZE[0]/2, SIZE[1]/2], dtype=float)
        self.p2 = np.array([SIZE[0]/2, SIZE[1]/2], dtype=float)
        
        angle = np.random.uniform(0, py5.TWO_PI)
        self.v1 = np.array([np.cos(angle), np.sin(angle)]) * np.random.uniform(2, 5)
        self.v2 = -self.v1.copy()
        
        self.hue = np.random.choice([180, 220, 320]) # Cyan, Cobalt, Rose
        
    def update(self, t):
        # Noise-driven drift
        n1 = py5.noise(self.p1[0] * 0.005, self.p1[1] * 0.005, t * 0.5) * py5.TWO_PI * 2
        n2 = py5.noise(self.p2[0] * 0.005, self.p2[1] * 0.005, t * 0.5 + 10) * py5.TWO_PI * 2
        
        self.v1 += np.array([np.cos(n1), np.sin(n1)]) * 0.2
        self.v2 += np.array([np.cos(n2), np.sin(n2)]) * 0.2
        
        self.p1 += self.v1
        self.p2 += self.v2
        
        # Boundary bounce
        for p, v in [(self.p1, self.v1), (self.p2, self.v2)]:
            if p[0] < 0 or p[0] > SIZE[0]: v[0] *= -1
            if p[1] < 0 or p[1] > SIZE[1]: v[1] *= -1
            
    def draw(self, t):
        dist = np.linalg.norm(self.p1 - self.p2)
        alpha = py5.remap(dist, 0, 800, 150, 0)
        if alpha < 0: return
        
        # Pulse
        pulse = np.sin(t * py5.TWO_PI * 2 + self.index) * 0.5 + 0.5
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        py5.stroke(self.hue, 80, 100, alpha * pulse)
        py5.stroke_weight(1.5)
        py5.line(self.p1[0], self.p1[1], self.p2[0], self.p2[1])
        
        # Particle heads
        py5.no_stroke()
        py5.fill(self.hue, 50, 100, alpha)
        py5.circle(self.p1[0], self.p1[1], 3)
        py5.circle(self.p2[0], self.p2[1], 3)
        
        py5.color_mode(py5.RGB, 255, 255, 255, 255)

pairs = [ParticlePair(i) for i in range(NUM_PAIRS)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background
    # Persistence
    py5.fill(5, 5, 10, 25)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 2. Draw Pairs
    py5.blend_mode(py5.ADD)
    for p in pairs:
        p.update(t)
        p.draw(t)
    py5.blend_mode(py5.BLEND)

    # 3. Capture
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

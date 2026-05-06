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
NUM_CELLS = 12

class Cell:
    def __init__(self, x, y, size):
        self.pos = np.array([x, y], dtype=float)
        self.size = size
        self.vertices = 40
        self.hue = np.random.uniform(180, 320) # Cyan to Rose
        self.phase = np.random.uniform(0, py5.TWO_PI)
        self.split_timer = np.random.randint(60, 180)
        self.burst = 0
        
    def update(self, t):
        # Drift
        n_x = py5.noise(self.pos[0] * 0.01, self.pos[1] * 0.01, t * 2) - 0.5
        n_y = py5.noise(self.pos[0] * 0.01, self.pos[1] * 0.01, t * 2 + 10) - 0.5
        self.pos += np.array([n_x, n_y]) * 5
        
        # Split logic
        self.split_timer -= 1
        if self.split_timer <= 0:
            self.burst = 1.0
            self.split_timer = np.random.randint(120, 300)
            self.hue = (self.hue + 60) % 360
            
        self.burst *= 0.92
        
    def draw(self, t):
        py5.push_matrix()
        py5.translate(*self.pos)
        
        py5.begin_shape()
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        
        # Membrane oscillation
        for i in range(self.vertices):
            angle = i * py5.TWO_PI / self.vertices
            n = py5.noise(np.cos(angle) + self.pos[0]*0.01, np.sin(angle) + self.pos[1]*0.01, t * 5)
            r = self.size + n * 30 + self.burst * 50
            
            x = np.cos(angle) * r
            y = np.sin(angle) * r
            
            py5.fill(self.hue, 50, 100, 10 + self.burst * 40)
            py5.stroke(self.hue, 80, 100, 40 + self.burst * 60)
            py5.stroke_weight(1 + self.burst * 2)
            py5.vertex(x, y)
            
        py5.end_shape(py5.CLOSE)
        
        # Core
        py5.no_stroke()
        py5.fill(self.hue, 20, 100, 20)
        py5.circle(0, 0, self.size * 0.4)
        
        py5.color_mode(py5.RGB, 255, 255, 255, 255)
        py5.pop_matrix()

cells = []
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    # Init cells
    for _ in range(NUM_CELLS):
        cells.append(Cell(np.random.uniform(200, SIZE[0]-200), np.random.uniform(200, SIZE[1]-200), np.random.uniform(40, 80)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background
    py5.background(5, 5, 10)
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 2. Draw Cells
    py5.blend_mode(py5.ADD)
    for c in cells:
        c.update(t)
        c.draw(t)
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

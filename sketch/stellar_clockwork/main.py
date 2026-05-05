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
NUM_TRACERS = 6

class EpicycleTracer:
    def __init__(self, index):
        self.index = index
        self.radii = [150, 100, 50, 25]
        self.speeds = [
            0.01 * (index + 1),
            0.03 * (index + 2),
            -0.07 * (index + 1),
            0.15 * (index + 0.5)
        ]
        self.angles = [np.random.uniform(0, py5.TWO_PI) for _ in range(4)]
        self.path = []
        self.color_type = index % 3 # 0: Gold, 1: Silver, 2: Copper
        
    def update(self):
        cx, cy = SIZE[0]/2, SIZE[1]/2
        for i in range(4):
            self.angles[i] += self.speeds[i]
            cx += np.cos(self.angles[i]) * self.radii[i]
            cy += np.sin(self.angles[i]) * self.radii[i]
        
        self.path.append((cx, cy))
        if len(self.path) > 100:
            self.path.pop(0)
            
    def draw(self):
        if len(self.path) < 2: return
        
        # Spectral colors
        if self.color_type == 0: # Gold
            c = (255, 200, 50)
        elif self.color_type == 1: # Silver
            c = (200, 200, 255)
        else: # Copper
            c = (255, 120, 50)
            
        py5.no_fill()
        py5.stroke_weight(1.5)
        
        # Draw path with fading alpha
        for i in range(1, len(self.path)):
            alpha = py5.remap(i, 0, len(self.path), 0, 150)
            py5.stroke(*c, alpha)
            p1 = self.path[i-1]
            p2 = self.path[i]
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
        # Glowing head
        py5.no_stroke()
        py5.fill(*c, 200)
        py5.circle(self.path[-1][0], self.path[-1][1], 3)

tracers = [EpicycleTracer(i) for i in range(NUM_TRACERS)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(60, 180)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # 1. Update
    for t in tracers:
        t.update()
        
    # 2. Draw Background (Persistence)
    # We want a very slight fade to build up the paths
    py5.fill(5, 5, 10, 15)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Stars (draw every frame but they will persist/blur slightly)
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Tracers
    py5.blend_mode(py5.ADD)
    for t in tracers:
        t.draw()
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

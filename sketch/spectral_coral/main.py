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

class Branch:
    def __init__(self, x, y, angle, length, depth):
        self.x1, self.y1 = x, y
        self.x2 = x + np.cos(angle) * length
        self.y2 = y + np.sin(angle) * length
        self.angle = angle
        self.length = length
        self.depth = depth
        self.children = []
        self.pulse = 0
        
        if depth < 6:
            num_children = np.random.randint(1, 4)
            for _ in range(num_children):
                new_angle = angle + np.random.uniform(-0.6, 0.6)
                new_length = length * np.random.uniform(0.7, 0.9)
                self.children.append(Branch(self.x2, self.y2, new_angle, new_length, depth + 1))
                
    def update(self, t):
        # Pulse travels from root to tips
        # t is 0-1, pulse logic
        self.pulse = np.sin(t * py5.TWO_PI * 2 - self.depth * 0.5) * 0.5 + 0.5
        for c in self.children:
            c.update(t)
            
    def draw(self):
        # Base branch
        py5.stroke(50, 50, 70, 150)
        py5.stroke_weight(py5.remap(self.depth, 0, 6, 8, 1))
        py5.line(self.x1, self.y1, self.x2, self.y2)
        
        # Spectral pulse
        if self.pulse > 0.3:
            p_alpha = py5.remap(self.pulse, 0.3, 1, 0, 200)
            if self.depth % 3 == 0: # Cyan
                py5.stroke(0, 255, 255, p_alpha)
            elif self.depth % 3 == 1: # Lime
                py5.stroke(150, 255, 50, p_alpha)
            else: # Amethyst
                py5.stroke(200, 100, 255, p_alpha)
            
            py5.stroke_weight(py5.remap(self.depth, 0, 6, 4, 0.5))
            py5.line(self.x1, self.y1, self.x2, self.y2)
            
        for c in self.children:
            c.draw()

roots = []
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Grow roots
    for _ in range(6):
        x = np.random.uniform(200, SIZE[0]-200)
        y = np.random.uniform(SIZE[1]*0.7, SIZE[1])
        roots.append(Branch(x, y, -py5.HALF_PI + np.random.uniform(-0.5, 0.5), 150, 0))
        
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Update
    for r in roots:
        r.update(t)
        
    # 2. Draw Background
    py5.background(2, 2, 8)
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Coral
    py5.blend_mode(py5.ADD)
    for r in roots:
        r.draw()
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
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

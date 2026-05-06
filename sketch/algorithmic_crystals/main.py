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
NUM_CRYSTALS = 8

class Crystal:
    def __init__(self, x, y, z, size):
        self.pos = np.array([x, y, z], dtype=float)
        self.size = size
        self.rot = np.random.uniform(0, py5.TWO_PI, 3)
        self.rot_v = np.random.uniform(-0.01, 0.01, 3)
        self.hue = np.random.choice([50, 150, 280]) # Gold, Green, Amethyst
        
    def draw(self, t):
        py5.push_matrix()
        py5.translate(*self.pos)
        py5.rotate_x(self.rot[0] + t * py5.TWO_PI)
        py5.rotate_y(self.rot[1] + t * py5.TWO_PI * 0.5)
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        
        # Recursive lattice
        for i in range(3):
            s = self.size * (1 - i * 0.2)
            pulse = np.sin(t * py5.TWO_PI * 2 + i) * 0.5 + 0.5
            
            py5.fill(self.hue, 50, 80 + pulse * 20, 80)
            py5.stroke(self.hue, 80, 100, 150)
            py5.stroke_weight(1)
            
            # Draw octahedron-like crystal
            py5.begin_shape(py5.TRIANGLES)
            # Top
            py5.vertex(0, -s, 0)
            py5.vertex(s, 0, s)
            py5.vertex(-s, 0, s)
            
            py5.vertex(0, -s, 0)
            py5.vertex(-s, 0, s)
            py5.vertex(-s, 0, -s)
            
            py5.vertex(0, -s, 0)
            py5.vertex(-s, 0, -s)
            py5.vertex(s, 0, -s)
            
            py5.vertex(0, -s, 0)
            py5.vertex(s, 0, -s)
            py5.vertex(s, 0, s)
            
            # Bottom
            py5.vertex(0, s, 0)
            py5.vertex(s, 0, s)
            py5.vertex(-s, 0, s)
            
            py5.vertex(0, s, 0)
            py5.vertex(-s, 0, s)
            py5.vertex(-s, 0, -s)
            
            py5.vertex(0, s, 0)
            py5.vertex(-s, 0, -s)
            py5.vertex(s, 0, -s)
            
            py5.vertex(0, s, 0)
            py5.vertex(s, 0, -s)
            py5.vertex(s, 0, s)
            py5.end_shape()
            
        py5.color_mode(py5.RGB, 255, 255, 255, 255)
        py5.pop_matrix()

crystals = []
stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-1000, 1000), np.random.uniform(-2000, 2000), np.random.uniform(50, 150)))
        
    # Init crystals
    for _ in range(NUM_CRYSTALS):
        crystals.append(Crystal(np.random.uniform(-400, 400), np.random.uniform(-300, 300), np.random.uniform(-400, 400), np.random.uniform(60, 120)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background & Lighting
    py5.background(5, 5, 10)
    py5.ambient_light(50, 50, 80)
    py5.directional_light(200, 200, 255, 0.5, 1, -0.5)
    
    # Camera
    angle = py5.frame_count * 0.005
    py5.camera(1000 * np.cos(angle), -600, 1000 * np.sin(angle), 0, 0, 0, 0, 1, 0)
    
    # 2. Draw Stars
    py5.no_stroke()
    for sx, sy, sz, s_alpha in stars:
        py5.push_matrix()
        py5.translate(sx, sy, sz)
        py5.fill(255, s_alpha)
        py5.box(2)
        py5.pop_matrix()

    # 3. Draw Crystals
    for c in crystals:
        c.draw(t)
        
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

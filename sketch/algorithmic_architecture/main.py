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
CITY_SIZE = 1000

class Building:
    def __init__(self, x, z, w, d, h, hue):
        self.x, self.z = x, z
        self.w, self.d = w, d
        self.h = h
        self.hue = hue
        
    def draw(self, t):
        py5.push_matrix()
        py5.translate(self.x, -self.h/2, self.z)
        
        # Spectral pulse on the building
        pulse = np.sin(t * py5.TWO_PI + self.x * 0.01) * 0.5 + 0.5
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        py5.fill(self.hue, 30, 20 + pulse * 10, 100)
        py5.stroke(self.hue, 50, 40 + pulse * 20, 150)
        py5.stroke_weight(0.5)
        py5.box(self.w, self.h, self.d)
        
        # Windows/Lights
        if pulse > 0.8:
            py5.no_stroke()
            py5.fill(self.hue, 80, 100, (pulse - 0.8) * 500)
            py5.box(self.w + 1, self.h * 0.1, self.d + 1)
            
        py5.color_mode(py5.RGB, 255, 255, 255, 255)
        py5.pop_matrix()

buildings = []
stars = []

def build_city(x, z, w, d, depth):
    if depth > 4 or (depth > 1 and np.random.random() < 0.3):
        h = np.random.uniform(50, 400) * (5 - depth) * 0.5
        hue = np.random.choice([190, 280]) # Cyan, Amethyst
        buildings.append(Building(x, z, w * 0.9, d * 0.9, h, hue))
        return
    
    nw, nd = w/2, d/2
    build_city(x - nw/2, z - nd/2, nw, nd, depth + 1)
    build_city(x + nw/2, z - nd/2, nw, nd, depth + 1)
    build_city(x - nw/2, z + nd/2, nw, nd, depth + 1)
    build_city(x + nw/2, z + nd/2, nw, nd, depth + 1)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-1000, 1000), np.random.uniform(-2000, 2000), np.random.uniform(50, 150)))
        
    # Grow city
    build_city(0, 0, CITY_SIZE, CITY_SIZE, 0)
    
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background & Lighting
    py5.background(5, 5, 10)
    py5.ambient_light(40, 40, 60)
    py5.directional_light(150, 150, 255, 0.5, 1, -0.5)
    
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

    # 3. Draw City
    for b in buildings:
        b.draw(t)
        
    # Data Highways (Horizontal filaments)
    py5.blend_mode(py5.ADD)
    for _ in range(5):
        h_y = -np.random.uniform(0, 300)
        h_z = np.random.uniform(-CITY_SIZE/2, CITY_SIZE/2)
        py5.stroke(0, 255, 255, 100)
        py5.stroke_weight(1)
        py5.line(-CITY_SIZE/2, h_y, h_z, CITY_SIZE/2, h_y, h_z)
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

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
NUM_LAYERS = 12

class Layer:
    def __init__(self, index):
        self.index = index
        self.y_base = py5.remap(index, 0, NUM_LAYERS, SIZE[1]*0.1, SIZE[1]*0.9)
        self.noise_seed = np.random.randint(0, 10000)
        self.color_type = index % 3 # 0: Emerald, 1: Amethyst, 2: Gold
        
    def draw(self, t):
        py5.push_matrix()
        
        # Spectral colors
        if self.color_type == 0: # Emerald
            base_c = (50, 255, 150)
        elif self.color_type == 1: # Amethyst
            base_c = (180, 80, 255)
        else: # Gold
            base_c = (255, 200, 50)
            
        # Draw layer body with mineral texture
        py5.no_stroke()
        py5.fill(*base_c, 30) # Low alpha for layering
        
        py5.begin_shape()
        py5.vertex(0, SIZE[1])
        
        steps = 100
        for i in range(steps + 1):
            x = py5.remap(i, 0, steps, 0, SIZE[0])
            # Multi-octave noise for the ridge
            n1 = py5.noise(x * 0.002, self.index * 0.5, t * 0.5)
            n2 = py5.noise(x * 0.01, self.index * 0.7, t * 0.2) * 0.3
            y_offset = (n1 + n2) * 200 - 100
            py5.vertex(x, self.y_base + y_offset)
            
        py5.vertex(SIZE[0], SIZE[1])
        py5.end_shape(py5.CLOSE)
        
        # Draw spectral edge
        py5.no_fill()
        py5.stroke(*base_c, 150)
        py5.stroke_weight(2)
        py5.begin_shape()
        for i in range(steps + 1):
            x = py5.remap(i, 0, steps, 0, SIZE[0])
            n1 = py5.noise(x * 0.002, self.index * 0.5, t * 0.5)
            n2 = py5.noise(x * 0.01, self.index * 0.7, t * 0.2) * 0.3
            y_offset = (n1 + n2) * 200 - 100
            py5.vertex(x, self.y_base + y_offset)
        py5.end_shape()
        
        # Subtle glow highlight
        py5.stroke(*base_c, 50)
        py5.stroke_weight(5)
        py5.begin_shape()
        for i in range(steps + 1):
            x = py5.remap(i, 0, steps, 0, SIZE[0])
            n1 = py5.noise(x * 0.002, self.index * 0.5, t * 0.5)
            n2 = py5.noise(x * 0.01, self.index * 0.7, t * 0.2) * 0.3
            y_offset = (n1 + n2) * 200 - 100
            py5.vertex(x, self.y_base + y_offset - 2)
        py5.end_shape()
        
        py5.pop_matrix()

layers = [Layer(i) for i in range(NUM_LAYERS)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 180)))
        
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

    # 2. Draw Layers
    # We draw from back to front (bottom layers first in index or base_y)
    # Actually, layers stack on top of each other
    for l in layers:
        l.draw(t)

    # 3. Grain Post-Process
    # We can use a simple noise overlay to create mineral grain
    py5.blend_mode(py5.MULTIPLY)
    for _ in range(200):
        gx = np.random.uniform(0, SIZE[0])
        gy = np.random.uniform(0, SIZE[1])
        py5.fill(200, 200, 255, 10)
        py5.circle(gx, gy, 1)
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

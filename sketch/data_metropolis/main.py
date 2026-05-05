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
NUM_PACKETS = 400
BLOCKS = []

def subdivide(x, y, w, h, depth):
    if depth > 4 or (depth > 1 and np.random.rand() < 0.3):
        BLOCKS.append({"rect": (x, y, w, h), "height": np.random.uniform(20, 200), "color": np.random.randint(0, 3)})
        return
    
    nw = w / 2
    nh = h / 2
    subdivide(x, y, nw, nh, depth + 1)
    subdivide(x + nw, y, nw, nh, depth + 1)
    subdivide(x, y + nh, nw, nh, depth + 1)
    subdivide(x + nw, y + nh, nw, nh, depth + 1)

class Packet:
    def __init__(self):
        self.pos = np.array([np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])])
        self.vel = np.array([0.0, 0.0])
        self.color = np.random.randint(0, 3)
        self.speed = np.random.uniform(2, 6)
        self.dir = np.random.choice([0, 1]) # 0: x, 1: y
        self.sign = np.random.choice([-1, 1])
        
    def update(self):
        if self.dir == 0:
            self.pos[0] += self.speed * self.sign
        else:
            self.pos[1] += self.speed * self.sign
            
        # Reset if OOB
        if self.pos[0] < 0 or self.pos[0] > SIZE[0] or self.pos[1] < 0 or self.pos[1] > SIZE[1]:
            self.pos = np.array([np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])])
            self.dir = np.random.choice([0, 1])
            self.sign = np.random.choice([-1, 1])

packets = [Packet() for _ in range(NUM_PACKETS)]
stars = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.smooth(8)
    
    # Subdivide blocks
    subdivide(100, 100, SIZE[0]-200, SIZE[1]-200, 0)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1]), np.random.uniform(0.5, 2.5), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    # 1. Update Packets
    for p in packets:
        p.update()
        
    # 2. Draw Background
    py5.background(5, 5, 10)
    
    # Stars
    py5.no_stroke()
    for sx, sy, s_size, s_alpha in stars:
        py5.fill(255, s_alpha + np.sin(py5.frame_count * 0.1 + sx) * 40)
        py5.circle(sx, sy, s_size)

    # 3. Draw Buildings (Blocks)
    # Simple top-down with pseudo-3D offset
    for b in BLOCKS:
        x, y, w, h = b["rect"]
        z = b["height"]
        
        # Draw side face (shadowed)
        py5.fill(20, 20, 40, 200)
        py5.no_stroke()
        # Side face offset slightly to create 3D look
        offset = z * 0.1
        py5.begin_shape()
        py5.vertex(x, y)
        py5.vertex(x + w, y)
        py5.vertex(x + w + offset, y - offset)
        py5.vertex(x + offset, y - offset)
        py5.end_shape()
        
        # Draw top face
        py5.fill(40, 40, 60, 230)
        py5.stroke(100, 100, 150, 50)
        py5.rect(x, y, w, h)
        
        # Edge glow
        if b["color"] == 0: # Pink
            py5.stroke(255, 50, 150, 150)
        elif b["color"] == 1: # Lime
            py5.stroke(150, 255, 50, 150)
        else: # Blue
            py5.stroke(50, 150, 255, 150)
        py5.stroke_weight(1.5)
        py5.no_fill()
        py5.rect(x, y, w, h)

    # 4. Draw Packets (Data)
    py5.blend_mode(py5.ADD)
    for p in packets:
        if p.color == 0: py5.stroke(255, 50, 150, 200)
        elif p.color == 1: py5.stroke(150, 255, 50, 200)
        else: py5.stroke(50, 150, 255, 200)
        
        py5.stroke_weight(2)
        # Draw a small streak
        tail_len = p.speed * 2
        if p.dir == 0:
            py5.line(p.pos[0], p.pos[1], p.pos[0] - p.sign * tail_len, p.pos[1])
        else:
            py5.line(p.pos[0], p.pos[1], p.pos[0], p.pos[1] - p.sign * tail_len)
            
    py5.blend_mode(py5.BLEND)

    # 5. Capture
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

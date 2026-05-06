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
STAR_COUNT = 800
NUM_NODES = 40
CONN_DIST = 300

class Node:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z], dtype=float)
        self.pulse = 0
        self.connections = []
        
    def draw(self, t):
        py5.push_matrix()
        py5.translate(*self.pos)
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        hue = py5.remap(self.pulse, 0, 1, 190, 280) # Cyan to Amethyst
        py5.fill(hue, 60, 100, 10 + self.pulse * 40)
        py5.no_stroke()
        py5.sphere(5 + self.pulse * 10)
        
        py5.color_mode(py5.RGB, 255, 255, 255, 255)
        py5.pop_matrix()
        
        self.pulse *= 0.95

class Pulse:
    def __init__(self, start_node, end_node):
        self.start = start_node
        self.end = end_node
        self.progress = 0
        self.speed = 0.02
        
    def update(self):
        self.progress += self.speed
        if self.progress >= 1:
            self.end.pulse = 1
            return True
        return False
        
    def draw(self):
        p = self.start.pos + (self.end.pos - self.start.pos) * self.progress
        py5.push_matrix()
        py5.translate(*p)
        py5.fill(0, 255, 255, 200)
        py5.no_stroke()
        py5.sphere(3)
        py5.pop_matrix()

nodes = []
pulses = []
stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-1000, 1000), np.random.uniform(-2000, 2000), np.random.uniform(50, 150)))
        
    # Init nodes
    for _ in range(NUM_NODES):
        nodes.append(Node(np.random.uniform(-500, 500), np.random.uniform(-300, 300), np.random.uniform(-500, 500)))
        
    # Build connections
    for i in range(NUM_NODES):
        for j in range(i + 1, NUM_NODES):
            if np.linalg.norm(nodes[i].pos - nodes[j].pos) < CONN_DIST:
                nodes[i].connections.append(nodes[j])
                nodes[j].connections.append(nodes[i])
                
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    global pulses
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

    # 3. Update/Draw Pulses
    if py5.frame_count % 10 == 0:
        start_node = np.random.choice(nodes)
        if start_node.connections:
            end_node = np.random.choice(start_node.connections)
            pulses.append(Pulse(start_node, end_node))
            
    new_pulses = []
    for p in pulses:
        if not p.update():
            new_pulses.append(p)
            p.draw()
    pulses = new_pulses

    # 4. Draw Nodes & Connections
    for n in nodes:
        n.draw(t)
        for target in n.connections:
            py5.stroke(255, 50)
            py5.stroke_weight(0.5)
            py5.line(*n.pos, *target.pos)

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

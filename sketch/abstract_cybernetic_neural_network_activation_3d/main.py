from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Network structure
LAYERS = 6
NODES_PER_LAYER = [15, 20, 25, 20, 15, 10]
LAYER_DIST = 400

nodes = []
edges = []
pulses = []

class Node:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.activation = 0.0

class Edge:
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2

class Pulse:
    def __init__(self, edge):
        self.edge = edge
        self.progress = 0.0
        self.speed = random.uniform(0.02, 0.05)

# Initialize network
for l in range(LAYERS):
    layer_nodes = []
    x = (l - LAYERS/2 + 0.5) * LAYER_DIST
    num_nodes = NODES_PER_LAYER[l]
    
    for i in range(num_nodes):
        # Position in a circle or randomly scattered in YZ plane
        angle = py5.remap(i, 0, num_nodes, 0, py5.PI * 2)
        radius = random.uniform(100, 300)
        y = math.cos(angle) * radius
        z = math.sin(angle) * radius
        layer_nodes.append(Node(x, y, z))
    nodes.append(layer_nodes)

# Create edges between adjacent layers
for l in range(LAYERS - 1):
    for n1 in nodes[l]:
        # Connect to random nodes in next layer
        targets = random.sample(nodes[l+1], min(5, len(nodes[l+1])))
        for n2 in targets:
            edges.append(Edge(n1, n2))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(10, 15, 25)
    
    t = py5.frame_count
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -500)
    
    py5.rotate_y(t * 0.005)
    py5.rotate_x(py5.sin(t * 0.01) * 0.2)
    
    # Randomly spawn new pulses at layer 0
    if random.random() < 0.2:
        layer0_node = random.choice(nodes[0])
        possible_edges = [e for e in edges if e.n1 == layer0_node]
        if possible_edges:
            pulses.append(Pulse(random.choice(possible_edges)))

    # Update pulses
    for p in pulses[:]:
        p.progress += p.speed
        if p.progress >= 1.0:
            p.edge.n2.activation = 1.0
            pulses.remove(p)
            # Propagate to next layer occasionally
            possible_next_edges = [e for e in edges if e.n1 == p.edge.n2]
            if possible_next_edges and random.random() < 0.6:
                pulses.append(Pulse(random.choice(possible_next_edges)))

    # Update node activations (decay)
    for layer in nodes:
        for n in layer:
            n.activation = max(0, n.activation - 0.05)
            # Baseline small activation
            n.activation = max(n.activation, 0.1)

    py5.stroke_weight(2)
    
    # Draw edges
    py5.stroke(200, 40, 40, 50)
    py5.begin_shape(py5.LINES)
    for e in edges:
        py5.vertex(e.n1.x, e.n1.y, e.n1.z)
        py5.vertex(e.n2.x, e.n2.y, e.n2.z)
    py5.end_shape()
    
    # Draw pulses
    py5.stroke_weight(4)
    py5.stroke(180, 80, 100)
    for p in pulses:
        x = py5.lerp(p.edge.n1.x, p.edge.n2.x, p.progress)
        y = py5.lerp(p.edge.n1.y, p.edge.n2.y, p.progress)
        z = py5.lerp(p.edge.n1.z, p.edge.n2.z, p.progress)
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.line(-5, -5, -5, 5, 5, 5) # small spark
        py5.pop_matrix()
        
    # Draw nodes
    py5.no_stroke()
    for layer in nodes:
        for n in layer:
            hue = (200 + n.activation * 60) % 360
            size = 10 + n.activation * 20
            py5.fill(hue, 80, 100, 150 + n.activation * 105)
            
            py5.push_matrix()
            py5.translate(n.x, n.y, n.z)
            # Avoid py5.sphere for perf, draw simple boxes or ellipses
            py5.box(size)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

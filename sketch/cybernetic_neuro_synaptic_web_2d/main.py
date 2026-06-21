from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_NODES = 400
NUM_SIGNALS = 200

nodes = []
edges = []
signals = []

class Node:
    def __init__(self, i):
        self.id = i
        self.pos = np.array([random.uniform(0, SIZE[0]), random.uniform(0, SIZE[1])])
        self.activation = 0.0
        self.neighbors = []

class Signal:
    def __init__(self, start_node, end_node):
        self.start = start_node
        self.end = end_node
        self.progress = 0.0
        self.speed = random.uniform(0.01, 0.05)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5)
    py5.blend_mode(py5.ADD)
    
    for i in range(NUM_NODES):
        nodes.append(Node(i))
        
    for i in range(NUM_NODES):
        for j in range(i + 1, NUM_NODES):
            dist = np.linalg.norm(nodes[i].pos - nodes[j].pos)
            if dist < 200:
                nodes[i].neighbors.append(nodes[j])
                nodes[j].neighbors.append(nodes[i])
                edges.append((nodes[i], nodes[j], dist))
                
    for _ in range(NUM_SIGNALS):
        spawn_signal()

def spawn_signal():
    start = random.choice(nodes)
    if start.neighbors:
        end = random.choice(start.neighbors)
        signals.append(Signal(start, end))

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Draw edges
    py5.stroke(200, 80, 20, 10)
    py5.stroke_weight(1)
    for e in edges:
        py5.line(e[0].pos[0], e[0].pos[1], e[1].pos[0], e[1].pos[1])
        
    # Update and draw signals
    active_signals = []
    py5.no_stroke()
    for s in signals:
        s.progress += s.speed
        if s.progress >= 1.0:
            s.end.activation = 1.0
            if random.random() > 0.1 and s.end.neighbors:
                next_node = random.choice(s.end.neighbors)
                active_signals.append(Signal(s.end, next_node))
            else:
                spawn_signal()
        else:
            active_signals.append(s)
            p = s.start.pos + (s.end.pos - s.start.pos) * s.progress
            py5.fill(180, 80, 100, 80)
            py5.circle(p[0], p[1], 4)
            
    signals.clear()
    signals.extend(active_signals)
    
    # Update and draw nodes
    for n in nodes:
        if n.activation > 0:
            n.activation -= 0.05
            py5.fill(180, 80, 100, n.activation * 100)
            py5.circle(n.pos[0], n.pos[1], 8 + n.activation * 10)

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
            
        import os
        os._exit(0)

py5.run_sketch()

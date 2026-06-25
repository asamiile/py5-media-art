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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Neuron parameters
nodes = []
edges = []

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.pulse = 0
        self.base_size = py5.random(5, 15)
        
class Edge:
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2
        self.signals = []
        
    def add_signal(self):
        self.signals.append(0.0)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)
    
    # Generate nodes
    num_nodes = 300
    for i in range(num_nodes):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        nodes.append(Node(i, x, y))
        
    # Generate edges (connect nearby)
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            dist = py5.dist(nodes[i].x, nodes[i].y, nodes[j].x, nodes[j].y)
            if dist < 150 and py5.random() < 0.3:
                edges.append(Edge(nodes[i], nodes[j]))

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(240, 90, 5, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Inject signals
    if py5.frame_count % 5 == 0:
        if len(edges) > 0:
            random_edge = random.choice(edges)
            random_edge.add_signal()
            random_edge.n1.pulse = 1.0
            
    # Update and draw edges
    py5.stroke_weight(1.5)
    for e in edges:
        # Base edge
        py5.stroke(260, 60, 30, 100)
        py5.line(e.n1.x, e.n1.y, e.n2.x, e.n2.y)
        
        # Signals
        new_signals = []
        for s in e.signals:
            s += 0.05
            if s <= 1.0:
                new_signals.append(s)
                # Draw signal
                sx = py5.lerp(e.n1.x, e.n2.x, s)
                sy = py5.lerp(e.n1.y, e.n2.y, s)
                
                py5.no_stroke()
                py5.fill(190, 80, 100, 255)
                py5.circle(sx, sy, 8)
                
                # Activate target node when reached
                if s >= 0.95:
                    e.n2.pulse = 1.0
                    # 10% chance to propagate
                    if py5.random() < 0.1:
                        # Find connected edges
                        connected = [other for other in edges if other.n1 == e.n2 or other.n2 == e.n2]
                        if connected:
                            random.choice(connected).add_signal()
        e.signals = new_signals
        
    # Draw nodes
    py5.no_stroke()
    for n in nodes:
        # Drift slightly
        n.x += (py5.os_noise(n.x * 0.01, n.y * 0.01, py5.frame_count * 0.01) - 0.5) * 0.5
        n.y += (py5.os_noise(n.x * 0.01 + 100, n.y * 0.01 + 100, py5.frame_count * 0.01) - 0.5) * 0.5
        
        n.pulse = max(0, n.pulse - 0.05)
        size = n.base_size + n.pulse * 15
        
        # Glow
        if n.pulse > 0:
            py5.fill(200, 50, 100, 150 * n.pulse)
            py5.circle(n.x, n.y, size * 2)
            
        py5.fill(220, 80, 80 + 20 * n.pulse, 200)
        py5.circle(n.x, n.y, size)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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
            
        import os
        os._exit(0)

py5.run_sketch()

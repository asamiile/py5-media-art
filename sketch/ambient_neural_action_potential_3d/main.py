from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Neuron:
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z])
        self.connections = []
        
    def add_connection(self, other):
        if other not in self.connections:
            self.connections.append(other)
            other.connections.append(self)

neurons = []
edges = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Generate points
    for _ in range(200):
        x = py5.random(-400, 400)
        y = py5.random(-400, 400)
        z = py5.random(-400, 400)
        # Filter to make a sphere-ish shape
        if np.linalg.norm([x, y, z]) < 400:
            neurons.append(Neuron(x, y, z))
            
    # Connect nearest neighbors
    for n1 in neurons:
        dists = []
        for n2 in neurons:
            if n1 != n2:
                dist = np.linalg.norm(n1.pos - n2.pos)
                dists.append((dist, n2))
        
        dists.sort(key=lambda x: x[0])
        for i in range(min(3, len(dists))):
            n1.add_connection(dists[i][1])
            edges.append((n1, dists[i][1]))
            
    # Unique edges
    global unique_edges
    unique_edges = list(set(tuple(sorted((n1, n2), key=lambda x: id(x))) for n1, n2 in edges))

def draw():
    py5.background(220, 80, 10) # Dark deep blue/purple background
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.translate(py5.width/2, py5.height/2, -400)
    
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Draw faint connections
    py5.stroke(200, 50, 40, 20)
    py5.stroke_weight(1)
    py5.begin_shape(py5.LINES)
    for n1, n2 in unique_edges:
        py5.vertex(*n1.pos)
        py5.vertex(*n2.pos)
    py5.end_shape()
    
    # Action potentials
    # We'll use a continuous wave flowing across the network based on position
    
    for n1, n2 in unique_edges:
        # Distance of midpoint from center
        mid = (n1.pos + n2.pos) / 2
        d = np.linalg.norm(mid)
        
        # Flow from bottom to top
        flow = mid[1] * 0.01 - t * 20
        
        # Pulse is active when sine is near 1
        pulse = py5.sin(flow)
        
        if pulse > 0.8:
            intensity = py5.remap(pulse, 0.8, 1.0, 0, 100)
            py5.stroke(50, 80, 100, intensity)
            py5.stroke_weight(py5.remap(pulse, 0.8, 1.0, 1, 5))
            py5.line(n1.pos[0], n1.pos[1], n1.pos[2], n2.pos[0], n2.pos[1], n2.pos[2])

    # Draw neurons
    py5.no_stroke()
    for n in neurons:
        flow = n.pos[1] * 0.01 - t * 20
        pulse = py5.sin(flow)
        
        py5.push_matrix()
        py5.translate(*n.pos)
        if pulse > 0.8:
            intensity = py5.remap(pulse, 0.8, 1.0, 40, 100)
            py5.fill(50, 80, 100, intensity)
            py5.box(5)
        else:
            py5.fill(200, 50, 40, 40)
            py5.box(3)
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

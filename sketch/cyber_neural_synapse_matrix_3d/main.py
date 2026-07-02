from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
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

class Node:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.connections = []

class Spark:
    def __init__(self, start_node, end_node):
        self.start = start_node
        self.end = end_node
        self.progress = 0
        self.speed = random.uniform(0.02, 0.05)
        self.hue = random.choice([320, 200, 280])

nodes = []
sparks = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Generate nodes
    num_nodes = 200
    for _ in range(num_nodes):
        x = random.uniform(-400, 400)
        y = random.uniform(-400, 400)
        z = random.uniform(-400, 400)
        nodes.append(Node(x, y, z))
        
    # Connect nearest neighbors
    for n1 in nodes:
        distances = []
        for n2 in nodes:
            if n1 != n2:
                d = math.sqrt((n1.x-n2.x)**2 + (n1.y-n2.y)**2 + (n1.z-n2.z)**2)
                distances.append((d, n2))
        distances.sort(key=lambda x: x[0])
        # Connect to 3-5 closest
        for i in range(random.randint(3, 5)):
            if distances[i][0] < 200:
                n1.connections.append(distances[i][1])
                
    # Initial sparks
    for _ in range(150):
        start = random.choice(nodes)
        if start.connections:
            end = random.choice(start.connections)
            sparks.append(Spark(start, end))

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    
    # Draw connections
    py5.stroke(240, 60, 20, 40)
    py5.stroke_weight(1)
    py5.begin_shape(py5.LINES)
    for n1 in nodes:
        for n2 in n1.connections:
            py5.vertex(n1.x, n1.y, n1.z)
            py5.vertex(n2.x, n2.y, n2.z)
    py5.end_shape()
    
    # Draw nodes
    py5.no_stroke()
    for n in nodes:
        py5.fill(200, 80, 80, 100)
        py5.push_matrix()
        py5.translate(n.x, n.y, n.z)
        py5.sphere(3)
        py5.pop_matrix()
        
    # Update and draw sparks
    new_sparks = []
    for s in sparks:
        s.progress += s.speed
        if s.progress >= 1:
            # Spark reached end, create new spark from end node
            if s.end.connections:
                next_node = random.choice(s.end.connections)
                new_sparks.append(Spark(s.end, next_node))
        else:
            new_sparks.append(s)
            
            # Interpolate position
            px = s.start.x + (s.end.x - s.start.x) * s.progress
            py = s.start.y + (s.end.y - s.start.y) * s.progress
            pz = s.start.z + (s.end.z - s.start.z) * s.progress
            
            py5.fill(s.hue, 100, 100, 255)
            py5.push_matrix()
            py5.translate(px, py, pz)
            py5.sphere(5)
            
            # Glow effect
            py5.fill(s.hue, 100, 100, 50)
            py5.sphere(15)
            py5.pop_matrix()
            
    sparks.clear()
    sparks.extend(new_sparks)
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

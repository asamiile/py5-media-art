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

NUM_NODES = 300
CONNECTION_DIST = SIZE[1] * 0.15

class Node:
    def __init__(self, id):
        self.id = id
        self.x = random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        self.y = random.uniform(SIZE[1] * 0.1, SIZE[1] * 0.9)
        self.energy = random.uniform(0, 1)
        self.connections = []
        
    def add_connection(self, other_node):
        if other_node not in self.connections:
            self.connections.append(other_node)

class Spark:
    def __init__(self, start_node, end_node):
        self.start = start_node
        self.end = end_node
        self.progress = 0
        self.speed = random.uniform(0.01, 0.03)
        self.hue = random.uniform(40, 60) # Yellow/Orange
        
    def update(self):
        self.progress += self.speed
        return self.progress >= 1.0
        
    def draw(self):
        x = py5.lerp(self.start.x, self.end.x, self.progress)
        y = py5.lerp(self.start.y, self.end.y, self.progress)
        
        py5.no_stroke()
        py5.fill(self.hue, 80, 100, 200)
        py5.circle(x, y, 6)
        
        # Add a slight glow
        py5.fill(self.hue, 100, 100, 50)
        py5.circle(x, y, 16)

nodes = []
sparks = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize nodes
    for i in range(NUM_NODES):
        nodes.append(Node(i))
        
    # Build connections
    for i in range(NUM_NODES):
        for j in range(i + 1, NUM_NODES):
            dx = nodes[i].x - nodes[j].x
            dy = nodes[i].y - nodes[j].y
            dist_sq = dx*dx + dy*dy
            if dist_sq < CONNECTION_DIST * CONNECTION_DIST:
                nodes[i].add_connection(nodes[j])
                nodes[j].add_connection(nodes[i])

def draw():
    # Trail effect
    py5.fill(0, 0, 5, 40)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Draw connections faintly
    py5.stroke(220, 50, 100, 20)
    py5.stroke_weight(1)
    for n in nodes:
        for c in n.connections:
            if n.id < c.id: # Draw once per pair
                py5.line(n.x, n.y, c.x, c.y)
                
    # Update and draw nodes
    for n in nodes:
        pulse = (py5.sin(py5.frame_count * 0.05 + n.energy * 10) + 1) * 0.5
        
        # Fire sparks randomly based on pulse
        if pulse > 0.9 and random.random() < 0.1 and len(n.connections) > 0:
            target = random.choice(n.connections)
            sparks.append(Spark(n, target))
            
        py5.no_stroke()
        py5.fill(200, 60, 100, 50 + pulse * 100)
        py5.circle(n.x, n.y, 4 + pulse * 6)
        
    # Update and draw sparks
    active_sparks = []
    for s in sparks:
        if not s.update():
            s.draw()
            active_sparks.append(s)
        else:
            # When spark reaches end, maybe trigger another
            if random.random() < 0.6 and len(s.end.connections) > 0:
                target = random.choice(s.end.connections)
                active_sparks.append(Spark(s.end, target))
                
    sparks.clear()
    sparks.extend(active_sparks)
    
    # Initially seed some sparks if none exist
    if len(sparks) < 20 and py5.frame_count % 10 == 0:
        n = random.choice(nodes)
        if len(n.connections) > 0:
            sparks.append(Spark(n, random.choice(n.connections)))

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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

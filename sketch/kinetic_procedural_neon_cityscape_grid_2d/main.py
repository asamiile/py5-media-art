from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

blocks = []
streets = [] 
particles = []

class Block:
    def __init__(self, x, y, w, h, depth):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.depth = depth

def subdivide(block):
    if block.depth > 7:
        blocks.append(block)
        return
        
    if block.w < 100 or block.h < 100:
        blocks.append(block)
        return
        
    if block.w > block.h:
        split_ratio = np.random.uniform(0.3, 0.7)
        split_x = block.w * split_ratio
        
        b1 = Block(block.x, block.y, split_x, block.h, block.depth + 1)
        b2 = Block(block.x + split_x, block.y, block.w - split_x, block.h, block.depth + 1)
        
        streets.append(((block.x + split_x, block.y), (block.x + split_x, block.y + block.h)))
    else:
        split_ratio = np.random.uniform(0.3, 0.7)
        split_y = block.h * split_ratio
        
        b1 = Block(block.x, block.y, block.w, split_y, block.depth + 1)
        b2 = Block(block.x, block.y + split_y, block.w, block.h - split_y, block.depth + 1)
        
        streets.append(((block.x, block.y + split_y), (block.x + block.w, block.y + split_y)))
        
    subdivide(b1)
    subdivide(b2)

graph = {}

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    root = Block(0, 0, SIZE[0], SIZE[1], 0)
    subdivide(root)
    
    for (p1, p2) in streets:
        if p1 not in graph: graph[p1] = []
        if p2 not in graph: graph[p2] = []
        graph[p1].append(p2)
        graph[p2].append(p1)
        
    nodes = list(graph.keys())
    
    num_particles = 15000
    for _ in range(num_particles):
        node = random.choice(nodes)
        if not graph[node]: continue
        target = random.choice(graph[node])
        c = random.choice([
            (0, 255, 255), 
            (255, 0, 150),  
            (200, 100, 255) 
        ])
        particles.append([node[0], node[1], target[0], target[1], random.uniform(5.0, 15.0), c])
        
def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    py5.stroke(30, 30, 50, 50)
    py5.stroke_weight(2)
    for (p1, p2) in streets:
        py5.line(p1[0], p1[1], p2[0], p2[1])
        
    py5.no_stroke()
    for b in blocks:
        n = py5.os_noise(b.x * 0.001, b.y * 0.001, py5.frame_count * 0.01)
        if n > 0.6:
            py5.fill(10, 20, 30, int(py5.remap(n, 0.6, 1.0, 0, 50)))
            py5.rect(b.x + 5, b.y + 5, b.w - 10, b.h - 10)
    
    py5.stroke_weight(3)
    for p in particles:
        cx, cy, tx, ty, speed, c = p
        
        dx = tx - cx
        dy = ty - cy
        dist = np.hypot(dx, dy)
        
        if dist < speed:
            p[0], p[1] = tx, ty
            node = (tx, ty)
            if node in graph and graph[node]:
                next_target = random.choice(graph[node])
                p[2], p[3] = next_target[0], next_target[1]
            else:
                p[2], p[3] = tx, ty 
        else:
            p[0] += (dx / dist) * speed
            p[1] += (dy / dist) * speed
            
        py5.stroke(c[0], c[1], c[2], 200)
        py5.point(p[0], p[1])
        
    py5.blend_mode(py5.BLEND)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

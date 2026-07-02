from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.spatial import cKDTree
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Differential Growth Parameters
MAX_NODES = 35000
REPULSION_RADIUS = 30.0
REPULSION_FORCE = 0.8
ATTRACTION_FORCE = 0.2
MAX_EDGE_LEN = 5.0
MIN_EDGE_LEN = 2.0

nodes = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes
    # Initialize a small circle of nodes
    num_initial = 50
    radius = 50.0
    angles = np.linspace(0, 2*np.pi, num_initial, endpoint=False)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    nodes = np.column_stack((
        cx + radius * np.cos(angles),
        cy + radius * np.sin(angles)
    )).astype(np.float32)
    
    # Add initial noise to break perfect symmetry and allow buckling
    nodes += np.random.uniform(-5.0, 5.0, nodes.shape).astype(np.float32)
    
    py5.background(240, 235, 225) # Warm off-white paper texture

def grow():
    global nodes
    
    # 1. Edge Attraction (Connected nodes pull each other)
    next_nodes = np.roll(nodes, -1, axis=0)
    prev_nodes = np.roll(nodes, 1, axis=0)
    
    # Spring force towards adjacent nodes
    force_attract = ((next_nodes - nodes) + (prev_nodes - nodes)) * ATTRACTION_FORCE
    
    # 2. Node Repulsion (All nodes repel each other within radius)
    tree = cKDTree(nodes)
    pairs = tree.query_pairs(REPULSION_RADIUS)
    
    force_repel = np.zeros_like(nodes)
    if len(pairs) > 0:
        pairs = np.array(list(pairs))
        i, j = pairs[:, 0], pairs[:, 1]
        
        diff = nodes[i] - nodes[j]
        dist = np.linalg.norm(diff, axis=1, keepdims=True)
        # Avoid division by zero
        dist = np.maximum(dist, 0.1)
        
        # Repulsion inversely proportional to distance
        mag = (REPULSION_RADIUS - dist) / REPULSION_RADIUS * REPULSION_FORCE
        f = (diff / dist) * mag
        
        np.add.at(force_repel, i, f)
        np.add.at(force_repel, j, -f)
        
    # Apply forces
    nodes += force_attract * 0.1
    nodes += force_repel * 0.5
    
    # 3. Add new nodes where edges are too long
    # We rebuild the array
    diffs = np.roll(nodes, -1, axis=0) - nodes
    dists = np.linalg.norm(diffs, axis=1)
    
    new_nodes = []
    for i in range(len(nodes)):
        new_nodes.append(nodes[i])
        if dists[i] > MAX_EDGE_LEN and len(nodes) + len(new_nodes) < MAX_NODES:
            midpoint = nodes[i] + diffs[i] * 0.5
            new_nodes.append(midpoint)
            
    nodes = np.array(new_nodes, dtype=np.float32)

def draw():
    global nodes
    
    # Simulate multiple steps per frame to speed up growth
    for _ in range(5):
        if len(nodes) < MAX_NODES:
            grow()
            
    # Render
    # We clear background completely or draw with trail?
    # Differential growth looks best when drawn clearly
    py5.background(20, 25, 30) # Dark charcoal
    
    py5.no_fill()
    py5.stroke(255, 200, 150) # Warm coral / peach
    py5.stroke_weight(3.0)
    
    py5.begin_shape()
    for pt in nodes:
        py5.vertex(pt[0], pt[1])
    py5.end_shape(py5.CLOSE)
    
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
        import os
        os._exit(0)

py5.run_sketch()

from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import numpy as np
import py5
from scipy.spatial import cKDTree

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

# Differential growth parameters
REPULSION_RADIUS = 12.0
REPULSION_FORCE = 0.8
ATTRACTION_FORCE = 0.5
MAX_EDGE_LEN = 8.0
MIN_EDGE_LEN = 2.0

nodes = None

def setup():
    global nodes
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(240, 240, 235)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize a small circle of nodes
    n_initial = 20
    r = 10.0
    cx, cy = SIZE[0]/2, SIZE[1]/2
    theta = np.linspace(0, 2*math.pi, n_initial, endpoint=False)
    nodes = np.column_stack((cx + r*np.cos(theta), cy + r*np.sin(theta))).astype(np.float32)

def draw():
    global nodes
    
    py5.background(240, 240, 235)
    
    # 1. Growth: Subdivide edges that are too long
    # Calculate edge vectors
    diffs = np.diff(nodes, axis=0, append=nodes[:1])
    dists = np.linalg.norm(diffs, axis=1)
    
    # Find edges to split
    split_idx = np.where(dists > MAX_EDGE_LEN)[0]
    
    if len(split_idx) > 0:
        # Create new nodes at midpoints
        new_nodes = nodes[split_idx] + diffs[split_idx] * 0.5
        
        inserts = split_idx + 1
        nodes = np.insert(nodes, inserts, new_nodes, axis=0)

    # 2. Physics step
    forces = np.zeros_like(nodes)
    
    # Attraction to neighbors
    diffs = np.diff(nodes, axis=0, append=nodes[:1]) # vector to next
    forces += diffs * ATTRACTION_FORCE
    
    prev_diffs = nodes - np.roll(nodes, 1, axis=0) # vector to prev
    forces -= prev_diffs * ATTRACTION_FORCE
    
    # Repulsion using KDTree
    tree = cKDTree(nodes)
    pairs = tree.query_pairs(REPULSION_RADIUS)
    
    if pairs:
        idx1, idx2 = np.array(list(pairs)).T
        p1 = nodes[idx1]
        p2 = nodes[idx2]
        
        d_vec = p1 - p2
        dist = np.linalg.norm(d_vec, axis=1)
        
        dist = np.maximum(dist, 0.0001)
        
        mag = (REPULSION_RADIUS - dist) / REPULSION_RADIUS * REPULSION_FORCE
        f_vec = (d_vec / dist[:, None]) * mag[:, None]
        
        np.add.at(forces, idx1, f_vec)
        np.add.at(forces, idx2, -f_vec)
        
    # Boundary repulsion
    margin = 50
    forces[:, 0] += np.maximum(0, margin - nodes[:, 0]) * 0.5
    forces[:, 1] += np.maximum(0, margin - nodes[:, 1]) * 0.5
    forces[:, 0] -= np.maximum(0, nodes[:, 0] - (SIZE[0] - margin)) * 0.5
    forces[:, 1] -= np.maximum(0, nodes[:, 1] - (SIZE[1] - margin)) * 0.5
        
    # Update positions
    nodes += forces
    
    # 3. Draw
    py5.no_fill()
    py5.stroke(20, 20, 25)
    py5.stroke_weight(1.5)
    
    py5.begin_shape()
    for i in range(len(nodes)):
        py5.vertex(nodes[i, 0], nodes[i, 1])
    py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%), Nodes: {len(nodes)}")

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

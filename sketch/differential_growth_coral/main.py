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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Differential growth parameters
REPULSION_RADIUS = 15.0
MAX_EDGE_LEN = 10.0
MIN_EDGE_LEN = 2.0
REPULSION_FORCE = 0.5
SPRING_FORCE = 0.2

# Nodes initialized as a small circle
NUM_INITIAL_NODES = 30
angles = np.linspace(0, 2*np.pi, NUM_INITIAL_NODES, endpoint=False)
nodes_x = np.cos(angles) * 50.0 + SIZE[0]/2
nodes_y = np.sin(angles) * 50.0 + SIZE[1]/2

nodes = np.stack([nodes_x, nodes_y], axis=-1).tolist()

def update_growth():
    global nodes
    
    n = len(nodes)
    if n > 8000:
        return # Cap to prevent physics from lagging too much
        
    pts = np.array(nodes, dtype=np.float32)
    forces = np.zeros_like(pts)
    
    # 1. Repulsion (O(N^2) but we use a small radius limit approximation via numpy)
    # To keep it fast, we do pure vectorized pairwise distances for N < 8000
    # but that's a 64M element array. We'll do chunked or just subset it.
    
    # Simple spring forces between neighbors
    next_pts = np.roll(pts, -1, axis=0)
    prev_pts = np.roll(pts, 1, axis=0)
    
    # Pull towards neighbors
    forces += (next_pts - pts) * SPRING_FORCE
    forces += (prev_pts - pts) * SPRING_FORCE
    
    # Fast vectorized repulsion
    # Pick random subset to repulse against for performance if n > 1000
    if n > 1000:
        subset_size = 500
        indices = np.random.choice(n, subset_size, replace=False)
        repulsors = pts[indices]
    else:
        repulsors = pts
        
    for i in range(len(repulsors)):
        diff = pts - repulsors[i]
        dist_sq = diff[:, 0]**2 + diff[:, 1]**2
        mask = (dist_sq > 0.1) & (dist_sq < REPULSION_RADIUS**2)
        forces[mask] += (diff[mask] / np.sqrt(dist_sq[mask])[:, None]) * REPULSION_FORCE

    pts += forces
    
    # Center the structure
    center_offset = np.mean(pts, axis=0) - np.array([SIZE[0]/2, SIZE[1]/2])
    pts -= center_offset * 0.05
    
    # 2. Add new nodes if edge is too long
    new_nodes = []
    for i in range(n):
        new_nodes.append(pts[i].tolist())
        p1 = pts[i]
        p2 = pts[(i+1)%n]
        d = np.linalg.norm(p2 - p1)
        if d > MAX_EDGE_LEN:
            mid = (p1 + p2) * 0.5
            new_nodes.append(mid.tolist())
            
    nodes = new_nodes


def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global nodes
    
    py5.background(0)
    
    for _ in range(5):
        update_growth()
    
    py5.no_fill()
    
    # Draw the coral
    py5.stroke_weight(2.0)
    
    # We draw the polygon with gradient color
    py5.begin_shape()
    n = len(nodes)
    for i in range(n):
        # Color based on index / total and time
        hue = (i / n * 360 * 3 + py5.frame_count) % 360
        py5.stroke(hue, 80, 100)
        py5.vertex(nodes[i][0], nodes[i][1])
    py5.end_shape(py5.CLOSE)
    
    # Draw a faint glow
    py5.stroke_weight(10.0)
    py5.begin_shape()
    for i in range(n):
        hue = (i / n * 360 * 3 + py5.frame_count) % 360
        py5.stroke(hue, 80, 100, 20)
        py5.vertex(nodes[i][0], nodes[i][1])
    py5.end_shape(py5.CLOSE)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) Nodes: {n}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

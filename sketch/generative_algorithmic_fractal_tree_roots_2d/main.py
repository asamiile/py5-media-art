from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.spatial import KDTree

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


NUM_NUTRIENTS = 10000
nodes_pts = []
nutrients_pts = []
nutrients_active = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize nutrients randomly in a circle
    global nutrients_pts, nutrients_active, nodes_pts
    r = py5.width * 0.45 * np.sqrt(np.random.rand(NUM_NUTRIENTS))
    theta = np.random.rand(NUM_NUTRIENTS) * 2 * np.pi
    nx = py5.width/2 + r * np.cos(theta)
    ny = py5.height/2 + r * np.sin(theta)
    
    nutrients_pts = np.column_stack((nx, ny))
    nutrients_active = np.ones(NUM_NUTRIENTS, dtype=bool)
        
    # Initial root
    nodes_pts = np.array([[py5.width/2, py5.height/2]])
    py5.background(5, 10, 15)


def draw():
    global nutrients_pts, nutrients_active, nodes_pts
    py5.stroke(100, 255, 150, 40)
    py5.stroke_weight(1)
    py5.blend_mode(py5.ADD)
    
    # Space colonization algorithm
    max_dist = 200.0
    min_dist = 10.0
    step_size = 10.0
    
    active_idx = np.where(nutrients_active)[0]
    if len(active_idx) > 0 and len(nodes_pts) > 0:
        # Build KDTree for nodes
        tree = KDTree(nodes_pts)
        active_nuts = nutrients_pts[active_idx]
        
        # Query nearest node for each nutrient
        dists, idxs = tree.query(active_nuts, distance_upper_bound=max_dist)
        
        valid = dists != np.inf
        
        # Mark reached nutrients inactive
        reached = valid & (dists < min_dist)
        nutrients_active[active_idx[reached]] = False
        
        # Get nutrients that are pulling a node
        pulling = valid & (~reached)
        pulling_nuts = active_nuts[pulling]
        pulling_node_idxs = idxs[pulling]
        
        # Accumulate forces
        new_nodes = []
        lines_x1 = []
        lines_y1 = []
        lines_x2 = []
        lines_y2 = []
        
        if len(pulling_node_idxs) > 0:
            unique_nodes, inverse_idx = np.unique(pulling_node_idxs, return_inverse=True)
            for i, n_idx in enumerate(unique_nodes):
                nuts_for_node = pulling_nuts[inverse_idx == i]
                node_pos = nodes_pts[n_idx]
                
                # direction vector
                d = nuts_for_node - node_pos
                lengths = np.hypot(d[:,0], d[:,1])
                d_norm = d / lengths[:, np.newaxis]
                
                avg_d = np.sum(d_norm, axis=0)
                avg_l = np.hypot(avg_d[0], avg_d[1])
                if avg_l > 0:
                    avg_d = (avg_d / avg_l) * step_size
                    
                new_pos = node_pos + avg_d
                new_nodes.append(new_pos)
                
                lines_x1.append(node_pos[0])
                lines_y1.append(node_pos[1])
                lines_x2.append(new_pos[0])
                lines_y2.append(new_pos[1])
                
            if len(new_nodes) > 0:
                nodes_pts = np.vstack((nodes_pts, new_nodes))
                
                # Batch draw lines
                py5.begin_shape(py5.LINES)
                for x1, y1, x2, y2 in zip(lines_x1, lines_y1, lines_x2, lines_y2):
                    py5.vertex(x1, y1)
                    py5.vertex(x2, y2)
                py5.end_shape()

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

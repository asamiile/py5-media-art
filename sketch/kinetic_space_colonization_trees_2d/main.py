from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.spatial import cKDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Space Colonization Algorithm parameters
NUM_ATTRACTORS = 15000
ATTRACT_DIST = py5.height * 0.15 # Max distance to be influenced
KILL_DIST = py5.height * 0.005  # Distance to eat an attractor
BRANCH_LEN = py5.height * 0.006

attractors = []
nodes = [] # (x, y, parent_idx, thickness)
node_pts = None # Nx2 numpy array for fast querying
KD_TREE_ATTRACTORS = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.background(150, 80, 10) # Dark teal background
    
    global attractors, nodes, node_pts
    
    # Create attractors in canopy shapes
    for _ in range(NUM_ATTRACTORS):
        # Three circular canopies
        cx, cy = random.choice([
            (py5.width * 0.2, py5.height * 0.4),
            (py5.width * 0.5, py5.height * 0.3),
            (py5.width * 0.8, py5.height * 0.4)
        ])
        
        # Add random scatter
        r = py5.height * 0.3 * np.sqrt(random.random())
        theta = random.random() * 2 * np.pi
        
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        
        attractors.append(np.array([x, y]))
        
    attractors = np.array(attractors, dtype=np.float32)
    
    # Create initial root nodes
    for i, cx in enumerate([py5.width * 0.2, py5.width * 0.5, py5.width * 0.8]):
        # Start at the bottom
        x = cx
        y = py5.height
        
        # Grow trunk straight up until it reaches canopy
        parent_idx = -1
        while y > py5.height * 0.7:
            nodes.append((x, y, parent_idx, 0.0))
            parent_idx = len(nodes) - 1
            y -= BRANCH_LEN
            
    node_pts = np.array([[n[0], n[1]] for n in nodes], dtype=np.float32)

def draw():
    global attractors, nodes, node_pts
    
    # We do multiple growth steps per frame for speed
    for _ in range(2):
        if len(attractors) == 0:
            break
            
        # Build KD tree of tree nodes to find nearest neighbors for each attractor
        node_tree = cKDTree(node_pts)
        
        # Query nearest node for each attractor
        dists, indices = node_tree.query(attractors, distance_upper_bound=ATTRACT_DIST)
        
        # Find which attractors are eaten
        eaten = dists < KILL_DIST
        
        # Filter out eaten attractors
        valid = ~eaten
        active_attractors = attractors[valid]
        active_dists = dists[valid]
        active_indices = indices[valid]
        
        attractors = active_attractors # Update global list
        
        if len(attractors) == 0:
            break
            
        # For each node, find the average direction of all attractors it influences
        # active_indices contains the index of the nearest node for each active attractor
        
        # Accumulate direction vectors
        node_dirs = np.zeros_like(node_pts)
        node_counts = np.zeros(len(node_pts), dtype=np.int32)
        
        # Only process those within ATTRACT_DIST (scipy cKDTree returns infinity if not found)
        in_range = active_dists < ATTRACT_DIST
        
        valid_attractors = active_attractors[in_range]
        valid_indices = active_indices[in_range]
        
        for i in range(len(valid_attractors)):
            attr = valid_attractors[i]
            n_idx = valid_indices[i]
            
            node_pos = node_pts[n_idx]
            dir_vec = attr - node_pos
            # Normalize
            norm = np.linalg.norm(dir_vec)
            if norm > 0:
                dir_vec /= norm
                
            node_dirs[n_idx] += dir_vec
            node_counts[n_idx] += 1
            
        # Add new nodes
        new_nodes = []
        new_node_pts = []
        
        for n_idx in range(len(node_pts)):
            if node_counts[n_idx] > 0:
                avg_dir = node_dirs[n_idx] / node_counts[n_idx]
                # Normalize again just in case
                norm = np.linalg.norm(avg_dir)
                if norm > 0:
                    avg_dir /= norm
                    
                # Add some noise to the direction for organic growth
                noise_angle = random.uniform(-0.2, 0.2)
                c, s = np.cos(noise_angle), np.sin(noise_angle)
                rot_dir = np.array([avg_dir[0]*c - avg_dir[1]*s, avg_dir[0]*s + avg_dir[1]*c])
                
                new_pos = node_pts[n_idx] + rot_dir * BRANCH_LEN
                
                new_nodes.append((new_pos[0], new_pos[1], n_idx, 0.0))
                new_node_pts.append(new_pos)
                
        if new_nodes:
            nodes.extend(new_nodes)
            node_pts = np.vstack([node_pts, np.array(new_node_pts)])
            
    # Calculate thickness from leaves to root
    # We do this every frame for the new topology
    leaf_nodes = set(range(len(nodes)))
    for n in nodes:
        if n[2] != -1:
            leaf_nodes.discard(n[2])
            
    area = np.zeros(len(nodes), dtype=np.float32)
    for i in leaf_nodes:
        area[i] = 1.0
        
    for i in range(len(nodes) - 1, -1, -1):
        parent_idx = nodes[i][2]
        if parent_idx != -1:
            area[parent_idx] += area[i]
            
    thickness = np.sqrt(area)
            
    # Render
    py5.background(150, 80, 10)
    
    # Draw attractors (leaves)
    py5.no_stroke()
    py5.fill(160, 90, 80, 40)
    for a in attractors:
        py5.circle(a[0], a[1], 4)
        
    # Draw branches
    py5.no_fill()
    py5.stroke(140, 80, 60)
    
    for i in range(len(nodes)):
        parent_idx = nodes[i][2]
        if parent_idx != -1:
            py5.stroke_weight(thickness[i] * 0.5)
            # Add a slight color gradient based on height
            h = py5.remap(nodes[i][1], py5.height, 0, 140, 180)
            py5.stroke(h, 90, 80)
            py5.line(nodes[i][0], nodes[i][1], nodes[parent_idx][0], nodes[parent_idx][1])

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

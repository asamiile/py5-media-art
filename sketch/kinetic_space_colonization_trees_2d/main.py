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

# Space Colonization Algorithm Constants
MAX_DIST = 400.0  # Max distance an attractor can influence a branch
MIN_DIST = 15.0   # Distance at which an attractor is "reached" and removed
BRANCH_LENGTH = 8.0 # How far a branch grows per step
NUM_ATTRACTORS = 15000

# Attractors: numpy array (N, 2)
attractors = []
for _ in range(NUM_ATTRACTORS):
    # distribute them mostly in a wide circle
    r = random.uniform(200, SIZE[1] // 2 - 50)
    theta = random.uniform(0, py5.TWO_PI)
    cx, cy = SIZE[0] // 2, SIZE[1] // 2
    attractors.append([cx + r * np.cos(theta), cy + r * np.sin(theta)])
attractors = np.array(attractors, dtype=np.float32)

# Tree nodes: numpy array (M, 2) of positions, parent index array (M,), and hue array (M,)
tree = np.array([[SIZE[0]//2, SIZE[1]//2]], dtype=np.float32)
parents = np.array([-1], dtype=np.int32)
hues = np.array([160.0], dtype=np.float32)

# To keep the render fast over time, we only consider "active" tree nodes (leaves) that recently grew
# This is an optimization. We keep a boolean mask of active nodes.
active_nodes = np.array([True])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 5) # almost black
    py5.stroke_weight(2.0)
    py5.no_fill()

def draw():
    global attractors, tree, parents, hues, active_nodes
    
    # We do a few growth steps per frame
    for _ in range(2):
        if len(attractors) == 0:
            break
            
        # Get active tree nodes
        active_idx = np.where(active_nodes)[0]
        if len(active_idx) == 0:
            break
        active_tree = tree[active_idx]
        
        # Calculate distances from all attractors to all active tree nodes
        # To avoid massive memory allocation (N*M*2 floats), we loop over attractors or use KDTree.
        # We find the closest active tree node for each attractor in chunks.
        
        N = len(attractors)
        M = len(active_tree)
        
        # If no active nodes, break
        if M == 0: break
        
        closest_node_idx_for_attractor = np.zeros(N, dtype=np.int32) - 1
        min_dist_for_attractor = np.full(N, np.inf)
        
        CHUNK_SIZE = 1000
        for i in range(0, N, CHUNK_SIZE):
            chunk = attractors[i:i+CHUNK_SIZE] # (C, 2)
            # diffs: (C, M, 2)
            diffs = chunk[:, np.newaxis, :] - active_tree[np.newaxis, :, :]
            dists = np.linalg.norm(diffs, axis=2) # (C, M)
            
            # Find min dist and index for each attractor in chunk
            min_idx = np.argmin(dists, axis=1) # (C,)
            min_dist = dists[np.arange(len(chunk)), min_idx] # (C,)
            
            # Map chunk indices back to global
            closest_node_idx_for_attractor[i:i+CHUNK_SIZE] = min_idx
            min_dist_for_attractor[i:i+CHUNK_SIZE] = min_dist

        # Filter attractors that are too far
        valid_mask = min_dist_for_attractor < MAX_DIST
        
        # Remove attractors that are reached
        reached_mask = min_dist_for_attractor < MIN_DIST
        
        # We only care about attractors that are valid and NOT reached
        active_attractor_mask = valid_mask & ~reached_mask
        
        if not np.any(active_attractor_mask):
            attractors = attractors[~reached_mask]
            # Randomly deactivate some old nodes so we don't get stuck checking them
            if random.random() < 0.1:
                active_nodes[random.choice(active_idx)] = False
            continue
            
        # For each valid attractor, it influences its closest active node
        valid_attractor_idx = np.where(active_attractor_mask)[0]
        influencing_attractors = attractors[valid_attractor_idx]
        influenced_active_nodes = closest_node_idx_for_attractor[valid_attractor_idx] # these are indices into active_tree!
        
        # Accumulate directions for each active node
        node_dir_sum = np.zeros_like(active_tree)
        node_pull_count = np.zeros(M, dtype=np.int32)
        
        # Calculate direction from node to attractor
        dirs = influencing_attractors - active_tree[influenced_active_nodes]
        dirs_norm = np.linalg.norm(dirs, axis=1, keepdims=True)
        dirs_normalized = np.divide(dirs, dirs_norm, out=np.zeros_like(dirs), where=dirs_norm!=0)
        
        np.add.at(node_dir_sum, influenced_active_nodes, dirs_normalized)
        np.add.at(node_pull_count, influenced_active_nodes, 1)
        
        # Find which nodes are being pulled
        pulled_mask = node_pull_count > 0
        pulled_indices = np.where(pulled_mask)[0]
        
        if len(pulled_indices) == 0:
            attractors = attractors[~reached_mask]
            continue
            
        # Calculate average direction for pulled nodes
        avg_dirs = node_dir_sum[pulled_indices] / node_pull_count[pulled_indices, np.newaxis]
        avg_dirs_norm = np.linalg.norm(avg_dirs, axis=1, keepdims=True)
        avg_dirs_normalized = np.divide(avg_dirs, avg_dirs_norm, out=np.zeros_like(avg_dirs), where=avg_dirs_norm!=0)
        
        # Calculate new node positions
        new_positions = active_tree[pulled_indices] + avg_dirs_normalized * BRANCH_LENGTH
        
        # The parent index in the FULL tree is active_idx[pulled_indices]
        new_parents = active_idx[pulled_indices]
        
        # Vary hue slightly based on parent hue
        new_hues = hues[new_parents] + np.random.uniform(-1, 1, size=len(new_parents))
        new_hues = np.mod(new_hues, 360) # keep it wrapping
        
        # Draw the new branches
        py5.begin_shape(py5.LINES)
        for i in range(len(new_positions)):
            py5.stroke(new_hues[i], 90, 100, 80)
            p_idx = new_parents[i]
            py5.vertex(tree[p_idx, 0], tree[p_idx, 1])
            py5.vertex(new_positions[i, 0], new_positions[i, 1])
        py5.end_shape()
        
        # Append new nodes to the full tree
        tree = np.vstack((tree, new_positions))
        parents = np.concatenate((parents, new_parents))
        hues = np.concatenate((hues, new_hues))
        active_nodes = np.concatenate((active_nodes, np.ones(len(new_positions), dtype=bool)))
        
        # Remove reached attractors
        attractors = attractors[~reached_mask]

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

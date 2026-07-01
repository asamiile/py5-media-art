from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import scipy.spatial as spatial
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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Differential growth parameters
MAX_EDGE_LEN = 15.0
MIN_EDGE_LEN = 5.0
REPULSION_RADIUS = 25.0
REPULSION_FORCE = 1.0
ATTRACTION_FORCE = 0.5
ALIGNMENT_FORCE = 0.1

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points, velocities
    
    # Start with a small circle
    num_initial = 50
    angles = np.linspace(0, py5.PI * 2, num_initial, endpoint=False)
    radius = 50.0
    cx, cy = py5.width / 2, py5.height / 2
    
    x = cx + np.cos(angles) * radius
    y = cy + np.sin(angles) * radius
    
    points = np.column_stack((x, y))
    velocities = np.zeros_like(points)

def draw():
    global points, velocities
    
    # Run the simulation for multiple steps per frame
    # We want it to grow rapidly within 450 frames
    STEPS = 5
    
    for step in range(STEPS):
        # 1. Repulsion using KDTree for efficiency
        tree = spatial.KDTree(points)
        pairs = tree.query_pairs(REPULSION_RADIUS)
        
        forces = np.zeros_like(points)
        
        if len(pairs) > 0:
            i, j = np.array(list(pairs)).T
            
            p_i = points[i]
            p_j = points[j]
            
            diff = p_i - p_j
            dist = np.linalg.norm(diff, axis=1, keepdims=True)
            # Avoid division by zero
            dist = np.maximum(dist, 0.001)
            
            # Inverse distance weighting for repulsion
            repel = (diff / dist) * (1.0 - dist / REPULSION_RADIUS) * REPULSION_FORCE
            
            # Accumulate forces
            np.add.at(forces, i, repel)
            np.add.at(forces, j, -repel)
            
        # 2. Edge attraction (keep connected points together)
        num_pts = len(points)
        next_idx = (np.arange(num_pts) + 1) % num_pts
        prev_idx = (np.arange(num_pts) - 1) % num_pts
        
        p_next = points[next_idx]
        p_prev = points[prev_idx]
        
        # Pull towards neighbors
        attract_next = (p_next - points) * ATTRACTION_FORCE
        attract_prev = (p_prev - points) * ATTRACTION_FORCE
        
        # 3. Alignment (try to stay in a smooth line)
        midpoint = (p_next + p_prev) / 2.0
        alignment = (midpoint - points) * ALIGNMENT_FORCE
        
        # Apply forces to velocities
        velocities += forces + attract_next + attract_prev + alignment
        
        # Friction
        velocities *= 0.5
        
        # Update positions
        points += velocities
        
        # Keep inside bounds
        # points = np.clip(points, 50, py5.width - 50) # Allow it to grow off screen
        
        # 4. Growth / Subdivision
        # Find segments that are too long
        diffs = points[next_idx] - points
        dists = np.linalg.norm(diffs, axis=1)
        
        too_long = np.where(dists > MAX_EDGE_LEN)[0]
        
        if len(too_long) > 0:
            # We insert new points at the midpoint of long segments
            new_points = []
            
            # Since inserting shifts indices, we do it carefully or build a new list
            # We can use np.insert, but doing it in bulk is tricky due to indices
            # For simplicity, we just rebuild the array if there are subdivisions
            
            new_pts_list = []
            new_vels_list = []
            for idx in range(num_pts):
                new_pts_list.append(points[idx])
                new_vels_list.append(velocities[idx])
                
                if dists[idx] > MAX_EDGE_LEN:
                    mid = (points[idx] + points[next_idx[idx]]) / 2.0
                    new_pts_list.append(mid)
                    new_vels_list.append((velocities[idx] + velocities[next_idx[idx]]) / 2.0)
                    
            points = np.array(new_pts_list)
            velocities = np.array(new_vels_list)
            
    # Draw the shape
    # We use a slightly transparent black background to leave trails
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 5, 15, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke(255, 150, 50, 150)
    py5.stroke_weight(2)
    
    # Draw the continuous organic line
    py5.begin_shape()
    py5.vertices(points)
    py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} (Nodes: {len(points)})")

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

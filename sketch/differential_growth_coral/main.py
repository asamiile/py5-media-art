from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
W, H = SIZE

# Differential Growth parameters
MAX_POINTS = 30000
REPULSION_RADIUS = 30.0
ATTRACTION_RADIUS = 40.0
MAX_EDGE_LEN = 15.0
SPLIT_EDGE_LEN = 25.0
MIN_EDGE_LEN = 5.0
REPULSION_FACTOR = 0.8
ATTRACTION_FACTOR = 0.1
SPRING_FACTOR = 0.4

points = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(20, 20, 25)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points
    # Start with a small circle
    num_initial = 100
    angles = np.linspace(0, 2 * np.pi, num_initial, endpoint=False)
    r = 200
    points = np.zeros((num_initial, 2))
    points[:, 0] = W / 2 + np.cos(angles) * r
    points[:, 1] = H / 2 + np.sin(angles) * r

def update_growth():
    global points
    N = len(points)
    
    if N >= MAX_POINTS:
        return
        
    forces = np.zeros_like(points)
    
    # 1. Spring forces between neighbors
    p_prev = np.roll(points, 1, axis=0)
    p_next = np.roll(points, -1, axis=0)
    
    # Vector to prev and next
    v_prev = p_prev - points
    v_next = p_next - points
    
    # Spring force pulling towards neighbors
    forces += v_prev * SPRING_FACTOR
    forces += v_next * SPRING_FACTOR
    
    # 2. Repulsion from nearby points using KDTree
    tree = cKDTree(points)
    pairs = tree.query_pairs(r=REPULSION_RADIUS)
    
    # Apply repulsion using vectorized numpy
    pairs_list = list(pairs)
    if len(pairs_list) > 0:
        pairs_arr = np.array(pairs_list)
        i_idx = pairs_arr[:, 0]
        j_idx = pairs_arr[:, 1]
        
        # Filter out immediate neighbors
        diff_idx = np.abs(i_idx - j_idx)
        mask = (diff_idx != 1) & (diff_idx != N - 1)
        i_idx = i_idx[mask]
        j_idx = j_idx[mask]
        
        if len(i_idx) > 0:
            diffs = points[i_idx] - points[j_idx]
            dist_sq = np.sum(diffs**2, axis=1)
            
            valid = dist_sq > 0
            if np.any(valid):
                i_v = i_idx[valid]
                j_v = j_idx[valid]
                diffs_v = diffs[valid]
                dists_v = np.sqrt(dist_sq[valid])
                
                rep_mags = (REPULSION_RADIUS - dists_v) / dists_v * REPULSION_FACTOR
                force_vectors = diffs_v * rep_mags[:, np.newaxis]
                
                np.add.at(forces, i_v, force_vectors)
                np.add.at(forces, j_v, -force_vectors)
            
    # Update positions
    points += forces
    
    # 3. Add new points (Growth)
    # Calculate distances to next point
    diffs = p_next - points
    dists = np.sqrt(np.sum(diffs**2, axis=1))
    
    # Find edges that are too long
    split_indices = np.where(dists > SPLIT_EDGE_LEN)[0]
    
    if len(split_indices) > 0 and N < MAX_POINTS:
        # Create new points at the midpoints
        new_points = points[split_indices] + diffs[split_indices] * 0.5
        
        # Insert them into the array
        # np.insert handles multiple indices based on the original array size automatically
        insert_positions = split_indices + 1
        
        points = np.insert(points, insert_positions, new_points, axis=0)

def draw():
    # Draw background with slight trail/fade
    py5.fill(20, 20, 25, 10)
    py5.no_stroke()
    py5.rect(0, 0, W, H)
    
    # Run multiple growth steps per frame for speed
    for _ in range(3):
        update_growth()
        
    # Draw points as a continuous smooth shape
    py5.no_fill()
    py5.stroke(180, 80, 90, 80) # Cyan-ish
    py5.stroke_weight(2.0)
    
    # We want a thick organic glow
    py5.stroke(320, 80, 90, 40) # Pinkish glow
    py5.stroke_weight(8.0)
    py5.begin_shape()
    for p in points:
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)
    
    # Core line
    py5.stroke(180, 60, 100, 90) # Cyan core
    py5.stroke_weight(2.0)
    py5.begin_shape()
    for p in points:
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Points: {len(points)}")

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

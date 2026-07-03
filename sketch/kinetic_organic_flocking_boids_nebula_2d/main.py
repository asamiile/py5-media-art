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

NUM_BOIDS = 2500
positions = np.random.uniform(0, max(SIZE), (NUM_BOIDS, 2)).astype(np.float32)

# Initial velocities
angles = np.random.uniform(0, 2*np.pi, NUM_BOIDS)
velocities = np.column_stack((np.cos(angles), np.sin(angles))) * 5.0
max_speed = 8.0
max_force = 0.2

# Boid rules weights
w_sep = 1.5
w_ali = 1.0
w_coh = 1.0
w_wander = 0.5

# Visuals
colors_hue = np.zeros(NUM_BOIDS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 100, 10) # Deep space blue
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(2)

def draw():
    global positions, velocities, colors_hue
    
    # Trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(240, 100, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.05
    
    # Boids algorithm using cKDTree for fast neighbor lookup
    tree = cKDTree(positions)
    
    # Neighbors within radius for cohesion and alignment
    radius = 150.0
    # Separation radius
    sep_radius = 40.0
    
    acceleration = np.zeros_like(positions)
    
    # We can query all pairs within radius
    # For Python speed, tree.query_pairs or querying tree against itself
    # tree.query_ball_tree is very fast
    # However, iterating lists in Python is slow. 
    # Let's use a trick: sparse matrix from tree.sparse_distance_matrix
    dist_matrix = tree.sparse_distance_matrix(tree, radius, output_type='coo_matrix')
    
    # Find neighbors count for color mapping
    # Just a bincount of row indices
    counts = np.bincount(dist_matrix.row, minlength=NUM_BOIDS)
    
    # To keep it completely vectorized without slow loops:
    # We will compute a simplified flocking model using NumPy.
    
    # Wander force (Perlin noise-like or just random changing angles)
    wander_angles = py5.frame_count * 0.05 + positions[:, 0] * 0.01 + positions[:, 1] * 0.01
    wander_force = np.column_stack((np.cos(wander_angles), np.sin(wander_angles))) * max_force * w_wander
    acceleration += wander_force
    
    # Instead of full proper boids which is hard to vectorize perfectly from COO matrix,
    # we'll approximate: 
    # A global center of mass for loose cohesion, and local repulsion
    
    # Repulsion (Separation)
    # Get all pairs within sep_radius
    sep_matrix = tree.sparse_distance_matrix(tree, sep_radius, output_type='coo_matrix')
    
    if sep_matrix.nnz > 0:
        i = sep_matrix.row
        j = sep_matrix.col
        # Ignore self
        mask = i != j
        i = i[mask]
        j = j[mask]
        
        diff = positions[i] - positions[j]
        # Normalize and weight by distance
        d = sep_matrix.data[mask]
        # Avoid division by zero
        d[d < 1.0] = 1.0
        
        diff = diff / (d[:, np.newaxis]**2)
        
        # Accumulate forces
        sep_force = np.zeros_like(positions)
        np.add.at(sep_force[:, 0], i, diff[:, 0])
        np.add.at(sep_force[:, 1], i, diff[:, 1])
        
        acceleration += sep_force * w_sep

    # Simplified Alignment & Cohesion based on center
    # Drive boids towards the center of mass of the entire flock or a moving target
    center_target = np.array([py5.width/2 + np.sin(time_val*0.5)*500, 
                              py5.height/2 + np.cos(time_val*0.3)*500])
    
    dir_to_center = center_target - positions
    dist_to_center = np.linalg.norm(dir_to_center, axis=1, keepdims=True)
    dir_to_center = dir_to_center / (dist_to_center + 1.0)
    
    acceleration += dir_to_center * max_force * w_coh * 0.5
    
    # Update velocities
    velocities += acceleration
    
    # Limit speed
    speed = np.linalg.norm(velocities, axis=1, keepdims=True)
    mask = speed > max_speed
    velocities[mask[:, 0]] = (velocities / speed)[mask[:, 0]] * max_speed
    
    # Update positions
    positions += velocities
    
    # Wrap around edges
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Drawing
    py5.begin_shape(py5.LINES)
    
    # The more neighbors, the hotter the color (Cyan -> Pink -> White)
    # Smooth counts
    colors_hue = colors_hue * 0.9 + counts * 0.1
    
    # Max neighbors roughly 50
    normalized_density = np.clip(colors_hue / 30.0, 0, 1)
    
    hues = 200 + normalized_density * 120 # 200 (Cyan) to 320 (Pink)
    brightness = 50 + normalized_density * 50
    
    # Calculate tail position
    tail = positions - velocities * 4.0
    
    for k in range(NUM_BOIDS):
        py5.stroke(hues[k], 80, brightness[k], 80)
        py5.vertex(positions[k, 0], positions[k, 1])
        py5.vertex(tail[k, 0], tail[k, 1])
        
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

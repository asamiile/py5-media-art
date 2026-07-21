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

# Boids simulation parameters
NUM_BOIDS = 4000
MAX_SPEED = 8.0
MAX_FORCE = 0.2
PERCEPTION_RADIUS = 75.0

# Initial positions and velocities
positions = np.random.rand(NUM_BOIDS, 2).astype(np.float32)
positions[:, 0] *= SIZE[0]
positions[:, 1] *= SIZE[1]

# random velocities
angles = np.random.rand(NUM_BOIDS) * 2 * np.pi
velocities = np.column_stack((np.cos(angles), np.sin(angles))).astype(np.float32) * MAX_SPEED

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 100, 10) # Navy blue
    py5.no_stroke()

def draw():
    global positions, velocities
    
    # We apply a slight fading background for motion blur
    py5.fill(240, 100, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Build KD-Tree for fast neighbor lookup
    tree = cKDTree(positions)
    
    # Compute flocking forces
    separation = np.zeros_like(velocities)
    alignment = np.zeros_like(velocities)
    cohesion = np.zeros_like(velocities)
    
    # Find all neighbors within radius
    # To optimize, we can use query_pairs or query_ball_tree, but doing it per boid via query_ball_point is okay in scipy
    # Or query_ball_tree against itself
    pairs = tree.query_pairs(PERCEPTION_RADIUS)
    
    # Using pairs to accumulate forces is very fast
    # pairs is a set of (i, j) indices where distance < r
    align_sums = np.zeros_like(velocities)
    cohes_sums = np.zeros_like(positions)
    sep_sums = np.zeros_like(velocities)
    counts = np.zeros(NUM_BOIDS, dtype=np.int32)
    
    if pairs:
        pairs = np.array(list(pairs))
        i = pairs[:, 0]
        j = pairs[:, 1]
        
        # distance vectors
        diff = positions[i] - positions[j]
        # wrapped distances? No, let's keep it simple without wrapping space for distance, 
        # but screen bounds will repel them.
        
        dist_sq = np.sum(diff**2, axis=1)
        # Avoid division by zero
        dist_sq[dist_sq < 0.1] = 0.1
        
        # Separation
        repel = diff / dist_sq[:, None]
        np.add.at(sep_sums, i, repel)
        np.add.at(sep_sums, j, -repel)
        
        # Alignment
        np.add.at(align_sums, i, velocities[j])
        np.add.at(align_sums, j, velocities[i])
        
        # Cohesion
        np.add.at(cohes_sums, i, positions[j])
        np.add.at(cohes_sums, j, positions[i])
        
        # Counts
        np.add.at(counts, i, 1)
        np.add.at(counts, j, 1)
    
    # Mask where counts > 0
    mask = counts > 0
    counts_masked = counts[mask, None]
    
    # Normalize forces
    
    # Alignment
    align_sums[mask] /= counts_masked
    # Set magnitude to max_speed
    speeds = np.linalg.norm(align_sums, axis=1, keepdims=True)
    align_sums = np.where(speeds > 0, (align_sums / (speeds + 1e-8)) * MAX_SPEED, align_sums)
    # Steering = desired - velocity
    alignment = align_sums - velocities
    
    # Cohesion
    cohes_sums[mask] /= counts_masked
    desired_cohes = cohes_sums - positions
    speeds_c = np.linalg.norm(desired_cohes, axis=1, keepdims=True)
    desired_cohes = np.where(speeds_c > 0, (desired_cohes / (speeds_c + 1e-8)) * MAX_SPEED, desired_cohes)
    cohesion = desired_cohes - velocities
    
    # Separation
    sep_sums[mask] /= counts_masked
    speeds_s = np.linalg.norm(sep_sums, axis=1, keepdims=True)
    sep_sums = np.where(speeds_s > 0, (sep_sums / (speeds_s + 1e-8)) * MAX_SPEED, sep_sums)
    separation = sep_sums - velocities
    
    # Limit forces
    def limit(v, max_val):
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        # using a tiny epsilon to avoid division by zero
        v = np.where(norms > max_val, (v / (norms + 1e-8)) * max_val, v)
        return v
        
    alignment = limit(alignment, MAX_FORCE)
    cohesion = limit(cohesion, MAX_FORCE)
    separation = limit(separation, MAX_FORCE * 1.5) # Separation gets more weight
    
    # Screen bounds repulsion
    bounds_repel = np.zeros_like(velocities)
    margin = 150
    bounds_repel[:, 0] += np.where(positions[:, 0] < margin, MAX_SPEED, 0)
    bounds_repel[:, 0] -= np.where(positions[:, 0] > SIZE[0] - margin, MAX_SPEED, 0)
    bounds_repel[:, 1] += np.where(positions[:, 1] < margin, MAX_SPEED, 0)
    bounds_repel[:, 1] -= np.where(positions[:, 1] > SIZE[1] - margin, MAX_SPEED, 0)
    
    # Update velocities
    velocities += alignment * 1.0 + cohesion * 1.0 + separation * 1.5 + bounds_repel * 0.5
    velocities = limit(velocities, MAX_SPEED)
    
    # Update positions
    positions += velocities
    
    # Render
    angles = np.arctan2(velocities[:, 1], velocities[:, 0])
    
    # Draw boids
    for i in range(NUM_BOIDS):
        x, y = positions[i]
        angle = angles[i]
        
        # Color based on angle
        hue = (angle / (2 * np.pi) * 360 + 180) % 360
        py5.fill(hue, 80, 100, 80)
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(angle)
        
        # Draw small triangle
        s = 8
        py5.triangle(s, 0, -s, -s/2, -s, s/2)
        
        py5.pop_matrix()

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

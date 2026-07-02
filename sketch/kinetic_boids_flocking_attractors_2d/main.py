import os
from pathlib import Path
import shutil
import subprocess
import sys
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
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Boids Setup
N_BOIDS = 2500
MAX_SPEED = 18.0
MAX_FORCE = 0.8
NEIGHBOR_DIST = 100.0
DESIRED_SEPARATION = 30.0

positions = np.zeros((N_BOIDS, 2))
velocities = np.zeros((N_BOIDS, 2))
accelerations = np.zeros((N_BOIDS, 2))
colors = np.zeros((N_BOIDS, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(0)
    
    positions[:, 0] = np.random.uniform(0, SIZE[0], N_BOIDS)
    positions[:, 1] = np.random.uniform(0, SIZE[1], N_BOIDS)
    
    angles = np.random.uniform(0, 2 * np.pi, N_BOIDS)
    velocities[:, 0] = np.cos(angles) * MAX_SPEED
    velocities[:, 1] = np.sin(angles) * MAX_SPEED
    
    # Assign bioluminescent colors
    # Mix of teal, deep blue, and neon green
    colors[:, 0] = np.random.uniform(0, 50, N_BOIDS)
    colors[:, 1] = np.random.uniform(150, 255, N_BOIDS)
    colors[:, 2] = np.random.uniform(200, 255, N_BOIDS)

def limit_vector(v, max_val):
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    mask = (norms > max_val).flatten()
    if np.any(mask):
        v[mask] = (v[mask] / norms[mask]) * max_val
    return v

def set_mag(v, mag):
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1.0
    return (v / norms) * mag

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 5, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global positions, velocities, accelerations
    
    t = py5.frame_count / TOTAL_FRAMES * 2 * np.pi
    
    # Update KDTree for neighbor finding
    tree = KDTree(positions)
    
    # Arrays to accumulate forces
    sep_force = np.zeros((N_BOIDS, 2))
    ali_force = np.zeros((N_BOIDS, 2))
    coh_force = np.zeros((N_BOIDS, 2))
    
    # Attractors
    attractor1 = np.array([py5.width/2 + np.cos(t) * py5.width/3, py5.height/2 + np.sin(t*2) * py5.height/3])
    attractor2 = np.array([py5.width/2 + np.sin(t*1.5) * py5.width/3, py5.height/2 + np.cos(t*2.5) * py5.height/3])
    
    # Calculate forces
    for i in range(N_BOIDS):
        neighbors = tree.query_ball_point(positions[i], NEIGHBOR_DIST)
        neighbors.remove(i)
        
        if len(neighbors) > 0:
            # Separation
            close_neighbors = [n for n in neighbors if np.linalg.norm(positions[i] - positions[n]) < DESIRED_SEPARATION]
            if len(close_neighbors) > 0:
                diff = positions[i] - positions[close_neighbors]
                dists = np.linalg.norm(diff, axis=1, keepdims=True)
                diff = diff / (dists * dists + 0.001)  # Weight by inverse distance squared
                steer = np.mean(diff, axis=0)
                steer = set_mag(np.array([steer]), MAX_SPEED)[0] - velocities[i]
                sep_force[i] = steer
            
            # Alignment
            avg_vel = np.mean(velocities[neighbors], axis=0)
            steer = set_mag(np.array([avg_vel]), MAX_SPEED)[0] - velocities[i]
            ali_force[i] = steer
            
            # Cohesion
            avg_pos = np.mean(positions[neighbors], axis=0)
            desired = avg_pos - positions[i]
            steer = set_mag(np.array([desired]), MAX_SPEED)[0] - velocities[i]
            coh_force[i] = steer
            
    # Attractor force
    attractor_force = np.zeros((N_BOIDS, 2))
    d1 = attractor1 - positions
    d2 = attractor2 - positions
    
    # Weight attractors
    attractor_force += set_mag(d1, MAX_SPEED) * 0.3
    attractor_force += set_mag(d2, MAX_SPEED) * 0.3

    # Apply limits to forces
    sep_force = limit_vector(sep_force, MAX_FORCE)
    ali_force = limit_vector(ali_force, MAX_FORCE)
    coh_force = limit_vector(coh_force, MAX_FORCE)
    attractor_force = limit_vector(attractor_force, MAX_FORCE * 1.5)
    
    # Add forces to acceleration
    accelerations = sep_force * 2.0 + ali_force * 1.0 + coh_force * 1.0 + attractor_force
    
    # Update physics
    velocities += accelerations
    velocities = limit_vector(velocities, MAX_SPEED)
    
    # Store old positions for lines
    old_positions = positions.copy()
    positions += velocities
    
    # Wrap around edges
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Draw boids
    py5.stroke_weight(4)
    # Using lines to show direction and speed
    
    # Py5 expects flat array for lines or column stacked (x1, y1, x2, y2)
    # Don't draw lines that wrap around the screen
    dist = np.linalg.norm(positions - old_positions, axis=1)
    valid_lines = dist < MAX_SPEED * 2
    
    if np.any(valid_lines):
        p1 = old_positions[valid_lines]
        p2 = positions[valid_lines]
        c = colors[valid_lines]
        
        lines_array = np.column_stack((p1[:, 0], p1[:, 1], p2[:, 0], p2[:, 1]))
        
        # Batch draw by colors is slow, let's just draw all lines at once with a generic glowing color
        # Since py5 vectorized lines can only take a single stroke color unless we iterate
        py5.stroke(0, 200, 255, 150)
        py5.lines(lines_array)
        
        py5.stroke_weight(2)
        py5.stroke(255, 255, 255, 200)
        py5.points(positions)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
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

if __name__ == '__main__':
    py5.run_sketch()

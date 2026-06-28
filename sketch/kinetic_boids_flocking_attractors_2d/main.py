from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.spatial.distance import cdist

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

NUM_BOIDS = 3000

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colors
    
    # Initialize positions and velocities
    pos = np.random.rand(NUM_BOIDS, 2) * [py5.width, py5.height]
    
    # Random initial velocities on a circle
    angles = np.random.rand(NUM_BOIDS) * 2 * py5.PI
    speed = 5.0
    vel = np.column_stack((np.cos(angles), np.sin(angles))) * speed
    
    # Color mapping: map boid index to a gradient (Cyan to Pink)
    norm_idx = np.linspace(0, 1, NUM_BOIDS)
    r = (0.5 + 0.5 * np.cos(norm_idx * py5.PI * 2 + 0.0)) * 255
    g = (0.5 + 0.5 * np.cos(norm_idx * py5.PI * 2 + 2.0)) * 255
    b = (0.5 + 0.5 * np.cos(norm_idx * py5.PI * 2 + 4.0)) * 255
    
    colors = np.column_stack((r, g, b, np.full(NUM_BOIDS, 30))) # Alpha 30

def update_boids():
    global pos, vel
    
    # Compute pairwise distances
    dist_matrix = cdist(pos, pos)
    # Prevent self-interaction and divide by zero
    np.fill_diagonal(dist_matrix, np.inf)
    
    # Boid Rules parameters
    r_sep = 30.0
    r_align = 80.0
    r_coh = 100.0
    
    w_sep = 1.5
    w_align = 1.0
    w_coh = 1.0
    
    max_speed = 8.0
    max_force = 0.1
    
    # 1. Separation
    mask_sep = dist_matrix < r_sep
    # Vector from neighbor to boid
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :] 
    # Weight by 1/distance
    dist_safe = np.where(mask_sep, dist_matrix, 1.0)
    diff = diff / dist_safe[:, :, np.newaxis]
    # Sum over neighbors
    sep_force = np.sum(diff * mask_sep[:, :, np.newaxis], axis=1)
    
    # 2. Alignment
    mask_align = dist_matrix < r_align
    counts_align = np.sum(mask_align, axis=1, keepdims=True)
    counts_align[counts_align == 0] = 1 # Prevent division by zero
    # Average velocity of neighbors
    align_force = np.sum(vel[np.newaxis, :, :] * mask_align[:, :, np.newaxis], axis=1) / counts_align
    
    # 3. Cohesion
    mask_coh = dist_matrix < r_coh
    counts_coh = np.sum(mask_coh, axis=1, keepdims=True)
    counts_coh[counts_coh == 0] = 1
    # Average position of neighbors
    center_of_mass = np.sum(pos[np.newaxis, :, :] * mask_coh[:, :, np.newaxis], axis=1) / counts_coh
    coh_force = center_of_mass - pos
    
    # Add a global attractor to the center to keep them on screen
    center = np.array([py5.width/2, py5.height/2])
    center_force = (center - pos) * 0.005
    
    # Combine forces
    force = (sep_force * w_sep) + (align_force * w_align) + (coh_force * w_coh) + center_force
    
    # Limit force
    force_mag = np.linalg.norm(force, axis=1, keepdims=True)
    force_mag[force_mag == 0] = 1
    force = np.where(force_mag > max_force, (force / force_mag) * max_force, force)
    
    # Update velocity
    vel += force
    
    # Limit speed
    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    speed[speed == 0] = 1
    vel = np.where(speed > max_speed, (vel / speed) * max_speed, vel)
    
    # Update position
    pos += vel
    
    # Wrap around screen edges
    pos[:, 0] = np.mod(pos[:, 0], py5.width)
    pos[:, 1] = np.mod(pos[:, 1], py5.height)

def draw():
    global pos
    
    # Fade background slightly for glowing trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Update boids twice per frame for faster perceived motion
    update_boids()
    update_boids()
    
    # Additive glowing trails
    py5.blend_mode(py5.ADD)
    
    # Draw boids in buckets to optimize py5.points calls
    py5.stroke_weight(2)
    dom_color = np.argmax(colors[:, :3], axis=1)
    
    palette = [
        (255, 50, 50, 60),
        (50, 255, 50, 60),
        (50, 50, 255, 60)
    ]
    
    for i in range(3):
        mask = (dom_color == i)
        if np.any(mask):
            py5.stroke(*palette[i])
            py5.points(pos[mask])
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

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

NUM_BOIDS = 1200
BOX_SIZE = 800

# Boid parameters
MAX_SPEED = 6.0
MAX_FORCE = 0.1
PERCEPTION_RADIUS = 80.0
SEP_WEIGHT = 2.0
ALI_WEIGHT = 1.0
COH_WEIGHT = 1.0

# Boid states
pos = np.random.uniform(-BOX_SIZE/2, BOX_SIZE/2, (NUM_BOIDS, 3)).astype(np.float32)
vel = np.random.uniform(-1, 1, (NUM_BOIDS, 3)).astype(np.float32)

def limit(vectors, max_val):
    magnitudes = np.linalg.norm(vectors, axis=1, keepdims=True)
    mask = (magnitudes > max_val).flatten()
    vectors[mask] = (vectors[mask] / magnitudes[mask]) * max_val
    return vectors

def normalize(vectors):
    magnitudes = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid div by zero
    magnitudes[magnitudes == 0] = 1.0
    return vectors / magnitudes

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global pos, vel
    
    py5.background(10, 15, 20)
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width/2, py5.height/2, -200)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.3) * 0.2)
    
    # Fast Numpy vectorized Boids computation
    # Compute pairwise distance matrix
    # diffs[i, j] = pos[j] - pos[i]
    diffs = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]
    distsq = np.sum(diffs**2, axis=2)
    
    # Avoid self-comparison
    np.fill_diagonal(distsq, np.inf)
    
    # Mask for neighbors
    neighbor_mask = distsq < (PERCEPTION_RADIUS**2)
    neighbor_counts = np.sum(neighbor_mask, axis=1)[:, np.newaxis]
    neighbor_counts[neighbor_counts == 0] = 1.0 # Prevent division by zero
    
    # 1. Separation
    # Weight by 1/distsq for closer avoidance
    inv_distsq = 1.0 / distsq
    np.fill_diagonal(inv_distsq, 0) # Clear infs
    inv_distsq[~neighbor_mask] = 0
    # diffs is pos[j] - pos[i], so we want pos[i] - pos[j] which is -diffs
    sep_steer = np.sum(-diffs * inv_distsq[:, :, np.newaxis], axis=1)
    
    # 2. Alignment
    # Average velocity of neighbors
    ali_steer = np.zeros((NUM_BOIDS, 3), dtype=np.float32)
    masked_vel = vel[np.newaxis, :, :] * neighbor_mask[:, :, np.newaxis]
    ali_avg = np.sum(masked_vel, axis=1) / neighbor_counts
    
    # 3. Cohesion
    # Average position of neighbors
    masked_pos = pos[np.newaxis, :, :] * neighbor_mask[:, :, np.newaxis]
    coh_avg = np.sum(masked_pos, axis=1) / neighbor_counts
    coh_steer = coh_avg - pos
    
    # Compute steering forces: (desired - velocity)
    # Separation
    sep_steer = normalize(sep_steer) * MAX_SPEED - vel
    sep_steer = limit(sep_steer, MAX_FORCE) * SEP_WEIGHT
    
    # Alignment
    mask_ali = np.linalg.norm(ali_avg, axis=1) > 0
    ali_steer[mask_ali] = normalize(ali_avg[mask_ali]) * MAX_SPEED - vel[mask_ali]
    ali_steer = limit(ali_steer, MAX_FORCE) * ALI_WEIGHT
    
    # Cohesion
    mask_coh = np.linalg.norm(coh_steer, axis=1) > 0
    coh_steer[mask_coh] = normalize(coh_steer[mask_coh]) * MAX_SPEED - vel[mask_coh]
    coh_steer = limit(coh_steer, MAX_FORCE) * COH_WEIGHT
    
    # Repel from walls (keep in box)
    wall_repel = np.zeros_like(pos)
    wall_repel[pos > BOX_SIZE/2] = -MAX_SPEED
    wall_repel[pos < -BOX_SIZE/2] = MAX_SPEED
    wall_steer = wall_repel - vel
    wall_steer = limit(wall_steer, MAX_FORCE * 2.0)
    
    # Update physics
    accel = sep_steer + ali_steer + coh_steer + wall_steer
    vel += accel
    vel = limit(vel, MAX_SPEED)
    pos += vel
    
    # Rendering
    py5.no_stroke()
    py5.ambient_light(50, 50, 50)
    py5.directional_light(200, 60, 100, 1, 1, -1)
    py5.directional_light(320, 80, 80, -1, -1, 1)
    
    for i in range(NUM_BOIDS):
        px, py_c, pz = pos[i]
        vx, vy, vz = vel[i]
        
        py5.push_matrix()
        py5.translate(px, py_c, pz)
        
        # Orient boid to its velocity vector
        theta = py5.atan2(vy, vx)
        phi = py5.atan2(vz, np.sqrt(vx*vx + vy*vy))
        
        py5.rotate_z(theta)
        py5.rotate_y(-phi)
        
        # Color based on spatial location and velocity
        speed = np.linalg.norm(vel[i])
        hue = (px * 0.2 + py_c * 0.2 + t * 50) % 360
        py5.fill(hue, 80, 50 + speed * 10)
        
        # Draw a pyramid for the boid
        py5.begin_shape(py5.TRIANGLES)
        
        s = 8 # scale
        
        # Top
        py5.vertex(s*2, 0, 0)
        py5.vertex(-s, -s, -s)
        py5.vertex(-s, s, -s)
        
        # Bottom
        py5.vertex(s*2, 0, 0)
        py5.vertex(-s, s, s)
        py5.vertex(-s, -s, s)
        
        # Left
        py5.vertex(s*2, 0, 0)
        py5.vertex(-s, -s, -s)
        py5.vertex(-s, -s, s)
        
        # Right
        py5.vertex(s*2, 0, 0)
        py5.vertex(-s, s, -s)
        py5.vertex(-s, s, s)
        
        py5.end_shape()
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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

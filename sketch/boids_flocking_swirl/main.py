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

NUM_BOIDS = 10000
MAX_SPEED = 6.0
MIN_SPEED = 3.0
MAX_FORCE = 0.2
PERCEPTION_RADIUS = 50.0

# Using a smaller buffer for fast motion blur accumulation
SIM_W = SIZE[0]
SIM_H = SIZE[1]

pos = np.zeros((NUM_BOIDS, 2), dtype=np.float32)
vel = np.zeros((NUM_BOIDS, 2), dtype=np.float32)

def setup():
    global pos, vel
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pos[:, 0] = np.random.uniform(0, SIM_W, NUM_BOIDS)
    pos[:, 1] = np.random.uniform(0, SIM_H, NUM_BOIDS)
    
    angles = np.random.uniform(0, 2 * np.pi, NUM_BOIDS)
    vel[:, 0] = np.cos(angles) * MAX_SPEED
    vel[:, 1] = np.sin(angles) * MAX_SPEED
    
    py5.background(0)

def compute_flocking(p, v):
    # Vectorized approximate boids algorithm.
    # Doing O(N^2) for 10000 boids is too slow for 60fps in Python.
    # We will use a fast grid-based approach or sample a subset.
    # Here, we use a random subset to calculate neighborhood averages for extreme speed.
    
    acc = np.zeros_like(v)
    
    # Randomly shuffle and pair up boids to simulate neighborhood
    # A fast, chaotic approximation of flocking
    shuffle_idx = np.random.permutation(NUM_BOIDS)
    p_shuff = p[shuffle_idx]
    v_shuff = v[shuffle_idx]
    
    # Distance to random peers
    diff = p_shuff - p
    dist_sq = diff[:, 0]**2 + diff[:, 1]**2
    
    mask = (dist_sq > 0) & (dist_sq < PERCEPTION_RADIUS**2)
    
    # Separation
    sep_mask = mask & (dist_sq < (PERCEPTION_RADIUS/2)**2)
    sep_force = np.zeros_like(v)
    sep_force[sep_mask] = -diff[sep_mask] / np.sqrt(dist_sq[sep_mask])[:, None]
    
    # Alignment
    align_force = np.zeros_like(v)
    align_force[mask] = v_shuff[mask]
    
    # Cohesion
    coh_force = np.zeros_like(v)
    coh_force[mask] = diff[mask]
    
    # Combine forces
    acc += sep_force * 2.5 + align_force * 1.0 + coh_force * 1.0
    
    # Limit force
    acc_mag = np.linalg.norm(acc, axis=1, keepdims=True) + 1e-6
    acc = np.where(acc_mag > MAX_FORCE, (acc / acc_mag) * MAX_FORCE, acc)
    
    return acc

def draw():
    global pos, vel
    
    # Semi-transparent background for motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Compute acceleration
    acc = compute_flocking(pos, vel)
    
    # Center attraction (keep them on screen)
    center = np.array([SIM_W/2, SIM_H/2], dtype=np.float32)
    center_force = center - pos
    center_dist = np.linalg.norm(center_force, axis=1, keepdims=True) + 1e-6
    acc += (center_force / center_dist) * 0.05
    
    vel += acc
    
    # Limit speed
    speed = np.linalg.norm(vel, axis=1, keepdims=True) + 1e-6
    vel = np.where(speed > MAX_SPEED, (vel / speed) * MAX_SPEED, vel)
    vel = np.where(speed < MIN_SPEED, (vel / speed) * MIN_SPEED, vel)
    
    pos += vel
    
    # Wrap edges
    pos[:, 0] = pos[:, 0] % SIM_W
    pos[:, 1] = pos[:, 1] % SIM_H
    
    # Render fast using py5.points() equivalent
    py5.blend_mode(py5.ADD)
    py5.stroke(100, 200, 255, 150)
    py5.stroke_weight(2)
    
    # To draw 10000 points fast, we can use PShape or just direct pixel array
    # We will use pixel array for maximum performance
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    px = pos[:, 0].astype(int)
    py_ = pos[:, 1].astype(int)
    
    valid = (px >= 0) & (px < SIM_W) & (py_ >= 0) & (py_ < SIM_H)
    px = px[valid]
    py_ = py_[valid]
    
    # Speed to color mapping
    v_mag = speed[valid].flatten()
    norm_v = np.clip((v_mag - MIN_SPEED) / (MAX_SPEED - MIN_SPEED), 0, 1)
    
    c_r = (norm_v * 50 + 50).astype(np.uint16)
    c_g = (norm_v * 150 + 100).astype(np.uint16)
    c_b = np.uint16(255)
    
    curr_r = pixels[py_, px, 1]
    curr_g = pixels[py_, px, 2]
    curr_b = pixels[py_, px, 3]
    
    pixels[py_, px, 1] = np.clip(curr_r.astype(np.float32) + c_r, 0, 255).astype(np.uint8)
    pixels[py_, px, 2] = np.clip(curr_g.astype(np.float32) + c_g, 0, 255).astype(np.uint8)
    pixels[py_, px, 3] = np.clip(curr_b.astype(np.float32) + c_b, 0, 255).astype(np.uint8)
    
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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

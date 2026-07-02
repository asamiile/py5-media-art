from pathlib import Path
import shutil
import subprocess
import sys
import math
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_BOIDS = 1500
MAX_SPEED = 12.0
MAX_FORCE = 0.5
PERCEPTION_RADIUS = 150.0
SEPARATION_RADIUS = 40.0

pos = None
vel = None

def setup():
    global pos, vel
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 0, 16)
    
    pos = np.random.uniform(0, [py5.width, py5.height], (NUM_BOIDS, 2))
    # Random angles
    angles = np.random.uniform(0, 2*np.pi, NUM_BOIDS)
    speed = np.random.uniform(2, MAX_SPEED, NUM_BOIDS)
    vel = np.column_stack((np.cos(angles)*speed, np.sin(angles)*speed))

def update_boids():
    global pos, vel
    
    # Calculate all pairwise distances squared
    # Broadcasting magic: shape (N, N, 2)
    diffs = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
    dist_sq = np.sum(diffs**2, axis=-1)
    
    # Ignore self by setting diagonal to infinity
    np.fill_diagonal(dist_sq, np.inf)
    
    # Masks for neighbors
    perception_mask = dist_sq < PERCEPTION_RADIUS**2
    separation_mask = dist_sq < SEPARATION_RADIUS**2
    
    # Counts of neighbors
    counts_perc = np.sum(perception_mask, axis=1)
    counts_sep = np.sum(separation_mask, axis=1)
    
    # -- ALIGNMENT --
    # Average velocity of neighbors
    align_force = np.zeros_like(vel)
    mask = counts_perc > 0
    
    if np.any(mask):
        sum_vel = perception_mask @ vel
        avg_vel = sum_vel[mask] / counts_perc[mask][:, np.newaxis]
        # Steer towards avg_vel
        # Normalize
        speeds = np.linalg.norm(avg_vel, axis=1, keepdims=True)
        speeds[speeds == 0] = 1.0
        desired_vel = (avg_vel / speeds) * MAX_SPEED
        steer = desired_vel - vel[mask]
        
        # Limit force
        steer_speeds = np.linalg.norm(steer, axis=1, keepdims=True)
        steer_speeds[steer_speeds == 0] = 1.0
        steer = np.where(steer_speeds > MAX_FORCE, (steer / steer_speeds) * MAX_FORCE, steer)
        align_force[mask] = steer
        
    # -- COHESION --
    # Average position of neighbors
    cohesion_force = np.zeros_like(vel)
    if np.any(mask):
        sum_pos = perception_mask @ pos
        avg_pos = sum_pos[mask] / counts_perc[mask][:, np.newaxis]
        # Steer towards avg_pos
        desired_vel = avg_pos - pos[mask]
        speeds = np.linalg.norm(desired_vel, axis=1, keepdims=True)
        speeds[speeds == 0] = 1.0
        desired_vel = (desired_vel / speeds) * MAX_SPEED
        steer = desired_vel - vel[mask]
        
        # Limit force
        steer_speeds = np.linalg.norm(steer, axis=1, keepdims=True)
        steer_speeds[steer_speeds == 0] = 1.0
        steer = np.where(steer_speeds > MAX_FORCE, (steer / steer_speeds) * MAX_FORCE, steer)
        cohesion_force[mask] = steer
        
    # -- SEPARATION --
    separation_force = np.zeros_like(vel)
    mask_sep = counts_sep > 0
    if np.any(mask_sep):
        # Weight by 1/distance
        # Safe division
        d = np.sqrt(dist_sq)
        d[d == 0] = 1.0
        weight = 1.0 / d
        weight[~separation_mask] = 0.0
        
        # We need the vector pointing AWAY from neighbors
        # diffs is (pos_i - pos_j), which is already away from j
        weighted_diffs = diffs * weight[:, :, np.newaxis]
        sum_diffs = np.sum(weighted_diffs, axis=1)
        
        avg_diffs = sum_diffs[mask_sep] / counts_sep[mask_sep][:, np.newaxis]
        
        speeds = np.linalg.norm(avg_diffs, axis=1, keepdims=True)
        speeds[speeds == 0] = 1.0
        desired_vel = (avg_diffs / speeds) * MAX_SPEED
        steer = desired_vel - vel[mask_sep]
        
        # Limit force
        steer_speeds = np.linalg.norm(steer, axis=1, keepdims=True)
        steer_speeds[steer_speeds == 0] = 1.0
        steer = np.where(steer_speeds > MAX_FORCE, (steer / steer_speeds) * MAX_FORCE, steer)
        separation_force[mask_sep] = steer
        
    # Weights
    vel += align_force * 1.0 + cohesion_force * 1.0 + separation_force * 1.5
    
    # Limit global speed
    speeds = np.linalg.norm(vel, axis=1, keepdims=True)
    speeds[speeds == 0] = 1.0
    vel = np.where(speeds > MAX_SPEED, (vel / speeds) * MAX_SPEED, vel)
    
    pos += vel
    
    # Wrap around
    pos = np.mod(pos, [py5.width, py5.height])

def draw():
    global pos, vel
    
    # Motion blur
    py5.fill(5, 0, 16, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Perturb the parameters slightly over time for more dynamic behavior
    t = py5.frame_count / TOTAL_FRAMES
    
    update_boids()
    
    # Draw boids
    # Color based on angle
    angles = np.arctan2(vel[:, 1], vel[:, 0])
    # Map angle (-pi to pi) to a nice cyan-magenta-blue range
    # Let's say Hue ranges around Cyan (0.5 in HSB) to Magenta (0.83)
    # We will compute RGB directly to avoid looping in py5
    # angle_norm = (angles + np.pi) / (2 * np.pi)
    
    py5.color_mode(py5.HSB, 1.0)
    
    py5.no_stroke()
    
    for i in range(NUM_BOIDS):
        a = (angles[i] + np.pi) / (2 * np.pi)
        # Hue: 0.5 (Cyan) to 0.85 (Magenta)
        h = 0.5 + 0.35 * a
        py5.fill(h, 0.8, 1.0, 0.6) # Alpha 0.6
        
        # Draw a little triangle pointing in direction of velocity
        x, y = pos[i]
        v = vel[i] / np.linalg.norm(vel[i])
        
        size = 12.0
        p1 = (x + v[0] * size, y + v[1] * size)
        p2 = (x - v[0] * size/2 - v[1] * size/2, y - v[1] * size/2 + v[0] * size/2)
        p3 = (x - v[0] * size/2 + v[1] * size/2, y - v[1] * size/2 - v[0] * size/2)
        
        py5.triangle(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])

    py5.color_mode(py5.RGB, 255) # Reset
    
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

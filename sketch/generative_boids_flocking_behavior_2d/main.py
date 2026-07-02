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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_BOIDS = 1500
MAX_SPEED = 6.0
MAX_FORCE = 0.15
PERCEPTION = 80.0

pos = np.zeros((NUM_BOIDS, 2), dtype=np.float32)
vel = np.zeros((NUM_BOIDS, 2), dtype=np.float32)
acc = np.zeros((NUM_BOIDS, 2), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    # Initialize randomly
    for i in range(NUM_BOIDS):
        pos[i] = [py5.random(py5.width), py5.random(py5.height)]
        angle = py5.random(py5.TWO_PI)
        vel[i] = [py5.cos(angle) * MAX_SPEED, py5.sin(angle) * MAX_SPEED]

def update_boids():
    global pos, vel, acc
    
    # For performance, we do an optimized numpy approach or simplified approach
    # We will pick a random subset of boids to interact with to save time
    # (Since N=1500, full O(N^2) is 2.2 million iterations, maybe slow for 60fps in pure Python)
    # Using numpy broadcasting for distance
    
    # Reset acc
    acc.fill(0)
    
    # Vectorized computation of flocking rules
    # To keep it fast in numpy without a spatial grid, we compute distance matrices in batches
    BATCH = 300
    for i in range(0, NUM_BOIDS, BATCH):
        end = min(i + BATCH, NUM_BOIDS)
        
        # Shape (BATCH, 1, 2) and (1, NUM_BOIDS, 2)
        diff = pos[i:end, np.newaxis, :] - pos[np.newaxis, :, :]
        dist_sq = diff[:, :, 0]**2 + diff[:, :, 1]**2
        
        # Mask out self and out-of-perception
        mask = (dist_sq > 0.1) & (dist_sq < PERCEPTION**2)
        
        # Separation
        sep_mask = mask & (dist_sq < (PERCEPTION * 0.4)**2)
        # diff is pointing from neighbor to i (if pos[i] - pos[j])
        sep_forces = diff * sep_mask[:, :, np.newaxis]
        # Weight by inverse distance (approximate to avoid div 0)
        sep_forces /= (dist_sq[:, :, np.newaxis] + 1.0)
        sep_sum = np.sum(sep_forces, axis=1)
        
        # Alignment
        ali_vel = vel[np.newaxis, :, :] * mask[:, :, np.newaxis]
        ali_sum = np.sum(ali_vel, axis=1)
        
        # Cohesion
        coh_pos = pos[np.newaxis, :, :] * mask[:, :, np.newaxis]
        counts = np.sum(mask, axis=1, keepdims=True)
        counts[counts == 0] = 1 # prevent div 0
        coh_sum = np.sum(coh_pos, axis=1) / counts - pos[i:end]
        
        # Apply forces (simplified steering: steer = desired - velocity)
        # Weights: sep=2.0, ali=1.0, coh=1.0
        
        for idx, k in enumerate(range(i, end)):
            # Separation steering
            sx, sy = sep_sum[idx]
            if sx != 0 or sy != 0:
                mag = (sx**2 + sy**2)**0.5
                sx = (sx / mag) * MAX_SPEED - vel[k, 0]
                sy = (sy / mag) * MAX_SPEED - vel[k, 1]
                smag = (sx**2 + sy**2)**0.5
                if smag > MAX_FORCE:
                    sx = sx / smag * MAX_FORCE
                    sy = sy / smag * MAX_FORCE
                acc[k, 0] += sx * 2.5
                acc[k, 1] += sy * 2.5
                
            # Alignment steering
            ax, ay = ali_sum[idx]
            if ax != 0 or ay != 0:
                mag = (ax**2 + ay**2)**0.5
                ax = (ax / mag) * MAX_SPEED - vel[k, 0]
                ay = (ay / mag) * MAX_SPEED - vel[k, 1]
                amag = (ax**2 + ay**2)**0.5
                if amag > MAX_FORCE:
                    ax = ax / amag * MAX_FORCE
                    ay = ay / amag * MAX_FORCE
                acc[k, 0] += ax * 1.5
                acc[k, 1] += ay * 1.5
                
            # Cohesion steering
            cx, cy = coh_sum[idx]
            if cx != 0 or cy != 0:
                mag = (cx**2 + cy**2)**0.5
                cx = (cx / mag) * MAX_SPEED - vel[k, 0]
                cy = (cy / mag) * MAX_SPEED - vel[k, 1]
                cmag = (cx**2 + cy**2)**0.5
                if cmag > MAX_FORCE:
                    cx = cx / cmag * MAX_FORCE
                    cy = cy / cmag * MAX_FORCE
                acc[k, 0] += cx * 1.0
                acc[k, 1] += cy * 1.0

    # Physics update
    vel += acc
    
    # Speed limit
    v_sq = vel[:, 0]**2 + vel[:, 1]**2
    limit_mask = v_sq > MAX_SPEED**2
    if np.any(limit_mask):
        v_mag = np.sqrt(v_sq[limit_mask])
        vel[limit_mask, 0] = (vel[limit_mask, 0] / v_mag) * MAX_SPEED
        vel[limit_mask, 1] = (vel[limit_mask, 1] / v_mag) * MAX_SPEED
        
    pos += vel
    
    # Screen wrapping
    pos[:, 0] = pos[:, 0] % py5.width
    pos[:, 1] = pos[:, 1] % py5.height


def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(3)
    
    update_boids()
    
    # Draw boids
    # Color based on velocity angle
    angles = np.arctan2(vel[:, 1], vel[:, 0])
    hues = (angles / py5.TWO_PI * 360 + 360 + py5.frame_count) % 360
    
    for i in range(NUM_BOIDS):
        px, py_pos = pos[i, 0], pos[i, 1]
        vx, vy = vel[i, 0], vel[i, 1]
        
        # Tail
        tail_x = px - vx * 3
        tail_y = py_pos - vy * 3
        
        # To avoid drawing long lines when wrapping
        if abs(px - tail_x) < py5.width/2 and abs(py_pos - tail_y) < py5.height/2:
            py5.stroke(hues[i], 90, 80, 80)
            py5.line(px, py_pos, tail_x, tail_y)
            
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

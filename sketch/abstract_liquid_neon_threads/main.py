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

NUM_PARTICLES = 15000

# Using NumPy for high-performance vectorized physics
pos_x = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
pos_y = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
vel_x = np.zeros(NUM_PARTICLES)
vel_y = np.zeros(NUM_PARTICLES)
old_x = pos_x.copy()
old_y = pos_y.copy()

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global pos_x, pos_y, vel_x, vel_y, old_x, old_y
    
    # Motion blur using semi-transparent background
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 8)  # Leave long trails
    py5.rect(0, 0, py5.width, py5.height)
    
    time = py5.frame_count * 0.02
    
    # 4 orbiting gravity wells
    wells_x = [
        py5.width / 2 + np.cos(time * 1.5) * 600,
        py5.width / 2 + np.sin(time * 1.1) * 800,
        py5.width / 2 + np.cos(time * 0.8) * 400,
        py5.width / 2 + np.sin(time * 1.3) * 500,
    ]
    wells_y = [
        py5.height / 2 + np.sin(time * 1.5) * 600,
        py5.height / 2 + np.cos(time * 1.1) * 800,
        py5.height / 2 + np.sin(time * 0.8) * 400,
        py5.height / 2 + np.cos(time * 1.3) * 500,
    ]
    
    wells_mass = [
        np.sin(time) * 1500,
        np.cos(time * 0.7) * 2000,
        np.sin(time * 1.3) * 1800,
        np.cos(time * 0.9) * 2500,
    ]
    
    # Save old positions
    old_x[:] = pos_x
    old_y[:] = pos_y
    
    # Apply forces
    for wx, wy, wmass in zip(wells_x, wells_y, wells_mass):
        dx = wx - pos_x
        dy = wy - pos_y
        dist_sq = dx**2 + dy**2 + 5000  # Softening parameter to prevent infinity
        force = wmass / dist_sq
        vel_x += dx * force
        vel_y += dy * force
        
    # Friction
    vel_x *= 0.95
    vel_y *= 0.95
    
    pos_x += vel_x
    pos_y += vel_y
    
    # Boundaries (wrap around)
    pos_x = np.where(pos_x < 0, py5.width, pos_x)
    pos_x = np.where(pos_x > py5.width, 0, pos_x)
    pos_y = np.where(pos_y < 0, py5.height, pos_y)
    pos_y = np.where(pos_y > py5.height, 0, pos_y)
    
    # Disconnect lines if wrapped
    wrapped = (np.abs(pos_x - old_x) > py5.width / 2) | (np.abs(pos_y - old_y) > py5.height / 2)
    old_x[wrapped] = pos_x[wrapped]
    old_y[wrapped] = pos_y[wrapped]

    # Draw
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    speeds = np.sqrt(vel_x**2 + vel_y**2)
    
    # Vectorized drawing using PShape or loop
    # For performance, we map arrays directly to geometry
    py5.begin_shape(py5.LINES)
    for i in range(NUM_PARTICLES):
        # Color based on speed and position
        h = (speeds[i] * 10 + time * 50) % 360
        s = 80
        b = np.clip(speeds[i] * 5 + 50, 0, 100)
        
        py5.stroke(h, s, b, 50)
        py5.vertex(old_x[i], old_y[i])
        py5.vertex(pos_x[i], pos_y[i])
    py5.end_shape()

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

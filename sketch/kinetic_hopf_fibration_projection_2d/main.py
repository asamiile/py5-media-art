from pathlib import Path
import shutil
import subprocess
import sys
import random
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

# Parameters
NUM_RINGS = 300
POINTS_PER_RING = 300
TOTAL_POINTS = NUM_RINGS * POINTS_PER_RING

# State
points_4d = np.zeros((TOTAL_POINTS, 4))
colors = np.zeros((TOTAL_POINTS, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # The Hopf fibration maps (eta, xi1, xi2) to 4D hypersphere (S3)
    # We will vary eta to get different rings
    # eta in [0, pi/2]
    # xi1, xi2 in [0, 2pi]
    
    idx = 0
    for r in range(NUM_RINGS):
        eta = np.random.uniform(0.1, np.pi/2 - 0.1) # Avoid exact poles
        xi2 = np.random.uniform(0, 2 * np.pi) # Phase offset for the ring
        
        # Color based on eta
        hue = eta / (np.pi/2)
        r_col = 255 * (0.5 + 0.5 * np.cos(hue * np.pi * 2))
        g_col = 255 * (0.5 + 0.5 * np.cos(hue * np.pi * 2 + 2.09)) # 120 deg
        b_col = 255 * (0.5 + 0.5 * np.cos(hue * np.pi * 2 + 4.18)) # 240 deg
        
        for p in range(POINTS_PER_RING):
            xi1 = (p / POINTS_PER_RING) * 2 * np.pi
            
            # Hopf map to S3
            x1 = np.cos(xi1 + xi2) * np.sin(eta)
            x2 = np.sin(xi1 + xi2) * np.sin(eta)
            x3 = np.cos(xi1 - xi2) * np.cos(eta)
            x4 = np.sin(xi1 - xi2) * np.cos(eta)
            
            points_4d[idx] = [x1, x2, x3, x4]
            colors[idx] = [r_col, g_col, b_col]
            idx += 1

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    # Motion blur
    py5.fill(5, 5, 10, 80)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # 4D Rotation matrix (rotate in X1-X4 plane)
    cos_t = np.cos(t)
    sin_t = np.sin(t)
    
    # A simple 4D rotation
    rot_4d = np.array([
        [cos_t, 0, 0, -sin_t],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [sin_t, 0, 0, cos_t]
    ])
    
    rotated_4d = points_4d @ rot_4d.T
    
    # Stereographic projection from 4D to 3D
    # p3d = p4d[0:3] / (1 - p4d[3])
    denom = 1.0 - rotated_4d[:, 3] * 0.99 # prevent div by zero
    x3d = rotated_4d[:, 0] / denom
    y3d = rotated_4d[:, 1] / denom
    z3d = rotated_4d[:, 2] / denom
    
    # 3D Rotation (rotate around Y and X to show it off)
    t2 = t * 0.7
    cos_t2 = np.cos(t2)
    sin_t2 = np.sin(t2)
    
    # Rot Y
    x3d_rot = x3d * cos_t2 - z3d * sin_t2
    z3d_rot = x3d * sin_t2 + z3d * cos_t2
    
    # Rot X
    y3d_rot = y3d * cos_t2 - z3d_rot * sin_t2
    z3d_final = y3d * sin_t2 + z3d_rot * cos_t2
    
    # Project to 2D
    fov = 800.0
    z_offset = 3.5
    z_proj = z3d_final + z_offset
    
    x2d = (x3d_rot / z_proj) * fov + SIZE[0]/2
    y2d = (y3d_rot / z_proj) * fov + SIZE[1]/2
    
    # Draw points
    # Format into groups of size POINTS_PER_RING
    # Using points since drawing continuous rings correctly requires order and depth sorting.
    # To avoid depth sorting artifacts, additive blending with dense points is best.
    
    x2d_rings = x2d.reshape((NUM_RINGS, POINTS_PER_RING))
    y2d_rings = y2d.reshape((NUM_RINGS, POINTS_PER_RING))
    
    py5.stroke_weight(2)
    
    # We loop over rings because we want them continuous, but points is faster
    # Actually, rendering 90,000 points natively is instant.
    points_array = np.column_stack((x2d, y2d))
    
    # Group by color buckets for speed
    py5.stroke(255, 100, 100, 150)
    mask_r = colors[:, 0] > 180
    if np.any(mask_r):
        py5.begin_shape(py5.POINTS)
        py5.vertices(points_array[mask_r])
        py5.end_shape()
        
    py5.stroke(100, 255, 100, 150)
    mask_g = colors[:, 1] > 180
    if np.any(mask_g):
        py5.begin_shape(py5.POINTS)
        py5.vertices(points_array[mask_g])
        py5.end_shape()
        
    py5.stroke(100, 100, 255, 150)
    mask_b = colors[:, 2] > 180
    if np.any(mask_b):
        py5.begin_shape(py5.POINTS)
        py5.vertices(points_array[mask_b])
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Data for splines
NUM_STRINGS = 15
POINTS_PER_STRING = 30
strings = []


def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize random seeds for paths
    py5.random_seed(10)
    for i in range(NUM_STRINGS):
        strings.append({
            'seed_x': py5.random(1000),
            'seed_y': py5.random(1000),
            'seed_z': py5.random(1000),
            'hue': py5.random(180, 280)  # cool blues and purples
        })


def draw():
    py5.background(5, 5, 10)
    
    py5.translate(py5.width / 2, py5.height / 2, -300)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    t = py5.frame_count * 0.015
    
    all_points = []
    
    # Calculate all points
    py5.no_fill()
    py5.stroke_weight(3)
    
    for s in strings:
        py5.stroke(s['hue'], 80, 80, 70)
        py5.begin_shape()
        
        pts = []
        for p in range(POINTS_PER_STRING):
            # parametric noise
            nx = s['seed_x'] + p * 0.05
            ny = s['seed_y'] + p * 0.05
            nz = s['seed_z'] + p * 0.05
            
            x = (py5.os_noise(nx, t) - 0.5) * 2500
            y = (py5.os_noise(ny, t) - 0.5) * 2500
            z = (py5.os_noise(nz, t) - 0.5) * 2500
            
            py5.curve_vertex(x, y, z)
            pts.append((x, y, z, s['hue']))
            
            # extra end vertices for proper curves
            if p == 0 or p == POINTS_PER_STRING - 1:
                py5.curve_vertex(x, y, z)
                
        py5.end_shape()
        all_points.extend(pts)
        
    # Draw connections (entanglements)
    py5.stroke_weight(1.5)
    all_pts_np = np.array([p[:3] for p in all_points])
    
    # compute pairwise distances
    # A simple nested loop is slow, but for ~450 points, it's fast enough in numpy
    if len(all_pts_np) > 0:
        diffs = all_pts_np[:, np.newaxis, :] - all_pts_np[np.newaxis, :, :]
        sq_dists = np.sum(diffs**2, axis=-1)
        
        threshold = 200**2
        mask = (sq_dists < threshold) & (sq_dists > 0)
        
        # draw lines for mask
        py5.begin_shape(py5.LINES)
        indices = np.argwhere(mask)
        # to avoid double drawing, only i < j
        for i, j in indices:
            if i < j:
                p1 = all_points[i]
                p2 = all_points[j]
                
                # mix hues or use bright cyan
                dist_ratio = 1.0 - (sq_dists[i, j] / threshold)
                alpha = dist_ratio * 100
                
                py5.stroke(180, 50, 100, alpha)
                py5.vertex(p1[0], p1[1], p1[2])
                py5.vertex(p2[0], p2[1], p2[2])
        py5.end_shape()
        
    # Draw particle nodes
    py5.stroke_weight(5)
    py5.begin_shape(py5.POINTS)
    for p in all_points:
        py5.stroke(p[3], 90, 100, 90)
        py5.vertex(p[0], p[1], p[2])
    py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

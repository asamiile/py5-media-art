from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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

points_data = None
fracture_centers = None
fracture_radii = None

def setup():
    global points_data, fracture_centers, fracture_radii
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    size_range = 1000
    N_points = 100000
    points_data = np.random.uniform(-size_range, size_range, (N_points, 3))
    
    lattice_spacing = 30
    points_data = np.round(points_data / lattice_spacing) * lattice_spacing
    points_data = np.unique(points_data, axis=0).astype(np.float32)
    
    fracture_centers = np.random.uniform(-size_range/2, size_range/2, (15, 3))
    fracture_radii = np.random.uniform(-500, 0, 15)

def draw():
    global points_data, fracture_radii
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    fracture_radii += 8.0
    
    displacements = np.zeros_like(points_data)
    for i in range(len(fracture_centers)):
        if fracture_radii[i] < 0:
            continue
        dist = np.linalg.norm(points_data - fracture_centers[i], axis=1)
        mask = (dist < fracture_radii[i]) & (dist > fracture_radii[i] - 350)
        
        direction = points_data[mask] - fracture_centers[i]
        norms = np.linalg.norm(direction, axis=1, keepdims=True)
        norms[norms == 0] = 1
        direction = direction / norms
        displacements[mask] += direction * 30.0
        
    current_points = (points_data + displacements).astype(np.float32)
    
    rx = py5.frame_count * 0.002
    ry = py5.frame_count * 0.003
    
    cx = np.cos(rx)
    sx = np.sin(rx)
    cy = np.cos(ry)
    sy = np.sin(ry)
    
    x = current_points[:, 0] * cy - current_points[:, 2] * sy
    z = current_points[:, 0] * sy + current_points[:, 2] * cy
    y = current_points[:, 1]
    
    y2 = y * cx - z * sx
    z2 = y * sx + z * cx
    
    z_offset = z2 + 1000
    z_offset[z_offset < 1] = 1
    
    fov = 800.0
    px = x / z_offset * fov + py5.width / 2
    py_coords = y2 / z_offset * fov + py5.height / 2
    
    projected_points = np.column_stack((px, py_coords)).astype(np.float32)
    
    stable_mask = np.linalg.norm(displacements, axis=1) < 0.1
    fractured_mask = ~stable_mask
    
    py5.stroke_weight(4)
    if np.any(stable_mask):
        py5.stroke(50, 200, 255, 200)
        py5.points(projected_points[stable_mask])
        
    py5.stroke_weight(6)
    if np.any(fractured_mask):
        py5.stroke(255, 100, 200, 255)
        py5.points(projected_points[fractured_mask])

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

py5.run_sketch()

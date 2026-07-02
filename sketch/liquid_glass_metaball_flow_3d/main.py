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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Performance optimization for marching cubes
# We use a point-cloud based "metaball" approximation to avoid heavy isosurface mesh generation in Python
NUM_POINTS = 30000
grid_points = None
point_colors = None

def setup():
    global grid_points, point_colors
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    np.random.seed(42)
    # Volumetric point cloud inside a cube
    x = np.random.uniform(-400, 400, NUM_POINTS)
    y = np.random.uniform(-400, 400, NUM_POINTS)
    z = np.random.uniform(-400, 400, NUM_POINTS)
    
    grid_points = np.column_stack((x, y, z))
    point_colors = np.random.uniform(0, 360, NUM_POINTS)

def draw():
    py5.background(5, 10, 15)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera rotation
    cam_angle = py5.frame_count * 0.015
    py5.rotate_x(py5.PI / 4 + np.sin(cam_angle) * 0.2)
    py5.rotate_y(cam_angle)
    
    t = py5.frame_count * 0.03
    
    # Metaball centers
    balls = [
        (np.sin(t*0.5) * 200, np.cos(t*0.7) * 200, np.sin(t*0.9) * 200, 40000), # x, y, z, mass
        (np.cos(t*0.6) * 250, np.sin(t*0.8) * 150, np.cos(t*0.4) * 250, 50000),
        (np.sin(t*0.4) * 150, np.cos(t*0.5) * 250, np.sin(t*0.8) * 150, 45000),
        (np.cos(t*0.7) * 200, np.sin(t*0.6) * 200, np.cos(t*0.5) * 200, 40000)
    ]
    
    # Calculate scalar field (Metaball formula)
    field = np.zeros(NUM_POINTS)
    for bx, by, bz, mass in balls:
        dist_sq = (grid_points[:, 0] - bx)**2 + (grid_points[:, 1] - by)**2 + (grid_points[:, 2] - bz)**2
        field += mass / (dist_sq + 1)
        
    # Isosurface threshold
    threshold = 1.0
    
    # Filter points near the isosurface
    valid_mask = (field > threshold - 0.2) & (field < threshold + 0.2)
    surface_points = grid_points[valid_mask]
    
    py5.stroke_weight(4)
    py5.begin_shape(py5.POINTS)
    
    for i in range(len(surface_points)):
        p = surface_points[i]
        
        # Calculate color based on position
        hue = (py5.remap(p[0], -400, 400, 180, 260) + py5.remap(p[1], -400, 400, 0, 100)) % 360
        bright = py5.remap(p[2], -400, 400, 40, 100)
        
        py5.stroke(hue, 90, bright, 80)
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

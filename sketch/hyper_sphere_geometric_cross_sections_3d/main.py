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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Generate 3D point cloud for a sphere using Fibonacci lattice
num_points = 50000
points = np.zeros((num_points, 3))
radius = 400

def setup():
    global points
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Fibonacci sphere
    phi = py5.PI * (3.0 - py5.sqrt(5.0))
    for i in range(num_points):
        y = 1 - (i / float(num_points - 1)) * 2
        r = py5.sqrt(1 - y * y)
        theta = phi * i
        
        points[i, 0] = py5.cos(theta) * r * radius
        points[i, 1] = y * radius
        points[i, 2] = py5.sin(theta) * r * radius
        
    py5.no_stroke()

def draw():
    py5.background(0, 0, 5)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Slowly rotate the entire structure
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_y(py5.frame_count * 0.005)
    
    py5.blend_mode(py5.ADD)
    
    # Plane 1: Scanning along Z
    z_offset = py5.sin(py5.frame_count * 0.02) * radius
    
    # Plane 2: Scanning along an angled plane
    ang = py5.frame_count * 0.015
    nx, ny, nz = py5.cos(ang), py5.sin(ang), 0.5
    
    # We will draw points that are close to these planes
    thickness = 10.0
    
    # For performance, use numpy to filter points
    dist1 = np.abs(points[:, 2] - z_offset)
    
    dot_prod = points[:, 0] * nx + points[:, 1] * ny + points[:, 2] * nz
    p2_offset = py5.cos(py5.frame_count * 0.025) * radius * 0.5
    dist2 = np.abs(dot_prod - p2_offset)
    
    mask1 = dist1 < thickness
    mask2 = dist2 < thickness
    
    # Base structure (very faint)
    py5.stroke(200, 50, 20, 30)
    py5.stroke_weight(1)
    py5.points(points)
    
    # Plane 1 points (Cyan)
    if np.any(mask1):
        py5.stroke(180, 80, 100, 90)
        py5.stroke_weight(4)
        py5.points(points[mask1])
        
    # Plane 2 points (Magenta)
    if np.any(mask2):
        py5.stroke(320, 80, 100, 90)
        py5.stroke_weight(4)
        py5.points(points[mask2])
        
    # Intersection points (White/Yellow glow)
    mask_intersect = mask1 & mask2
    if np.any(mask_intersect):
        py5.stroke(60, 40, 100, 100)
        py5.stroke_weight(10)
        py5.points(points[mask_intersect])

    py5.blend_mode(py5.BLEND)

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

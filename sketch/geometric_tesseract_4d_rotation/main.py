from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

# Generate 4D vertices for a tesseract
def generate_hypercube():
    points = []
    for i in range(16):
        # binary representation gives -1 or 1
        x = -1 if (i & 1) == 0 else 1
        y = -1 if (i & 2) == 0 else 1
        z = -1 if (i & 4) == 0 else 1
        w = -1 if (i & 8) == 0 else 1
        points.append(np.array([x, y, z, w], dtype=float))
    return points

points_4d = generate_hypercube()

# Edges connect vertices that differ by exactly 1 bit
edges = []
for i in range(16):
    for j in range(i + 1, 16):
        # Check if i and j differ by exactly one bit
        if (i ^ j) in [1, 2, 4, 8]:
            edges.append((i, j))

def rotate_4d(point, angle_xw, angle_yw, angle_zw):
    # XY, XZ, YZ are handled by py5.rotate_x/y/z after projection
    
    # XW rotation
    x = point[0]
    w = point[3]
    point[0] = x * np.cos(angle_xw) - w * np.sin(angle_xw)
    point[3] = x * np.sin(angle_xw) + w * np.cos(angle_xw)
    
    # YW rotation
    y = point[1]
    w = point[3]
    point[1] = y * np.cos(angle_yw) - w * np.sin(angle_yw)
    point[3] = y * np.sin(angle_yw) + w * np.cos(angle_yw)
    
    # ZW rotation
    z = point[2]
    w = point[3]
    point[2] = z * np.cos(angle_zw) - w * np.sin(angle_zw)
    point[3] = z * np.sin(angle_zw) + w * np.cos(angle_zw)
    
    return point

def project_4d_to_3d(point_4d):
    distance = 2.0
    w = 1.0 / (distance - point_4d[3])
    
    projection_matrix = np.array([
        [w, 0, 0, 0],
        [0, w, 0, 0],
        [0, 0, w, 0]
    ])
    
    projected = np.dot(projection_matrix, point_4d)
    return projected * 500  # Scale

def draw():
    py5.background(0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # 3D Rotations
    py5.rotate_x(t * py5.TWO_PI)
    py5.rotate_y(t * py5.TWO_PI * 1.5)
    py5.rotate_z(py5.sin(t * py5.TWO_PI) * py5.PI / 4)
    
    angle_xw = t * py5.TWO_PI * 2
    angle_yw = t * py5.TWO_PI
    angle_zw = py5.sin(t * py5.TWO_PI) * py5.PI
    
    projected_points = []
    
    for p in points_4d:
        rotated = rotate_4d(p.copy(), angle_xw, angle_yw, angle_zw)
        proj3d = project_4d_to_3d(rotated)
        projected_points.append(proj3d)
        
    py5.stroke_weight(6)
    
    # Draw edges
    for i, j in edges:
        p1 = projected_points[i]
        p2 = projected_points[j]
        
        # Color based on Z depth
        avg_z = (p1[2] + p2[2]) / 2
        hue = (180 + avg_z * 0.2 + t * 360) % 360
        brightness = py5.remap(avg_z, -1000, 1000, 40, 100)
        
        py5.stroke(hue, 80, brightness)
        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
        
    # Draw vertices
    py5.no_stroke()
    for p in projected_points:
        brightness = py5.remap(p[2], -1000, 1000, 50, 100)
        py5.fill(0, 0, 100, brightness)
        
        py5.push_matrix()
        py5.translate(p[0], p[1], p[2])
        py5.sphere(15)
        py5.pop_matrix()

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

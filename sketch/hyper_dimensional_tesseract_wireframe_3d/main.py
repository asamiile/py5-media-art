from pathlib import Path
import shutil
import subprocess
import sys
import math
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

# 4D Math projection
def matmul(a, b):
    colsA = len(a[0])
    rowsA = len(a)
    colsB = len(b[0])
    rowsB = len(b)
    
    if colsA != rowsB:
        return None
        
    result = [[0 for _ in range(colsB)] for _ in range(rowsA)]
    for i in range(rowsA):
        for j in range(colsB):
            sum_val = 0
            for k in range(colsA):
                sum_val += a[i][k] * b[k][j]
            result[i][j] = sum_val
    return result

points = []
edges = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global points, edges
    
    # 4D Hypercube vertices
    for i in range(16):
        x = -1 if (i & 1) == 0 else 1
        y = -1 if (i & 2) == 0 else 1
        z = -1 if (i & 4) == 0 else 1
        w = -1 if (i & 8) == 0 else 1
        points.append([[x], [y], [z], [w]])
        
    # Connect edges
    for i in range(16):
        for j in range(16):
            # If they differ by exactly one bit, they are connected
            diff = i ^ j
            if diff in (1, 2, 4, 8) and i < j:
                edges.append((i, j))

def draw():
    py5.background(10, 10, 15)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.02
    
    # Base 3D rotation
    py5.rotate_y(py5.sin(t * 0.3) * 0.5)
    py5.rotate_x(py5.cos(t * 0.4) * 0.5)
    
    angle = t
    
    # 4D Rotation matrices
    # XY rotation
    r_xy = [
        [math.cos(angle), -math.sin(angle), 0, 0],
        [math.sin(angle), math.cos(angle), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]
    
    # XW rotation
    r_xw = [
        [math.cos(angle), 0, 0, -math.sin(angle)],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [math.sin(angle), 0, 0, math.cos(angle)]
    ]
    
    # ZW rotation
    r_zw = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, math.cos(angle), -math.sin(angle)],
        [0, 0, math.sin(angle), math.cos(angle)]
    ]
    
    projected_3d = []
    
    # Process 4D points
    for p in points:
        # Apply 4D rotations
        rotated = matmul(r_xy, p)
        rotated = matmul(r_xw, rotated)
        rotated = matmul(r_zw, rotated)
        
        # Distance for stereographic projection
        distance = 3
        w = rotated[3][0]
        z_factor = 1 / (distance - w)
        
        projection_matrix = [
            [z_factor, 0, 0, 0],
            [0, z_factor, 0, 0],
            [0, 0, z_factor, 0]
        ]
        
        proj_3d = matmul(projection_matrix, rotated)
        
        # Scale for display
        scale = 600
        projected_3d.append([proj_3d[0][0] * scale, proj_3d[1][0] * scale, proj_3d[2][0] * scale])

    # Draw nodes
    py5.no_stroke()
    for i, p3d in enumerate(projected_3d):
        py5.push_matrix()
        py5.translate(p3d[0], p3d[1], p3d[2])
        hue = (180 + py5.sin(t + i)*60) % 360
        py5.fill(hue, 90, 100, 80)
        py5.sphere(12)
        py5.pop_matrix()
        
    # Draw edges
    py5.stroke_weight(4)
    for edge in edges:
        p1 = projected_3d[edge[0]]
        p2 = projected_3d[edge[1]]
        
        dist = math.dist(p1, p2)
        hue = (300 + py5.sin(dist * 0.01 - t * 2) * 60) % 360
        
        py5.stroke(hue, 90, 100, 60)
        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])


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

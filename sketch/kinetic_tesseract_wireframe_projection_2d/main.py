from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Tesseract vertices
points = []
for i in range(16):
    x = (i & 1) - 0.5
    y = ((i >> 1) & 1) - 0.5
    z = ((i >> 2) & 1) - 0.5
    w = ((i >> 3) & 1) - 0.5
    points.append(np.array([x, y, z, w]))
points = np.array(points)

def get_rotation_matrix_4d_xw(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [c, 0, 0, -s],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [s, 0, 0, c]
    ])
    
def get_rotation_matrix_4d_yw(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [1, 0, 0, 0],
        [0, c, 0, -s],
        [0, 0, 1, 0],
        [0, s, 0, c]
    ])
    
def get_rotation_matrix_4d_xy(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
    
def get_rotation_matrix_4d_zw(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, c, -s],
        [0, 0, s, c]
    ])

def connect(offset, i, j, projected):
    a = projected[i + offset]
    b = projected[j + offset]
    py5.line(float(a[0]), float(a[1]), float(b[0]), float(b[1]))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    # Trail effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(260, 90, 5, 20) # Deep violet background fade
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Angles for rotation
    angle_xw = t * py5.TWO_PI * 1.5
    angle_yw = t * py5.TWO_PI * 2.0
    angle_xy = t * py5.TWO_PI * 0.5
    angle_zw = t * py5.TWO_PI * 1.2
    
    rot_xw = get_rotation_matrix_4d_xw(angle_xw)
    rot_yw = get_rotation_matrix_4d_yw(angle_yw)
    rot_xy = get_rotation_matrix_4d_xy(angle_xy)
    rot_zw = get_rotation_matrix_4d_zw(angle_zw)
    
    projected = []
    
    for p in points:
        # Rotate in 4D
        rotated = rot_xw @ p
        rotated = rot_yw @ rotated
        rotated = rot_xy @ rotated
        rotated = rot_zw @ rotated
        
        # Distance from 4D "camera"
        distance = 2.5
        w = 1.0 / (distance - rotated[3])
        
        # Projection Matrix 4D -> 3D
        projection_4d = np.array([
            [w, 0, 0, 0],
            [0, w, 0, 0],
            [0, 0, w, 0]
        ])
        
        projected_3d = projection_4d @ rotated
        
        # Distance from 3D "camera"
        z = 1.0 / (2.0 - projected_3d[2])
        
        # Projection Matrix 3D -> 2D
        projection_3d = np.array([
            [z, 0, 0],
            [0, z, 0]
        ])
        
        projected_2d = projection_3d @ projected_3d
        
        # Scale to screen
        scale_factor = py5.width * 0.6
        projected_2d *= scale_factor
        
        projected.append(projected_2d)
        
    projected = np.array(projected)
    
    # Draw wireframe edges
    py5.stroke_weight(4)
    
    # Cycle colors (Pink to Cyan)
    hue = (300 + t * 120) % 360
    py5.stroke(hue, 90, 100, 80)
    
    # A tesseract has 32 edges. 
    # Connect nodes where their binary indices differ by exactly 1 bit.
    for i in range(16):
        for j in range(i + 1, 16):
            diff = i ^ j
            # If it's a power of 2, they differ by 1 bit, so they share an edge
            if diff in (1, 2, 4, 8):
                connect(0, i, j, projected)

    # Draw vertices
    py5.no_stroke()
    py5.fill((hue + 180) % 360, 90, 100, 90) # Opposite color for nodes
    for p in projected:
        py5.ellipse(float(p[0]), float(p[1]), 12, 12)

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
        import os
        os._exit(0)

py5.run_sketch()

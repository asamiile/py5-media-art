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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Torus knot parameters
P = 3
Q = 7
NUM_POINTS = 600
TUBE_RADIUS = 30
TUBE_DETAIL = 12

def evaluate_knot(theta):
    # Parametric equations for a Torus Knot
    r = py5.cos(Q * theta) + 2
    x = r * py5.cos(P * theta) * 100
    y = r * py5.sin(P * theta) * 100
    z = -py5.sin(Q * theta) * 100
    return np.array([x, y, z])

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Complex rotations to view the knot from all angles
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    py5.rotate_z(t * 0.2)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # We evaluate the knot curve and draw a tubular mesh around it
    for i in range(NUM_POINTS):
        theta1 = py5.TWO_PI * i / NUM_POINTS
        theta2 = py5.TWO_PI * (i + 1) / NUM_POINTS
        
        # Current point and next point on the knot
        p1 = evaluate_knot(theta1)
        p2 = evaluate_knot(theta2)
        
        # Calculate frenet frame (tangent, normal, binormal) to orient the tube
        tangent = p2 - p1
        t_len = np.linalg.norm(tangent)
        if t_len > 0:
            tangent /= t_len
            
        # A simple up vector to cross with tangent
        up = np.array([0.0, 1.0, 0.0])
        if abs(tangent[1]) > 0.99:
            up = np.array([1.0, 0.0, 0.0])
            
        normal = np.cross(tangent, up)
        n_len = np.linalg.norm(normal)
        if n_len > 0:
            normal /= n_len
            
        binormal = np.cross(tangent, normal)
        
        # Color pulsing along the knot
        hue = (i * 1.5 + py5.frame_count * 2) % 360
        py5.stroke(hue, 90, 100, 80)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(TUBE_DETAIL + 1):
            angle = py5.TWO_PI * j / TUBE_DETAIL
            
            # Circle offset in local space
            offset_x = py5.cos(angle) * TUBE_RADIUS
            offset_y = py5.sin(angle) * TUBE_RADIUS
            
            # Transform to world space for p1
            v1 = p1 + normal * offset_x + binormal * offset_y
            
            # Transform to world space for p2
            v2 = p2 + normal * offset_x + binormal * offset_y
            
            py5.vertex(v1[0], v1[1], v1[2])
            py5.vertex(v2[0], v2[1], v2[2])
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

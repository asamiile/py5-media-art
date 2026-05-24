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

NUM_RINGS = 18
NUM_POINTS = 360
t_angles = np.linspace(0, 2*np.pi, NUM_POINTS, endpoint=False)

def rot_matrix(x, y, z):
    cx, sx = np.cos(x), np.sin(x)
    cy, sy = np.cos(y), np.sin(y)
    cz, sz = np.cos(z), np.sin(z)
    
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    # Motion blur using semi-transparent background
    py5.push_matrix()
    py5.reset_matrix()
    py5.no_lights()
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()

    py5.translate(py5.width / 2, py5.height / 2, -400)
    
    time = py5.frame_count * 0.015
    
    # Global rotation
    py5.rotate_x(time * 0.15)
    py5.rotate_y(time * 0.25)
    py5.rotate_z(time * 0.1)
    
    ring_pts = []
    
    # Calculate absolute 3D coordinates for all rings
    for i in range(NUM_RINGS):
        r = 150 + i * 50
        base_x = r * np.cos(t_angles)
        base_y = r * np.sin(t_angles)
        base_z = np.zeros_like(base_x)
        
        pts = np.vstack([base_x, base_y, base_z])
        
        # Harmonic rotation speeds based on ring index
        speed_x = (i % 3 + 1) * 0.8
        speed_y = (i % 4 + 1) * 0.5
        speed_z = (i % 2 + 1) * 0.7
        
        rx = time * speed_x + i * 0.1
        ry = time * speed_y + i * 0.2
        rz = time * speed_z + i * 0.05
        
        # Apply 3D rotation
        R = rot_matrix(rx, ry, rz)
        rotated_pts = R @ pts
        ring_pts.append(rotated_pts)
        
    py5.blend_mode(py5.ADD)
    
    # Draw solid rings
    py5.stroke_weight(4)
    for i in range(NUM_RINGS):
        py5.stroke(45 + i * 2, 80, 100, 90) # Golden gradient
        py5.no_fill()
        py5.begin_shape()
        for j in range(NUM_POINTS):
            py5.vertex(*ring_pts[i][:, j])
        py5.end_shape(py5.CLOSE)
        
    # Draw energetic strings between adjacent rings
    py5.stroke_weight(1.5)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_RINGS - 1):
        # Vary twist phase per layer
        twist = int(np.sin(time * 1.5 + i) * 15) 
        
        for j in range(NUM_POINTS):
            # Only draw some lines to avoid blowing out to white
            if j % 3 != 0:
                continue
                
            py5.stroke(50 + i * 2, 40, 100, 40) # Lighter amber/gold
            py5.vertex(*ring_pts[i][:, j])
            
            next_j = (j + twist) % NUM_POINTS
            py5.vertex(*ring_pts[i+1][:, next_j])
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

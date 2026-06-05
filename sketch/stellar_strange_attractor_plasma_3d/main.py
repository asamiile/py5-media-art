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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Aizawa Attractor parameters
a = 0.95
b = 0.7
c = 0.6
d = 3.5
e = 0.25
f = 0.1

NUM_POINTS = 30000
points = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize points near origin
    for _ in range(NUM_POINTS):
        x = py5.random(-0.1, 0.1)
        y = py5.random(-0.1, 0.1)
        z = py5.random(-0.1, 0.1)
        points.append(np.array([x, y, z]))

def draw():
    py5.background(10, 0, 5) # Dark crimson/black
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.01
    
    py5.rotate_x(py5.PI/2 + np.sin(t)*0.2)
    py5.rotate_z(t * 1.5)
    
    py5.scale(250) # Scale up the attractor
    
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    dt = 0.03
    
    # Slowly morph the parameter 'c' to make it dynamic
    current_c = c + np.sin(t * 0.5) * 0.15
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    
    for i in range(NUM_POINTS):
        p = points[i]
        x, y, z = p[0], p[1], p[2]
        
        # Aizawa equations
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        dz = current_c + a * z - (z**3) / 3 - (x**2 + y**2) * (1 + e * z) + f * z * (x**3)
        
        nx = x + dx * dt
        ny = y + dy * dt
        nz = z + dz * dt
        
        points[i] = np.array([nx, ny, nz])
        
        # Color based on position and velocity
        vel = abs(dx) + abs(dy) + abs(dz)
        
        if vel > 2.0:
            py5.stroke(0, 150, 255, 60) # Electric Blue for fast particles
        elif nz > 0.5:
            py5.stroke(255, 200, 50, 40) # Solar Yellow
        else:
            py5.stroke(255, 80, 20, 30) # Fiery Orange
            
        py5.vertex(nx, ny, nz)
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

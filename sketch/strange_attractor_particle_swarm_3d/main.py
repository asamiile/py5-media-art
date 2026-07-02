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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points, num_points, dt
    num_points = 50000
    # Start all points close to each other
    points = np.random.randn(num_points, 3) * 0.1
    points[:, 0] += 0.1
    points[:, 1] += 0.1
    points[:, 2] += 20.0
    dt = 0.008

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global points, dt
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    
    # Calculate differentials for all points at once
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    
    # Update positions
    points[:, 0] += dx * dt
    points[:, 1] += dy * dt
    points[:, 2] += dz * dt
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.015
    py5.rotate_y(t)
    py5.rotate_x(0.3 + np.sin(t*0.5)*0.2)
    py5.rotate_z(np.cos(t*0.7)*0.1)
    
    py5.scale(18)
    
    # Offset attractor to center
    py5.translate(0, 0, -25)
    
    py5.stroke_weight(2)
    
    # Draw points
    py5.begin_shape(py5.POINTS)
    for i in range(num_points):
        # Color based on speed and z-position
        speed = np.sqrt(dx[i]**2 + dy[i]**2 + dz[i]**2)
        hue = (180 + speed * 0.8 + z[i] * 5 + t * 50) % 360
        py5.stroke(hue, 80, 100, 30)
        py5.vertex(x[i], y[i], z[i])
    py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

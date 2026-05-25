from pathlib import Path
import shutil
import subprocess
import sys
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

import numpy as np

num_particles = 15000
# Initial cylinder coordinates
radius = np.random.uniform(50, 400, num_particles)
theta = np.random.uniform(0, 2 * np.pi, num_particles)
heights = np.random.uniform(-400, 400, num_particles)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Use low opacity black for motion blur trails
    py5.background(10, 15, 10, 20)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Rotate camera over time
    py5.rotate_x(py5.PI / 6)
    py5.rotate_y(py5.frame_count * 0.01)
    
    global radius, theta, heights
    
    # Vector field dynamics
    # Speed of vortex depends on inverse of radius
    v_theta = 200.0 / (radius + 10)
    # Upward draft
    v_height = -150.0 / (radius + 20)
    # Inward pull
    v_radius = (radius - 150) * -0.01
    
    theta += v_theta * 0.02
    heights += v_height * 2.0
    radius += v_radius * 2.0
    
    # Add noise
    theta += np.random.normal(0, 0.02, num_particles)
    
    # Reset particles that go out of bounds
    reset_mask = (heights < -400) | (radius < 10)
    heights[reset_mask] = 400
    radius[reset_mask] = np.random.uniform(200, 500, np.sum(reset_mask))
    
    x = radius * np.cos(theta)
    y = heights
    z = radius * np.sin(theta)
    
    py5.stroke_weight(3)
    
    py5.begin_shape(py5.POINTS)
    for i in range(num_particles):
        # Color based on height and radius
        hue = (180 + (radius[i] / 500) * 120 - y[i] * 0.1) % 360
        py5.stroke(hue, 90, 100, 80)
        py5.vertex(x[i], y[i], z[i])
    py5.end_shape()

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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

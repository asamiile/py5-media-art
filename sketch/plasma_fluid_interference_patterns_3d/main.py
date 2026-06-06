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

# Grid settings
cols, rows = 150, 150
scl = 15
w = cols * scl
h = rows * scl

# Vectorized grid setup
x_coords = np.linspace(-w/2, w/2, cols)
y_coords = np.linspace(-h/2, h/2, rows)
X, Y = np.meshgrid(x_coords, y_coords)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(0, 0, 5)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera orbit
    cam_angle = py5.frame_count * 0.01
    py5.rotate_x(py5.PI / 3 + np.sin(cam_angle) * 0.2)
    py5.rotate_z(cam_angle * 1.5)
    
    t = py5.frame_count * 0.05
    
    # Origins of interference
    origins = [
        (np.sin(t*0.5) * 800, np.cos(t*0.4) * 800),
        (np.cos(t*0.6) * 600, np.sin(t*0.7) * 600),
        (np.sin(t*0.3) * 500, np.cos(t*0.8) * -500),
    ]
    
    Z = np.zeros_like(X)
    
    # Calculate interference pattern
    for ox, oy in origins:
        dist = np.sqrt((X - ox)**2 + (Y - oy)**2)
        Z += np.sin(dist * 0.02 - t * 2) * 100
        
    # Draw points
    py5.stroke_weight(4)
    py5.begin_shape(py5.POINTS)
    
    for i in range(rows):
        for j in range(cols):
            x = X[i, j]
            y = Y[i, j]
            z = Z[i, j]
            
            # Map height to hue and brightness
            hue = (py5.remap(z, -300, 300, 180, 360) + py5.frame_count) % 360
            bright = py5.remap(z, -300, 300, 30, 100)
            
            py5.stroke(hue, 90, bright, 90)
            py5.vertex(x, y, z)
            
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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

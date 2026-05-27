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
DURATION_SEC = 15  # 15s animation
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

dt = 0.01

NUM_LINES = 100
positions = None

def setup():
    global positions
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = (np.random.rand(NUM_LINES, 3) - 0.5) * 2.0

def draw():
    global positions
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 10)
    py5.no_stroke()
    
    # Draw background
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.push_matrix()
    py5.camera()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()
    py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.01
    
    py5.translate(py5.width/2, py5.height/2)
    py5.rotate_x(py5.PI / 3 + time * 0.2)
    py5.rotate_z(time * 0.5)
    
    # Scale up the attractor
    py5.scale(150)
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    for i in range(NUM_LINES):
        x, y, z = positions[i]
        
        # Aizawa equations
        dx = (z - b) * x - d * y
        dy = d * x + (z - b) * y
        dz = c + a * z - z**3 / 3 - (x**2 + y**2) * (1 + e * z) + f * z * x**3
        
        nx = x + dx * dt
        ny = y + dy * dt
        nz = z + dz * dt
        
        hue = (10 + (np.linalg.norm([nx, ny, nz]) * 50) + time * 50) % 360
        # restrict to fire colors: 0 (red) to 60 (yellow)
        fire_hue = hue % 60
        py5.stroke(fire_hue, 90, 100, 30)
        
        py5.line(x, y, z, nx, ny, nz)
        
        positions[i] = [nx, ny, nz]

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

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 80000

# Arrays for particles initialized near the origin
x = np.random.uniform(-0.1, 0.1, NUM_PARTICLES).astype(np.float32)
y = np.random.uniform(-0.1, 0.1, NUM_PARTICLES).astype(np.float32)
z = np.random.uniform(-0.1, 0.1, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global x, y, z
    py5.background(0, 0, 0, 15)  # Slight fade for trails

    py5.translate(py5.width / 2, py5.height / 2, -100)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.PI / 6)
    
    # Aizawa parameters
    dt = 0.015
    a = 0.95
    b = 0.7
    c = 0.6
    d = 3.5
    e = 0.25
    f = 0.1
    
    # Equations
    dx = (z - b) * x - d * y
    dy = d * x + (z - b) * y
    dz = c + a * z - (z**3 / 3) - (x**2 + y**2) * (1 + e * z) + f * z * x**3
    
    x += dx * dt
    y += dy * dt
    z += dz * dt
    
    py5.stroke_weight(2)
    
    # Render particles
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        # Color mapping based on Z position and distance
        hue = (180 + z[i] * 120 + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 100, 30)
        # Scale the attractor to fit the screen
        py5.vertex(x[i] * 150, y[i] * 150, z[i] * 150)
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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

py5.run_sketch()

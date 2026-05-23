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

NUM_PARTICLES = 50000

# Arrays for particles
x = np.random.uniform(-10, 10, NUM_PARTICLES).astype(np.float32)
y = np.random.uniform(-10, 10, NUM_PARTICLES).astype(np.float32)
z = np.random.uniform(-10, 10, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    global x, y, z
    py5.background(0, 0, 0, 15)  # Slight fade for trails

    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.frame_count * 0.005)
    
    # Lorenz parameters transitioning over time
    dt = 0.005
    sigma = 10.0
    rho = 28.0 + py5.sin(py5.frame_count * 0.01) * 10
    beta = 8.0 / 3.0
    
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    
    x += dx
    y += dy
    z += dz
    
    py5.stroke_weight(2)
    
    # Render particles
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        px = x[i] * 10
        py5.stroke(300 + py5.sin(py5.frame_count*0.02 + i*0.0001)*60, 90, 100, 20)
        py5.vertex(x[i] * 10, y[i] * 10, z[i] * 10)
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


py5.run_sketch()

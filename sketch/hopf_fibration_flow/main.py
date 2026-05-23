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

# Generate points on S2 and a random fiber parameter psi
theta = np.random.uniform(0, np.pi, NUM_PARTICLES).astype(np.float32)
phi = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES).astype(np.float32)
psi_base = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES).astype(np.float32)
hue_base = (theta / np.pi * 360).astype(np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0, 0, 0, 15)

    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.frame_count * 0.005)
    
    # Animate psi to flow along the fibers
    time_t = py5.frame_count * 0.02
    psi = psi_base + time_t
    
    eta = theta / 2.0
    x1 = np.sin(eta) * np.cos(psi)
    x2 = np.sin(eta) * np.sin(psi)
    x3 = np.cos(eta) * np.cos(phi + psi)
    x4 = np.cos(eta) * np.sin(phi + psi)
    
    # Stereographic projection from S3 to R3
    scale = 1.0 / (1.001 - x4)
    X = x1 * scale * 150
    Y = x2 * scale * 150
    Z = x3 * scale * 150
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        hue = (hue_base[i] + py5.frame_count * 0.5) % 360
        py5.stroke(hue, 90, 100, 40)
        py5.vertex(X[i], Y[i], Z[i])
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

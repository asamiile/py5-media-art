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

# Generate intersecting spirals
N = 25_000
theta = np.linspace(0, 300 * 2 * np.pi, N)
r = np.linspace(0.01, 0.99, N)

# Two spirals
Z1 = r * np.exp(1j * theta)
Z2 = r * np.exp(-1j * theta)

# Colors based on radius
colors1 = np.zeros((N, 3))
colors1[:, 0] = 320 # Magenta
colors1[:, 1] = 90
colors1[:, 2] = np.linspace(50, 100, N)

colors2 = np.zeros((N, 3))
colors2[:, 0] = 180 # Cyan
colors2[:, 1] = 90
colors2[:, 2] = np.linspace(50, 100, N)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 60, 10)  # Deep blue space

def draw():
    # Motion trails
    py5.fill(240, 60, 10, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES * np.pi * 2
    
    # Mobius transformation parameter 'a'
    # Use a smooth 2D Lissajous curve inside the unit disk
    a = 0.8 * np.sin(t) + 1j * 0.8 * np.sin(t * 2 + np.pi/4)
    
    # Global rotation
    rot = np.exp(1j * t * 1.5)
    
    # Transform
    def transform(Z):
        return rot * (Z - a) / (1 - np.conj(a) * Z)
        
    Z1_trans = transform(Z1)
    Z2_trans = transform(Z2)
    
    py5.translate(py5.width / 2, py5.height / 2)
    scale = min(py5.width, py5.height) * 0.45
    
    py5.stroke_weight(1.5)
    
    # Draw Z1
    py5.stroke(320, 90, 100, 80)
    py5.points(np.column_stack((np.real(Z1_trans), np.imag(Z1_trans))) * scale)
    
    # Draw Z2
    py5.stroke(180, 90, 100, 80)
    py5.points(np.column_stack((np.real(Z2_trans), np.imag(Z2_trans))) * scale)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 10 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
        import os
        os._exit(0)

py5.run_sketch()

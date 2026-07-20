from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    global grid_z
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create a dense grid of points in the complex plane
    # We map a larger grid into the unit disk
    x = np.linspace(-3, 3, 300)
    y = np.linspace(-3, 3, 300)
    X, Y = np.meshgrid(x, y)
    grid_z = X + 1j * Y

def draw():
    global grid_z
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    # Let alpha drift around inside the unit disk
    alpha_r = 0.85 * np.sin(t * 0.4)
    alpha_th = t * 0.9
    alpha = alpha_r * np.exp(1j * alpha_th)
    
    theta = t * 0.7
    rot = np.exp(1j * theta)
    
    # Apply mobius automorphism of unit disk
    # But wait, our grid is up to radius 3. 
    # An automorphism maps the unit disk to itself. If we apply it to a grid that goes outside,
    # the points outside will map outside (or through infinity).
    # That's fine, we will only draw points whose mapped absolute value is <= 1.0
    z_mapped = rot * (grid_z - alpha) / (1 - np.conj(alpha) * grid_z + 1e-8)
    
    radius = min(SIZE) * 0.48
    cx, cy = SIZE[0]/2, SIZE[1]/2
    
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    # Draw mapped horizontal lines
    for i in range(0, 300, 6):
        py5.stroke(0, 255, 255, 120) # Cyan
        py5.begin_shape()
        for j in range(300):
            z = z_mapped[i, j]
            if np.abs(z) <= 1.02: # Draw slightly outside to avoid gaps
                py5.vertex(cx + np.real(z) * radius, cy + np.imag(z) * radius)
            else:
                py5.end_shape()
                py5.begin_shape()
        py5.end_shape()

    # Draw mapped vertical lines
    for j in range(0, 300, 6):
        py5.stroke(255, 0, 255, 120) # Magenta
        py5.begin_shape()
        for i in range(300):
            z = z_mapped[i, j]
            if np.abs(z) <= 1.02:
                py5.vertex(cx + np.real(z) * radius, cy + np.imag(z) * radius)
            else:
                py5.end_shape()
                py5.begin_shape()
        py5.end_shape()
        
    # Draw boundary circle
    py5.stroke(255, 255, 255, 80)
    py5.ellipse(cx, cy, radius * 2, radius * 2)
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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
        import os
        os._exit(0)

py5.run_sketch()

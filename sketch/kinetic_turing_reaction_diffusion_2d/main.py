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

# Grid size for computation (downscaled for performance)
# To render at 4k, we'll map a smaller grid to rects or pixels
CELL_SIZE = 8
GRID_W = SIZE[0] // CELL_SIZE
GRID_H = SIZE[1] // CELL_SIZE

# Reaction-Diffusion constants (Gray-Scott model)
DA = 1.0     # Diffusion rate of A
DB = 0.5     # Diffusion rate of B
F = 0.055    # Feed rate
K = 0.062    # Kill rate
DT = 1.0     # Time step

# Initial states: A = 1.0, B = 0.0
A = np.ones((GRID_H, GRID_W), dtype=np.float32)
B = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Seed the grid with B in a few random spots
for _ in range(20):
    cy = random.randint(20, GRID_H - 20)
    cx = random.randint(20, GRID_W - 20)
    r = random.randint(5, 15)
    Y, X = np.ogrid[:GRID_H, :GRID_W]
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    B[dist < r] = 1.0

# Pre-calculate laplacian weights for 2D convolution
laplacian_kernel = np.array([[0.05, 0.2, 0.05],
                             [0.2, -1.0, 0.2],
                             [0.05, 0.2, 0.05]], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()

def draw():
    global A, B
    
    # We need to run multiple simulation steps per frame to make it visually interesting
    import scipy.signal
    
    for _ in range(8):
        # Laplacian
        lapA = scipy.signal.convolve2d(A, laplacian_kernel, mode='same', boundary='wrap')
        lapB = scipy.signal.convolve2d(B, laplacian_kernel, mode='same', boundary='wrap')
        
        # Gray-Scott equations
        ABB = A * B * B
        nextA = A + (DA * lapA - ABB + F * (1.0 - A)) * DT
        nextB = B + (DB * lapB + ABB - (K + F) * B) * DT
        
        A = np.clip(nextA, 0.0, 1.0)
        B = np.clip(nextB, 0.0, 1.0)
        
    # Render
    py5.background(240, 100, 20) # Deep blue base
    
    active_y, active_x = np.where(B > 0.1)
    
    for i in range(len(active_y)):
        y = active_y[i]
        x = active_x[i]
        valB = B[y, x]
        
        # Color mapping based on B concentration
        # High B -> toxic green (120)
        # Low B -> teal/blue (200)
        hue = 220 - (valB * 250)
        hue = np.clip(hue, 100, 240)
        
        py5.fill(hue, 100, 80 + valB * 50, 100)
        py5.rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

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

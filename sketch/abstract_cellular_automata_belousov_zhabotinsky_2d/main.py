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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation grid size (scaled up later)
GRID_W = 480
GRID_H = 270

# Parameters
alpha = 1.2
beta = 1.0
gamma = 1.0

# Initialize grids
A = np.random.rand(GRID_H, GRID_W)
B = np.random.rand(GRID_H, GRID_W)
C = np.random.rand(GRID_H, GRID_W)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global A, B, C
    
    # Simple 3-point neighborhood average to diffuse
    # We use numpy roll for fast shifting
    def diffuse(arr):
        return (arr + np.roll(arr, 1, axis=0) + np.roll(arr, -1, axis=0) + 
                np.roll(arr, 1, axis=1) + np.roll(arr, -1, axis=1) +
                np.roll(np.roll(arr, 1, axis=0), 1, axis=1) +
                np.roll(np.roll(arr, -1, axis=0), -1, axis=1) +
                np.roll(np.roll(arr, 1, axis=0), -1, axis=1) +
                np.roll(np.roll(arr, -1, axis=0), 1, axis=1)) / 9.0

    A_diff = diffuse(A)
    B_diff = diffuse(B)
    C_diff = diffuse(C)
    
    # BZ reaction rules
    next_A = np.clip(A_diff + A_diff * (alpha * B_diff - gamma * C_diff), 0, 1)
    next_B = np.clip(B_diff + B_diff * (beta * C_diff - alpha * A_diff), 0, 1)
    next_C = np.clip(C_diff + C_diff * (gamma * A_diff - beta * B_diff), 0, 1)
    
    A, B, C = next_A, next_B, next_C
    
    # Create image from arrays
    pixels = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    pixels[..., 0] = (A * 255).astype(np.uint8)
    pixels[..., 1] = (B * 255).astype(np.uint8)
    pixels[..., 2] = (C * 255).astype(np.uint8)
    
    img = py5.create_image_from_numpy(pixels, "RGB")
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

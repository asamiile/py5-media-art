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

# Reaction diffusion grid (scaled up to save compute)
GRID_W = 480
GRID_H = 270

# Gray-Scott parameters
dA = 1.0
dB = 0.5
feed = 0.055
k = 0.062

A = np.ones((GRID_H, GRID_W))
B = np.zeros((GRID_H, GRID_W))

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed the simulation with random blobs of B
    for _ in range(20):
        rx = np.random.randint(10, GRID_W - 10)
        ry = np.random.randint(10, GRID_H - 10)
        B[ry-5:ry+5, rx-5:rx+5] = 1.0

def diffuse(arr):
    # Using a 3x3 Laplacian convolution approximation
    laplace = (
        np.roll(arr, 1, axis=0) * 0.2 + 
        np.roll(arr, -1, axis=0) * 0.2 + 
        np.roll(arr, 1, axis=1) * 0.2 + 
        np.roll(arr, -1, axis=1) * 0.2 +
        np.roll(np.roll(arr, 1, axis=0), 1, axis=1) * 0.05 +
        np.roll(np.roll(arr, -1, axis=0), -1, axis=1) * 0.05 +
        np.roll(np.roll(arr, 1, axis=0), -1, axis=1) * 0.05 +
        np.roll(np.roll(arr, -1, axis=0), 1, axis=1) * 0.05 -
        arr * 1.0
    )
    return laplace

def draw():
    global A, B
    
    # Run multiple simulation steps per frame to speed it up
    for _ in range(8):
        lapA = diffuse(A)
        lapB = diffuse(B)
        
        abb = A * B * B
        
        next_A = A + (dA * lapA - abb + feed * (1 - A))
        next_B = B + (dB * lapB + abb - (k + feed) * B)
        
        A = np.clip(next_A, 0, 1)
        B = np.clip(next_B, 0, 1)
        
    # Map to colors
    diff = A - B
    pixels = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    
    # Map to a fiery/biological color palette
    hue = np.clip((1.0 - diff) * 60 + 20, 0, 360)
    sat = np.clip(diff * 100 + 50, 0, 100)
    bri = np.clip((1.0 - diff) * 100, 0, 100)
    
    # Since py5.create_image_from_numpy uses RGB, we must convert HSB to RGB manually or just use RGB math
    # We will compute pseudo-RGB for simplicity
    # A corresponds to empty space (blueish), B corresponds to cells (pinkish/white)
    
    pixels[..., 0] = (np.clip((1 - diff) * 255 + diff * 50, 0, 255)).astype(np.uint8) # R
    pixels[..., 1] = (np.clip((1 - diff) * 50 + diff * 150, 0, 255)).astype(np.uint8) # G
    pixels[..., 2] = (np.clip((1 - diff) * 100 + diff * 255, 0, 255)).astype(np.uint8) # B
    
    img = py5.create_image_from_numpy(pixels, "RGB")
    
    py5.background(0)
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

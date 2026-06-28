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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global y_indices, pixel_array
    y_indices = np.linspace(0, py5.TWO_PI * 4, py5.height)
    
    # Pre-allocate the entire image buffer: (height, width, 4) RGBA
    # uint8 array
    pixel_array = np.zeros((py5.height, py5.width, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255  # Full alpha

def draw():
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    global pixel_array
    
    # We will generate a new chunk of vertical data (e.g. 20 pixels wide)
    # and shift the entire image to the left by that amount.
    shift_amount = 20
    
    # Shift existing pixels to the left
    pixel_array[:, :-shift_amount] = pixel_array[:, shift_amount:]
    
    # Generate new column data using a mix of trigonometric interference for "noise"
    # To make it wide, we compute for an x grid
    x_indices = np.linspace(t * py5.TWO_PI * 50, (t + shift_amount/py5.width) * py5.TWO_PI * 50, shift_amount)
    
    # Create 2D grids for vectorization
    Y, X = np.meshgrid(y_indices, x_indices, indexing='ij')
    
    # Glitchy landscape formula
    val1 = np.sin(Y * 2.0 + X * 0.5)
    val2 = np.cos(Y * 4.0 - X * 1.5)
    val3 = np.sin(Y * 1.0 + X * 2.0 + t * py5.TWO_PI * 5)
    
    # Combine and add sharp thresholding for "glitch" blocks
    combined = val1 + val2 + val3
    
    # Base gradient (sky to ground)
    gradient = np.linspace(0, 1, py5.height)[:, None]
    
    # Colors
    r = np.where(combined > 1.0, 255, gradient * 100).astype(np.uint8)
    g = np.where(combined < -1.0, 255, gradient * 50).astype(np.uint8)
    b = np.where(np.abs(combined) < 0.2, 255, 50).astype(np.uint8)
    
    # Apply to the rightmost edge
    pixel_array[:, -shift_amount:, 0] = r
    pixel_array[:, -shift_amount:, 1] = g
    pixel_array[:, -shift_amount:, 2] = b
    
    # Add a scanline effect over the newly generated section
    pixel_array[::2, -shift_amount:, :3] = (pixel_array[::2, -shift_amount:, :3] * 0.5).astype(np.uint8)
    
    # Convert numpy array to Py5 image and display
    # create_image_from_numpy requires (height, width, 4) for RGBA
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    py5.image(img, 0, 0)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

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

# Internal resolution (half-res upscaled, runs 4x faster)
W_INT = SIZE[0] // 2
H_INT = SIZE[1] // 2

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global grid_x, grid_y, pixel_array
    
    # Precompute coordinate grids
    x = np.linspace(-3, 3, W_INT)
    y = np.linspace(-3, 3, H_INT)
    grid_x, grid_y = np.meshgrid(x, y)
    
    # Pre-allocate RGBA buffer
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255

def draw():
    global grid_x, grid_y, pixel_array
    
    t = (py5.frame_count / TOTAL_FRAMES) * py5.PI * 2
    
    # Domain warping using nested sine/cosine interference
    # Layer 1
    q_x = np.sin(grid_x * 2.0 + t) + np.cos(grid_y * 3.0 - t * 0.5)
    q_y = np.sin(grid_y * 1.5 - t) + np.cos(grid_x * 2.5 + t * 0.8)
    
    # Layer 2
    r_x = np.sin(grid_x * 1.0 + q_x * 2.0 + t * 1.2) + np.cos(grid_y * 1.5 + q_y * 1.5)
    r_y = np.sin(grid_y * 2.0 + q_y * 1.0 - t * 0.9) + np.cos(grid_x * 0.8 + q_x * 2.5)
    
    # Final value
    v = np.sin(grid_x * 0.5 + r_x * 2.0) + np.cos(grid_y * 0.5 + r_y * 2.0)
    
    # Normalize v from approx [-2, 2] to [0, 1]
    v_norm = (v + 2.0) / 4.0
    v_norm = np.clip(v_norm, 0, 1)
    
    # Create a marble/liquid color palette using cosine gradients
    # a + b * cos(2 * pi * (c * t + d))
    # We'll use a deep ocean / iridescent pearl palette
    r = (0.5 + 0.5 * np.cos(2 * py5.PI * (1.0 * v_norm + 0.00))) * 255
    g = (0.5 + 0.5 * np.cos(2 * py5.PI * (1.0 * v_norm + 0.33))) * 255
    b = (0.5 + 0.5 * np.cos(2 * py5.PI * (1.0 * v_norm + 0.67))) * 255
    
    # Optional: add "contour lines" or "isohypses" to make it look like a map
    # A sharp sine wave on the final value
    contours = np.abs(np.sin(v_norm * py5.PI * 20.0))
    # Mix contours in by darkening
    contour_mix = 0.5 + 0.5 * np.clip(contours * 2.0, 0, 1)
    
    pixel_array[:, :, 0] = (r * contour_mix).astype(np.uint8)
    pixel_array[:, :, 1] = (g * contour_mix).astype(np.uint8)
    pixel_array[:, :, 2] = (b * contour_mix).astype(np.uint8)
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Smooth upscale to 4K
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} (Time: {t:.2f})")

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

from pathlib import Path
import shutil
import subprocess
import sys
import random
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

NUM_CENTERS = 5
base_centers = np.random.rand(NUM_CENTERS, 2) * np.array([SIZE[0], SIZE[1]])
phases = np.random.rand(NUM_CENTERS) * np.pi * 2
speeds = np.random.uniform(0.01, 0.05, NUM_CENTERS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Pre-compute X and Y grids
    x_vals = np.arange(SIZE[0])
    y_vals = np.arange(SIZE[1])
    global xx, yy
    xx, yy = np.meshgrid(x_vals, y_vals, indexing='xy')

def draw():
    t = py5.frame_count * 0.05
    
    current_centers = base_centers + np.stack((
        np.sin(t * speeds + phases) * 400,
        np.cos(t * speeds + phases) * 400
    ), axis=-1)
    
    val = np.zeros((SIZE[1], SIZE[0]))
    for cx, cy in current_centers:
        dist = np.hypot(xx - cx, yy - cy)
        val += np.sin(dist * 0.02 - t * 2.0)
        
    val /= NUM_CENTERS
    # val is -1 to 1
    
    # Vectorized HSV to RGB conversion
    # Map val to hue (Cyan 180 to Magenta 320 -> approx 0.5 to 0.89 in 0-1)
    H = np.interp(val, [-1, 1], [180/360, 320/360])
    # Add golden yellow accent where abs(val) > 0.8
    accent_mask = np.abs(val) > 0.8
    H[accent_mask] = 50/360
    
    S = np.full_like(H, 0.9)
    V = np.interp(np.abs(val), [0, 1], [0.2, 1.0])
    
    # Convert HSV to RGB (simplified vectorization)
    i = (H * 6).astype(int)
    f = (H * 6) - i
    p = V * (1 - S)
    q = V * (1 - S * f)
    t_c = V * (1 - S * (1 - f))
    i = i % 6
    
    conditions = [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5]
    
    R = np.select(conditions, [V, q, p, p, t_c, V]) * 255
    G = np.select(conditions, [t_c, V, V, q, p, p]) * 255
    B = np.select(conditions, [p, p, t_c, V, V, q]) * 255
    
    pixels = np.empty((SIZE[1], SIZE[0], 4), dtype=np.uint8)
    # A (alpha) channel is ignored by py5's update_np_pixels without ARGB, 
    # but we will just write RGB channels
    # wait, py5.np_pixels is (height, width, 1) for grayscale or depends on color_mode?
    # No, we use py5.load_pixels and py5.pixels directly, or update_np_pixels requires specific shape.
    # update_np_pixels takes (height, width, 4) in ARGB format.
    pixels[:,:,0] = 255 # Alpha
    pixels[:,:,1] = R
    pixels[:,:,2] = G
    pixels[:,:,3] = B
    
    py5.load_np_pixels()
    py5.np_pixels[:] = pixels
    py5.update_np_pixels()

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
        
        import os
        os._exit(0)

py5.run_sketch()

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

# Internal resolution for fast Mandelbrot rendering
W_INT = SIZE[0] // 2
H_INT = SIZE[1] // 2

# Target coordinate to zoom into (Seahorse Valley deep spiral)
TARGET_R = -0.743643887037151
TARGET_I = 0.131825904205330

MAX_ITER = 300

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pixel_array
    
    # Pre-allocate RGBA buffer
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255
    
def get_mandelbrot(r_center, i_center, zoom):
    # Calculate bounds based on zoom
    width = 3.5 / zoom
    height = width * (H_INT / W_INT)
    
    r_min, r_max = r_center - width / 2, r_center + width / 2
    i_min, i_max = i_center - height / 2, i_center + height / 2
    
    # Create coordinate grid
    r, i = np.meshgrid(np.linspace(r_min, r_max, W_INT), np.linspace(i_min, i_max, H_INT))
    c = r + 1j * i
    z = np.zeros_like(c)
    
    # Track the escape time
    escape_time = np.zeros(z.shape, dtype=np.float32)
    # Boolean mask for points that haven't escaped
    not_escaped = np.ones(z.shape, dtype=bool)
    
    for iteration in range(MAX_ITER):
        # Update only points that haven't escaped yet
        z[not_escaped] = z[not_escaped]**2 + c[not_escaped]
        
        # Check which points escaped in this iteration
        escaped_now = np.abs(z) > 2.0
        # newly_escaped are those that escaped now AND were not already escaped
        newly_escaped = escaped_now & not_escaped
        
        # Record iteration for newly escaped
        escape_time[newly_escaped] = iteration
        
        # Update not_escaped mask
        not_escaped = not_escaped & ~escaped_now
        
        # Early exit if all points escaped
        if not np.any(not_escaped):
            break
            
    # Continuous smoothing for escaped points
    # escape_time = iteration + 1 - ln(ln(|Z|)) / ln(2)
    mask = ~not_escaped
    z_abs = np.abs(z[mask])
    # Avoid log(0) or log of negative
    z_abs[z_abs < 1] = 1
    
    # Add fractional part
    escape_time[mask] = escape_time[mask] + 1 - np.log(np.log(z_abs)) / np.log(2.0)
    
    # Set unescaped points to 0
    escape_time[not_escaped] = 0
    
    return escape_time

def draw():
    global pixel_array
    
    # Exponential zoom mapping over 450 frames
    # Starts at zoom = 1, ends at zoom = 10^11
    # We use a smooth ease-in-out curve for the zoom speed so it isn't jarring
    progress = py5.frame_count / TOTAL_FRAMES
    # Ease in-out cubic
    ease = progress * progress * (3.0 - 2.0 * progress)
    
    max_zoom_power = 11.0
    current_zoom = 10 ** (ease * max_zoom_power)
    
    # As we zoom in, we slowly pan towards the target to keep it centered
    # Pan from (0, 0) to TARGET
    pan_progress = 1.0 - (1.0 / current_zoom)
    curr_r = TARGET_R * pan_progress
    curr_i = TARGET_I * pan_progress
    
    escape_time = get_mandelbrot(curr_r, curr_i, current_zoom)
    
    # Map escape time to a stunning color palette
    # Use sine functions for periodic smooth color bands
    val = escape_time * 0.05
    val[escape_time == 0] = 0 # Center set is black
    
    # Glowing neon cyan / pink / deep blue
    r = (0.5 + 0.5 * np.cos(3.0 + val * 1.0)) * 255
    g = (0.5 + 0.5 * np.cos(3.0 + val * 1.5)) * 255
    b = (0.5 + 0.5 * np.cos(3.0 + val * 2.0)) * 255
    
    # Keep the Mandelbrot set itself black
    mask = (escape_time == 0)
    r[mask] = 0
    g[mask] = 0
    b[mask] = 0
    
    pixel_array[:, :, 0] = r.astype(np.uint8)
    pixel_array[:, :, 1] = g.astype(np.uint8)
    pixel_array[:, :, 2] = b.astype(np.uint8)
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Scale up to 4K
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} | Zoom: {current_zoom:.1e}x")

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

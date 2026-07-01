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

# Parameters
MAX_ITER = 60
ESCAPE_RADIUS = 10.0

# Pre-compute grid coordinates
# We'll render at full 4K
w, h = SIZE
y_idx, x_idx = np.mgrid[0:h, 0:w]

# Map pixels to complex plane [-1.5, 1.5]
# Adjust aspect ratio
aspect = w / h
x_map = (x_idx / w) * 3.0 * aspect - 1.5 * aspect
y_map = (y_idx / h) * 3.0 - 1.5

Z0 = x_map + 1j * y_map

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # We will use py5.set_np_pixels() to write directly to the canvas
    py5.load_np_pixels()

def draw():
    t = py5.frame_count * 0.015
    
    # The Julia set parameter c
    # We trace a circular path in the complex plane to smoothly morph the fractal
    # Radius ~0.7885 gives very intricate dragon-like shapes
    radius = 0.7885
    angle = t * 0.5
    
    # Add a little wobble to the radius to make it breathe
    r = radius + np.sin(t * 1.3) * 0.01
    c = r * np.cos(angle) + 1j * r * np.sin(angle)
    
    Z = Z0.copy()
    
    # To store the smooth iteration count
    smooth_iter = np.zeros(Z.shape, dtype=np.float32)
    
    # Active mask of points that haven't escaped yet
    active = np.ones(Z.shape, dtype=bool)
    
    for i in range(MAX_ITER):
        # Only update active points to save computation
        Z[active] = Z[active]**2 + c
        
        # Check escape condition
        escaped = np.abs(Z) > ESCAPE_RADIUS
        
        # New escaped points
        just_escaped = escaped & active
        
        # Calculate smooth coloring for newly escaped points
        # smooth_i = i + 1 - ln(ln(|z|)) / ln(2)
        if np.any(just_escaped):
            z_esc = Z[just_escaped]
            abs_z = np.abs(z_esc)
            # Avoid log of zero or negative (abs_z is > ESCAPE_RADIUS > 1)
            smooth_val = i + 1.0 - np.log2(np.log(abs_z))
            smooth_iter[just_escaped] = smooth_val
            
        active[just_escaped] = False
        
        # Early exit if all points escaped
        if not np.any(active):
            break

    # For points that never escaped (inside the set), set a distinct value
    smooth_iter[active] = MAX_ITER
    
    # Map smooth_iter to colors
    # We'll create a nice palette
    # Map to [0, 1]
    norm_iter = np.clip(smooth_iter / MAX_ITER, 0.0, 1.0)
    
    # We construct RGB channels using sine waves for a continuous gradient
    # Sine frequency and phase determine the color banding
    freq = 15.0
    
    # Deep blue/purple to glowing neon cyan/magenta
    R = (0.5 + 0.5 * np.cos(freq * norm_iter + 0.0)) * 255.0
    G = (0.5 + 0.5 * np.cos(freq * norm_iter + 2.0)) * 255.0
    B = (0.5 + 0.5 * np.cos(freq * norm_iter + 4.0)) * 255.0
    
    # Points inside the set are black
    R[active] = 0
    G[active] = 0
    B[active] = 0
    
    # Construct ARGB pixels for py5
    A = np.full(Z.shape, 255, dtype=np.uint8)
    
    pixels = np.dstack((A, R.astype(np.uint8), G.astype(np.uint8), B.astype(np.uint8)))
    
    # Write to canvas
    py5.np_pixels[:] = pixels.reshape((h, w, 4))
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
        import os
        os._exit(0)

py5.run_sketch()

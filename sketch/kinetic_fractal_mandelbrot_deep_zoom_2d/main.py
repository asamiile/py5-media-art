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
    global X_base, Y_base, scale, cols, rows, max_iter
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    scale = 4
    cols = SIZE[0] // scale
    rows = SIZE[1] // scale
    
    x = np.linspace(-1, 1, cols)
    y = np.linspace(-1, 1, rows)
    X, Y = np.meshgrid(x, y)
    X_base = X * (cols / rows)
    Y_base = Y
    
    max_iter = 120

def draw():
    t = py5.frame_count / FPS
    
    # Zoom exponentially
    zoom = 2.0 ** (t * 0.9)
    
    # Interesting coordinate to zoom into
    cx = -0.7436438870371587
    cy = 0.1318259042053119
    
    # Apply zoom and center
    C = (X_base / zoom + cx) + 1j * (Y_base / zoom + cy)
    Z = np.zeros_like(C)
    
    iters = np.zeros(C.shape, dtype=int)
    m = np.full(C.shape, True, dtype=bool)
    
    for i in range(max_iter):
        Z[m] = Z[m]**2 + C[m]
        # To avoid overflow warnings, only check active points
        abs_Z = np.zeros_like(Z, dtype=float)
        abs_Z[m] = np.abs(Z[m])
        escaped = (abs_Z > 2.0) & m
        m[escaped] = False
        iters[escaped] = i
        
    py5.load_np_pixels()
    
    color_mapped = np.zeros((rows, cols, 3), dtype=np.uint8)
    
    # Map iterations to colors
    # Cycle the colors based on time and iterations
    color_phase = (iters / 40.0) - (t * 0.5)
    
    color_mapped[:,:,0] = ((np.sin(color_phase * np.pi * 2) * 0.5 + 0.5) * 255).astype(np.uint8) # R
    color_mapped[:,:,1] = ((np.sin(color_phase * np.pi * 2 + 1.0) * 0.5 + 0.5) * 150).astype(np.uint8) # G
    color_mapped[:,:,2] = ((np.sin(color_phase * np.pi * 2 + 2.0) * 0.5 + 0.5) * 80).astype(np.uint8) # B
    
    # Inside the set (m is true) is black
    color_mapped[m] = 0
    
    # Scale up
    r_scaled = np.repeat(np.repeat(color_mapped[:,:,0], scale, axis=0), scale, axis=1)
    g_scaled = np.repeat(np.repeat(color_mapped[:,:,1], scale, axis=0), scale, axis=1)
    b_scaled = np.repeat(np.repeat(color_mapped[:,:,2], scale, axis=0), scale, axis=1)
    
    r_scaled = r_scaled[:SIZE[1], :SIZE[0]]
    g_scaled = g_scaled[:SIZE[1], :SIZE[0]]
    b_scaled = b_scaled[:SIZE[1], :SIZE[0]]
    
    py5.np_pixels[:, :, 1] = r_scaled
    py5.np_pixels[:, :, 2] = g_scaled
    py5.np_pixels[:, :, 3] = b_scaled
    py5.np_pixels[:, :, 0] = 255
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
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

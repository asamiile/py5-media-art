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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global X, Y
    x = np.linspace(-1, 1, SIZE[0])
    y = np.linspace(-1, 1, SIZE[1])
    X, Y = np.meshgrid(x, y)
    
    global R, Theta
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # Generate an interference pattern
    z1 = np.sin(R * 40 - t * py5.TWO_PI * 4)
    z2 = np.sin((X + 0.5) * 30 + t * py5.TWO_PI * 2) * np.cos((Y - 0.5) * 30)
    
    # Math based topography
    Z = z1 + z2 + np.sin(Theta * 6 + t * py5.TWO_PI) * 0.5
    
    # Extract contour lines
    Z_scaled = Z * 10
    Z_fractional = Z_scaled - np.floor(Z_scaled)
    
    line_mask = (Z_fractional < 0.15) | (Z_fractional > 0.85)
    
    py5.load_np_pixels()
    
    normalized_Z = (Z + 2.5) / 5.0
    
    # Start with a very dark background
    r = np.full_like(Z, 5, dtype=np.float32)
    g = np.full_like(Z, 5, dtype=np.float32)
    b = np.full_like(Z, 15, dtype=np.float32)
    
    # Apply glowing holographic colors to lines
    r[line_mask] = np.clip(normalized_Z[line_mask] * 255, 0, 255)
    g[line_mask] = np.clip((1 - normalized_Z[line_mask]) * 255, 0, 255)
    b[line_mask] = 255
    
    # Vignette
    vignette = np.clip(1.2 - R, 0, 1) ** 2
    r = (r * vignette).astype(np.uint32)
    g = (g * vignette).astype(np.uint32)
    b = (b * vignette).astype(np.uint32)
    
    a = np.full_like(r, 255, dtype=np.uint32)
    py5.np_pixels[:, :, 0] = a.reshape((SIZE[1], SIZE[0]))
    py5.np_pixels[:, :, 1] = r.reshape((SIZE[1], SIZE[0]))
    py5.np_pixels[:, :, 2] = g.reshape((SIZE[1], SIZE[0]))
    py5.np_pixels[:, :, 3] = b.reshape((SIZE[1], SIZE[0]))
    py5.update_np_pixels()

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

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

# Kuramoto simulation state
GRID_SCALE = 4
grid_w = SIZE[0] // GRID_SCALE
grid_h = SIZE[1] // GRID_SCALE

theta = np.random.uniform(0, 2*np.pi, (grid_h, grid_w))
omega = np.random.normal(0.08, 0.02, (grid_h, grid_w))
K = 0.8  # Coupling constant

def kuramoto_step():
    global theta, omega
    # Compute neighborhood order parameter using complex numbers
    Z = np.exp(1j * theta)
    
    # 3x3 convolution using shifts (very fast)
    C = np.zeros_like(Z)
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            C += np.roll(Z, shift=(dy, dx), axis=(0, 1))
            
    # The interaction term is Im(C * exp(-i*theta))
    interaction = np.imag(C * np.exp(-1j * theta))
    
    # Update phases
    theta += omega + K * interaction
    theta = np.mod(theta, 2*np.pi)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    kuramoto_step()
    
    py5.load_np_pixels()
    
    # Upscale theta to pixel size using Kronecker product or repeat
    theta_large = np.repeat(np.repeat(theta, GRID_SCALE, axis=0), GRID_SCALE, axis=1)
    
    # Map theta [0, 2pi] to colors
    # Hue: Lime green (0.3) to Cyan (0.5)
    hue = 0.3 + 0.2 * (theta_large / (2*np.pi))
    # Brightness: pulses when phase is near 0
    brightness = 0.2 + 0.8 * (np.cos(theta_large) * 0.5 + 0.5)**4
    
    # Fast HSB to RGB
    h = hue * 6.0
    i = np.floor(h)
    f = h - i
    v = brightness
    q = v * (1.0 - f)
    t = v * f
    
    i = (i % 6).astype(int)
    
    r = np.choose(i, [v, q, np.zeros_like(v), np.zeros_like(v), t, v]) * 255
    g = np.choose(i, [t, v, v, q, np.zeros_like(v), np.zeros_like(v)]) * 255
    b = np.choose(i, [np.zeros_like(v), np.zeros_like(v), t, v, v, q]) * 255
    
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b.astype(np.uint8)
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

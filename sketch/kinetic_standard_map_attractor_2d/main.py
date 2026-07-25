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

# Simulation state
N = 1000000
# Initial points (Standard map is naturally on a torus [0, 2pi] x [0, 2pi])
# but often viewed from [-pi, pi]
x = np.random.uniform(-np.pi, np.pi, N).astype(np.float32)
y = np.random.uniform(-np.pi, np.pi, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_standard(K):
    global x, y
    y_new = y + K * np.sin(x)
    x_new = x + y_new
    
    # Wrap to [-pi, pi]
    x_new = (x_new + np.pi) % (2 * np.pi) - np.pi
    y_new = (y_new + np.pi) % (2 * np.pi) - np.pi
    
    x[:] = x_new
    y[:] = y_new

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Modulate chaos parameter K
    # K=0.9716 is the critical threshold where global chaos emerges
    # We modulate K between 0.5 (mostly structured) and 2.5 (mostly chaotic)
    K = 1.5 + 1.0 * np.sin(t)
    
    # Run steps
    for _ in range(5):
        step_standard(K)
        
    # Map to screen (Bounds: [-pi, pi])
    screen_x = (x + np.pi) / (2 * np.pi) * SIZE[0]
    screen_y = (y + np.pi) / (2 * np.pi) * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Deep Ocean Blue, Aqua, and Seafoam Green
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    r = 20 + 20 * (density_norm ** 2)
    g = 50 + 205 * (density_norm ** 1.5)
    b = 100 + 155 * (density_norm ** 0.8)
    
    # Intense seafoam highlights
    highlight = density_norm > 0.7
    r[highlight] = 150 + 105 * ((density_norm[highlight] - 0.7) / 0.3)
    g[highlight] = 255
    b[highlight] = 200 + 55 * ((density_norm[highlight] - 0.7) / 0.3)
    
    py5.np_pixels[:, :, 0] = 255
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

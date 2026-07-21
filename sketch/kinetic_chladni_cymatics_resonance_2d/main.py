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

# High particle count to simulate dense sand
NUM_PARTICLES = 100_000
pts_x = np.random.uniform(0, SIZE[0], NUM_PARTICLES).astype(np.float32)
pts_y = np.random.uniform(0, SIZE[1], NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 10, 15)

def chladni(x, y, n, m):
    nx = x * np.pi * n
    my = y * np.pi * m
    mx = x * np.pi * m
    ny = y * np.pi * n
    return np.sin(nx) * np.sin(my) - np.cos(mx) * np.cos(ny)

def get_chladni_gradient(x, y, t):
    # Map pixel coordinates to -1 to 1 plate scale
    cx = (x / SIZE[0]) * 2 - 1
    cy = (y / SIZE[1]) * 2 - 1
    
    # Dynamically shifting resonant frequencies
    n = 4.0 + np.sin(t * 0.4) * 2.0
    m = 6.0 + np.cos(t * 0.5) * 3.0
    
    eps = 0.005
    
    # Calculate finite difference gradient
    c = chladni(cx, cy, n, m)
    c_dx = chladni(cx + eps, cy, n, m) - chladni(cx - eps, cy, n, m)
    c_dy = chladni(cx, cy + eps, n, m) - chladni(cx, cy - eps, n, m)
    
    # The gradient of the squared function pushes particles towards the zeros (nodes)
    grad_x = 2 * c * c_dx
    grad_y = 2 * c * c_dy
    
    return grad_x, grad_y

def draw():
    global pts_x, pts_y
    
    # Faint clear to leave slight trails as the resonant patterns shift
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Calculate forces pushing particles into cymatic nodes
    grad_x, grad_y = get_chladni_gradient(pts_x, pts_y, t)
    
    # Particles move opposite to the gradient to settle in the valleys (nodes)
    pts_x -= grad_x * 8.0
    pts_y -= grad_y * 8.0
    
    # Add random Brownian motion so they don't get stuck permanently
    # and re-settle when the frequency changes
    pts_x += np.random.normal(0, 1.5, NUM_PARTICLES)
    pts_y += np.random.normal(0, 1.5, NUM_PARTICLES)
    
    # Keep particles on the plate
    pts_x = np.clip(pts_x, 0, SIZE[0])
    pts_y = np.clip(pts_y, 0, SIZE[1])
    
    # Draw the sand particles (gold/bronze color)
    py5.stroke(255, 200, 100, 40)
    py5.stroke_weight(2)
    
    coords = np.column_stack((pts_x, pts_y))
    py5.points(coords)

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

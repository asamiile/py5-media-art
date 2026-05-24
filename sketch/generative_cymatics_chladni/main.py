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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 30000

# We use numpy for fast vectorized calculations
px = np.random.uniform(-1, 1, NUM_PARTICLES)
py_pos = np.random.uniform(-1, 1, NUM_PARTICLES)
vx = np.zeros(NUM_PARTICLES)
vy = np.zeros(NUM_PARTICLES)

def chladni_grad(x, y, n, m, a, b):
    # Calculate the gradient of the Chladni plate equation squared (we want to minimize amplitude squared)
    # F(x,y) = a * sin(n pi x) sin(m pi y) + b * sin(m pi x) sin(n pi y)
    
    npx = n * np.pi * x
    mpy = m * np.pi * y
    mpx = m * np.pi * x
    npy = n * np.pi * y
    
    F = a * np.sin(npx) * np.sin(mpy) + b * np.sin(mpx) * np.sin(npy)
    
    # Partial derivative with respect to x
    dF_dx = a * n * np.pi * np.cos(npx) * np.sin(mpy) + b * m * np.pi * np.cos(mpx) * np.sin(npy)
    
    # Partial derivative with respect to y
    dF_dy = a * m * np.pi * np.sin(npx) * np.cos(mpy) + b * n * np.pi * np.sin(mpx) * np.cos(npy)
    
    # Gradient of F^2 is 2 * F * dF
    grad_x = 2 * F * dF_dx
    grad_y = 2 * F * dF_dy
    
    return grad_x, grad_y

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10)
    
def draw():
    global px, py_pos, vx, vy
    
    # Motion blur / particle trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Slowly morph the resonant frequencies
    # We smoothly transition between different harmonic states
    n = py5.remap(py5.sin(t * 0.5), -1, 1, 2.0, 6.0)
    m = py5.remap(py5.cos(t * 0.3), -1, 1, 2.0, 6.0)
    a, b = 1.0, 1.0
    
    # Multiple simulation steps per frame for fast settling
    for _ in range(3):
        gx, gy = chladni_grad(px, py_pos, n, m, a, b)
        
        # Particles move down the gradient towards zero amplitude (nodes)
        # Adding some Brownian noise so they don't get stuck in local minima perfectly
        vx = vx * 0.8 - gx * 0.002 + np.random.normal(0, 0.005, NUM_PARTICLES)
        vy = vy * 0.8 - gy * 0.002 + np.random.normal(0, 0.005, NUM_PARTICLES)
        
        px += vx
        py_pos += vy
        
        # Wrap particles that fall off the plate
        out_of_bounds = (np.abs(px) > 1) | (np.abs(py_pos) > 1)
        if np.any(out_of_bounds):
            px[out_of_bounds] = np.random.uniform(-1, 1, np.sum(out_of_bounds))
            py_pos[out_of_bounds] = np.random.uniform(-1, 1, np.sum(out_of_bounds))
            vx[out_of_bounds] = 0
            vy[out_of_bounds] = 0

    py5.translate(py5.width / 2, py5.height / 2)
    
    # Slow rotation
    py5.rotate_z(t * 0.2)
    
    # Draw particles
    py5.stroke_weight(2)
    
    scale_factor = min(py5.width, py5.height) * 0.45
    
    # Since iterating 30,000 points in Python is slow, we use points() with numpy arrays
    # But py5 points() takes 2D array of coordinates
    coords = np.column_stack((px * scale_factor, py_pos * scale_factor))
    
    hue = (t * 50) % 360
    py5.stroke(hue, 90, 100, 30)
    py5.points(coords)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

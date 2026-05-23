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

# Render at half resolution for performance, upscale later
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

# Physics parameters
G = 0.5        # Gravity
C = 0.1        # Friction/Damping
H = 0.25       # Height of pendulum above magnets
DT = 0.05      # Timestep

# Magnets layout (equilateral triangle)
magnets = np.array([
    [0, 1],
    [np.cos(7*np.pi/6), np.sin(7*np.pi/6)],
    [np.cos(11*np.pi/6), np.sin(11*np.pi/6)]
], dtype=np.float32)

# Initial coordinate space
x_range = np.linspace(-2.0, 2.0, SIM_W, dtype=np.float32)
y_range = np.linspace(-2.0, 2.0, SIM_H, dtype=np.float32)
xv, yv = np.meshgrid(x_range, y_range)

# Particles state
px = xv.copy()
py_ = yv.copy()
vx = np.zeros_like(px)
vy = np.zeros_like(py_)

# Output colors
out_r = np.zeros((SIM_H, SIM_W), dtype=np.float32)
out_g = np.zeros((SIM_H, SIM_W), dtype=np.float32)
out_b = np.zeros((SIM_H, SIM_W), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    global px, py_, vx, vy, out_r, out_g, out_b
    
    # Run a few physics steps per frame
    for _ in range(5):
        ax = -G * px - C * vx
        ay = -G * py_ - C * vy
        
        # Magnetic forces
        for i in range(3):
            dx = magnets[i, 0] - px
            dy = magnets[i, 1] - py_
            dist_sq = dx**2 + dy**2 + H**2
            dist_52 = dist_sq ** 2.5  # approximation of force ~ r/|r|^3
            
            # small epsilon to avoid divide by zero just in case
            ax += dx / (dist_52 + 1e-6)
            ay += dy / (dist_52 + 1e-6)
            
        vx += ax * DT
        vy += ay * DT
        px += vx * DT
        py_ += vy * DT

    # Map proximity to magnets to RGB channels
    # Red -> Magnet 0
    # Green -> Magnet 1
    # Blue -> Magnet 2
    
    # Calculate distance to each magnet
    d0 = (px - magnets[0, 0])**2 + (py_ - magnets[0, 1])**2
    d1 = (px - magnets[1, 0])**2 + (py_ - magnets[1, 1])**2
    d2 = (px - magnets[2, 0])**2 + (py_ - magnets[2, 1])**2
    
    # Smooth coloring based on closeness
    w0 = 1.0 / (d0 + 0.05)
    w1 = 1.0 / (d1 + 0.05)
    w2 = 1.0 / (d2 + 0.05)
    w_sum = w0 + w1 + w2
    
    r_target = w0 / w_sum * 255.0
    g_target = w1 / w_sum * 255.0
    b_target = w2 / w_sum * 255.0
    
    # Smoothly blend the colors over time (motion blur / trail effect)
    out_r = out_r * 0.9 + r_target * 0.1
    out_g = out_g * 0.9 + g_target * 0.1
    out_b = out_b * 0.9 + b_target * 0.1
    
    # Upscale 2x
    r_up = np.kron(out_r.astype(np.uint8), np.ones((2, 2), dtype=np.uint8))
    g_up = np.kron(out_g.astype(np.uint8), np.ones((2, 2), dtype=np.uint8))
    b_up = np.kron(out_b.astype(np.uint8), np.ones((2, 2), dtype=np.uint8))
    
    r_up = r_up[:SIZE[1], :SIZE[0]]
    g_up = g_up[:SIZE[1], :SIZE[0]]
    b_up = b_up[:SIZE[1], :SIZE[0]]
    
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    pixels[:, :, 0] = 255
    pixels[:, :, 1] = r_up
    pixels[:, :, 2] = g_up
    pixels[:, :, 3] = b_up
    
    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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

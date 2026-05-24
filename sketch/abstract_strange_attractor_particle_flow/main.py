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

NUM_PARTICLES = 50000
# Initial positions slightly randomized around a point
pos = np.random.randn(NUM_PARTICLES, 3) * 0.1
pos[:, 0] += 0.1
pos[:, 1] += 0.1
pos[:, 2] += 0.1

# Lorenz attractor parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0
dt = 0.005

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global pos
    
    # Motion blur / glowing trails effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Calculate Lorenz Attractor vector field step using NumPy for performance
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]
    
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    
    # Add some organic noise/wind to the chaotic system
    # We do a slight drift so the attractor evolves
    dx += np.sin(y * 0.1 + t) * 0.05
    dy += np.cos(x * 0.1 + t) * 0.05
    
    pos[:, 0] += dx
    pos[:, 1] += dy
    pos[:, 2] += dz
    
    # Camera and view
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.2) * 0.3)
    
    # Scale up the Lorenz coordinates (usually range -20 to 20) to screen space
    scale_factor = 15.0
    
    py5.stroke_weight(1.5)
    
    # Render particles as points
    # We will use points instead of individual shapes for performance with 50,000 particles
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        px = pos[i, 0] * scale_factor
        py = pos[i, 1] * scale_factor
        pz = (pos[i, 2] - 25.0) * scale_factor # offset Z to center
        
        # Color based on speed and Z-depth
        speed = abs(dx[i]) + abs(dy[i]) + abs(dz[i])
        hue = (py5.remap(speed, 0, 0.5, 180, 360) + t * 20) % 360
        brightness = py5.remap(pz, -400, 400, 30, 100)
        
        py5.stroke(hue, 80, brightness, 20)
        py5.vertex(px, py, pz)
    py5.end_shape()

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

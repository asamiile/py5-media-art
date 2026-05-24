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
dt = 0.005

# Lorenz attractor parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0

# Arrays for particles
# x, y, z
pos = np.random.uniform(-10, 10, (NUM_PARTICLES, 3)).astype(np.float32)
colors = np.zeros((NUM_PARTICLES,), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Additive blending motion blur trick
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global pos, colors
    
    # Calculate Lorenz vector field
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    
    # Update positions
    pos[:, 0] += dx
    pos[:, 1] += dy
    pos[:, 2] += dz
    
    # Update colors based on speed
    speed = np.sqrt(dx**2 + dy**2 + dz**2)
    colors = (colors + speed * 1000 + py5.frame_count) % 360
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slowly rotate camera
    t = py5.frame_count * 0.01
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.2) * 0.5)
    
    # The Lorenz attractor is small, scale it up to fit the screen
    # Also offset Z to center the two "butterfly wings"
    py5.scale(15)
    py5.translate(0, 0, -25)
    
    # Draw points
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.stroke(colors[i], 90, 100, 40)
        py5.vertex(pos[i, 0], pos[i, 1], pos[i, 2])
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

from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 30000
px = None
py = None
vx = None
vy = None

def setup():
    global px, py, vx, vy
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    px = np.random.uniform(0, py5.width, num_particles)
    py = np.random.uniform(0, py5.height, num_particles)
    vx = np.zeros(num_particles)
    vy = np.zeros(num_particles)

def chladni(x, y, n, m):
    # Map pixel coords to -1..1
    nx = py5.remap(x, 0, py5.width, -1, 1)
    ny = py5.remap(y, 0, py5.height, -1, 1)
    
    val = np.sin(n * py5.PI * nx) * np.sin(m * py5.PI * ny) + \
          np.sin(m * py5.PI * nx) * np.sin(n * py5.PI * ny)
    return np.abs(val)

def draw():
    global px, py, vx, vy
    
    # Fade trail
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.01
    
    # Animate resonance frequencies
    n = py5.remap(np.sin(time * 0.5), -1, 1, 2, 7)
    m = py5.remap(np.cos(time * 0.3), -1, 1, 3, 8)
    
    # Calculate gradient via finite difference
    eps = 1.0
    val_center = chladni(px, py, n, m)
    val_right = chladni(px + eps, py, n, m)
    val_top = chladni(px, py + eps, n, m)
    
    grad_x = (val_right - val_center) / eps
    grad_y = (val_top - val_center) / eps
    
    # Particles move towards 0 (so down the gradient)
    force_x = -grad_x * 50.0
    force_y = -grad_y * 50.0
    
    # Add some random noise to break them out of local minima
    noise_force_x = np.random.uniform(-0.5, 0.5, num_particles)
    noise_force_y = np.random.uniform(-0.5, 0.5, num_particles)
    
    vx = vx * 0.8 + force_x + noise_force_x
    vy = vy * 0.8 + force_y + noise_force_y
    
    px += vx
    py += vy
    
    # Wrap around
    px = np.mod(px, py5.width)
    py = np.mod(py, py5.height)
    
    # Draw
    py5.stroke(40, 80, 50, 40) # Amber/Gold
    py5.stroke_weight(2)
    py5.points(np.column_stack((px, py)))

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn

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

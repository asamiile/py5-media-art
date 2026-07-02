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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle parameters
NUM_PARTICLES = 50000
positions = None
velocities = None
colors = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    global positions, velocities, colors
    # Initialize positions randomly across the screen
    positions = np.random.rand(NUM_PARTICLES, 2)
    positions[:, 0] *= py5.width
    positions[:, 1] *= py5.height
    
    velocities = np.zeros((NUM_PARTICLES, 2))
    colors = np.zeros((NUM_PARTICLES, 4))
    
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global positions, velocities, colors
    
    # Motion blur: semi-transparent black background
    # Since we are in HSB, black is 0, 0, 0, alpha
    py5.no_stroke()
    py5.fill(0, 0, 0, 15) 
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.005
    
    # Update velocities based on noise field
    # We use a vectorized approach, but since py5.os_noise isn't vectorized out of the box in python,
    # we'll use a fast sine approximation or a grid-based lookup to keep it 60fps, 
    # OR we can just use numpy math to create a pseudo-noise vector field for extreme speed.
    
    # Fast pseudo-noise vector field using numpy broadcasting
    # Angle = sin(x*a + t) + cos(y*b + t) + sin((x+y)*c - t)
    x = positions[:, 0] * 0.002
    y = positions[:, 1] * 0.002
    
    angles = (np.sin(x * 2.0 + t) * 2.0 + 
              np.cos(y * 2.5 + t * 1.2) * 2.0 + 
              np.sin((x + y) * 1.5 - t * 0.8) * 3.0)
    
    velocities[:, 0] = np.cos(angles) * 4.0
    velocities[:, 1] = np.sin(angles) * 4.0
    
    # Update positions
    positions += velocities
    
    # Wrap around screen
    positions[:, 0] = np.mod(positions[:, 0], py5.width)
    positions[:, 1] = np.mod(positions[:, 1], py5.height)
    
    # Map angles to colors (Holographic Blue/Purple/Pink)
    # Hue range: roughly 260 (purple) to 340 (pink) to 200 (blue)
    normalized_angles = (angles + 7.0) / 14.0 # Roughly 0 to 1
    hues = 200 + (normalized_angles * 160)
    hues = np.mod(hues, 360)
    
    # Draw particles
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.stroke(hues[i], 80, 100, 150)
        py5.vertex(positions[i, 0], positions[i, 1])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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

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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(5, 5, 10)
    
    global particles, num_particles
    num_particles = 200
    particles = np.zeros((num_particles, 4)) # x, y, hue, length
    for i in range(num_particles):
        particles[i, 0] = py5.random(py5.width)
        particles[i, 1] = py5.random(py5.height)
        particles[i, 2] = py5.random(160, 320) # Blue to pink
        particles[i, 3] = py5.random(10, 50)

def draw():
    # Subtle motion blur
    py5.no_stroke()
    py5.fill(5, 5, 10, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    time_t = py5.frame_count * 0.005
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    for i in range(num_particles):
        x, y, hue, length = particles[i]
        
        # Calculate flow field direction
        angle = py5.os_noise(x * 0.002, y * 0.002, time_t) * py5.TWO_PI * 2
        
        nx = x + py5.cos(angle) * 5
        ny = y + py5.sin(angle) * 5
        
        # Draw fiber
        alpha = py5.noise(i, time_t * 5) * 100
        
        # Additive blending effect by drawing multiple times with low opacity
        py5.stroke(hue % 360, 90, 100, alpha)
        py5.line(x, y, nx, ny)
        
        # Bright head pulse
        if py5.random(1) < 0.05:
            py5.stroke((hue + 50) % 360, 50, 100, 100)
            py5.point(nx, ny)
            
        particles[i, 0] = nx
        particles[i, 1] = ny
        
        if nx < 0 or nx > py5.width or ny < 0 or ny > py5.height:
            particles[i, 0] = py5.random(py5.width)
            particles[i, 1] = py5.random(py5.height)

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

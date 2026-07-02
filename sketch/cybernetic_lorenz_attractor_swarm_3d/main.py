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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lorenz parameters
a = 10.0
b = 28.0
c = 8.0 / 3.0
dt = 0.01

particles = []
history_length = 50

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize particles with slight offsets
    for i in range(150):
        x = 0.1 + py5.random(-0.1, 0.1)
        y = 0.0 + py5.random(-0.1, 0.1)
        z = 0.0 + py5.random(-0.1, 0.1)
        hue = random.choice([190, 320]) # Neon blue or Hot pink
        particles.append({'pos': [x,y,z], 'history': [], 'hue': hue})

def draw():
    py5.background(10, 20, 5) # Deep cybernetic space
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.01
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -300)
    py5.rotate_y(time * 0.5)
    py5.rotate_x(py5.PI / 8)
    
    py5.scale(15) # Scale up the Lorenz attractor which normally fits in a small box
    py5.translate(0, 0, -20) # Center the attractor
    
    py5.no_fill()
    py5.stroke_weight(0.5)
    
    for p in particles:
        x, y, z = p['pos']
        
        dx = (a * (y - x)) * dt
        dy = (x * (b - z) - y) * dt
        dz = (x * y - c * z) * dt
        
        x += dx
        y += dy
        z += dz
        
        p['pos'] = [x, y, z]
        p['history'].append([x, y, z])
        
        if len(p['history']) > history_length:
            p['history'].pop(0)
            
        py5.begin_shape()
        for i, pos in enumerate(p['history']):
            # fade out trail
            alpha = py5.remap(i, 0, len(p['history']), 0, 100)
            py5.stroke(p['hue'], 80, 100, alpha)
            py5.vertex(pos[0], pos[1], pos[2])
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

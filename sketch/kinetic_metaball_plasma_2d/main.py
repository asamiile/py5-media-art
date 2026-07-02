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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 255)
    py5.background(0)
    
    global balls
    num_balls = 40
    balls = []
    for _ in range(num_balls):
        r = random.uniform(200, 800)
        x = random.uniform(r, py5.width - r)
        y = random.uniform(r, py5.height - r)
        vx = random.uniform(-8, 8)
        vy = random.uniform(-8, 8)
        hue = random.uniform(0, 255)
        balls.append([x, y, vx, vy, r, hue])

def draw():
    global balls
    
    # Very slight fade for trails
    py5.fill(0, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    for b in balls:
        # Update physics
        b[0] += b[2]
        b[1] += b[3]
        
        # Bounce
        if b[0] < -b[4]/2 or b[0] > py5.width + b[4]/2: b[2] *= -1
        if b[1] < -b[4]/2 or b[1] > py5.height + b[4]/2: b[3] *= -1
        
        # Color shifting
        b[5] = (b[5] + 1) % 255
        
        # Draw soft glowing plasma orb
        py5.fill(b[5], 200, 255, 10)
        # Using multiple concentric circles to simulate a soft radial gradient
        steps = 10
        for i in range(steps):
            radius = b[4] * (1.0 - i/steps)
            py5.circle(b[0], b[1], radius * 2)
            
    py5.blend_mode(py5.BLEND)
    
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

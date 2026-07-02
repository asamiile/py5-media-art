from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 40000

class Particle:
    def __init__(self):
        self.x = random.uniform(0, py5.width)
        self.y = random.uniform(0, py5.height)
        self.vx = 0
        self.vy = 0

particles = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(10, 10, 15)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Subtle fade for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_t = py5.frame_count * 0.005
    
    noise_scale = 0.002
    
    py5.stroke_weight(1.5)
    
    py5.begin_shape(py5.LINES)
    
    for p in particles:
        # Perlin noise vector field
        angle = py5.noise(p.x * noise_scale, p.y * noise_scale, time_t) * py5.TWO_PI * 4.0
        
        # Flow force
        p.vx = np.cos(angle) * 2.0
        p.vy = np.sin(angle) * 2.0
        
        # Color based on angle and time
        hue = (angle / py5.TWO_PI * 360 + time_t * 50) % 360
        py5.stroke(hue, 80, 100, 50)
        
        py5.vertex(p.x, p.y)
        
        p.x += p.vx
        p.y += p.vy
        
        py5.vertex(p.x, p.y)
        
        # Wrap around screen
        if p.x < 0: p.x += py5.width
        if p.x > py5.width: p.x -= py5.width
        if p.y < 0: p.y += py5.height
        if p.y > py5.height: p.y -= py5.height

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

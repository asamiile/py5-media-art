from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random
import math

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

NUM_PARTICLES = 6000

class Particle:
    def __init__(self):
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.vx = 0
        self.vy = 0
        self.hue = random.uniform(0, 360)
        self.life = random.randint(50, 200)
        
    def respawn(self):
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.life = random.randint(50, 200)
        
    def update(self, time_val):
        # Glitchy flow field: snap angles to 45 degree increments
        n = py5.os_noise(self.x * 0.003, self.y * 0.003, time_val)
        angle = py5.remap(n, 0, 1, 0, py5.PI * 4)
        
        # Snap angle
        snap = py5.PI / 4
        angle = round(angle / snap) * snap
        
        speed = 5.0
        self.vx = py5.cos(angle) * speed
        self.vy = py5.sin(angle) * speed
        
        # Glitch jumps
        if random.random() < 0.01:
            self.x += random.uniform(-50, 50)
            self.y += random.uniform(-50, 50)
            
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        
        if self.x < 0 or self.x > SIZE[0] or self.y < 0 or self.y > SIZE[1] or self.life < 0:
            self.respawn()

particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 10, 15)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Fade background slightly to leave trails
    py5.fill(10, 10, 15, 20)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    time_val = py5.frame_count * 0.01
    
    py5.stroke_weight(2)
    for p in particles:
        p.update(time_val)
        
        # Shift hue based on direction and time
        hue = (p.hue + py5.frame_count * 0.5) % 360
        
        # Digital artifact colors (CMYK/RGB glitch)
        if random.random() < 0.05:
            hue = random.choice([0, 120, 240, 60, 300, 180])
            
        py5.stroke(hue, 90, 100, 150)
        
        # Draw small lines indicating direction
        py5.line(p.x, p.y, p.x - p.vx*2, p.y - p.vy*2)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

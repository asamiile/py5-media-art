from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import random

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

class Ripple:
    def __init__(self, x, y, hue):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = random.uniform(100, 600)
        self.speed = random.uniform(2, 6)
        self.hue = hue
        self.life = 1.0

    def update(self):
        self.radius += self.speed
        self.life -= 0.01
        
    def display(self):
        alpha = py5.remap(self.life, 0, 1, 0, 100)
        if alpha < 0: alpha = 0
        
        # Multiple rings per ripple for caustic effect
        for i in range(3):
            r = self.radius - i * 15
            if r > 0:
                py5.stroke(self.hue, 80, 100, alpha * (1.0 - i * 0.2))
                py5.circle(self.x, self.y, r * 2)

ripples = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(220, 100, 5, 20)  # Trail effect
    py5.blend_mode(py5.ADD)
    
    # Spawn new ripples
    if random.random() < 0.3:
        x = random.uniform(0, py5.width)
        y = random.uniform(0, py5.height)
        
        # Cyberpunk colors: Cyan to Magenta
        hue = random.choice([180, 190, 200, 300, 320]) + random.uniform(-10, 10)
        ripples.append(Ripple(x, y, hue))
        
    # Extra burst occasionally
    if py5.frame_count % 120 == 0:
        x = random.uniform(py5.width*0.2, py5.width*0.8)
        y = random.uniform(py5.height*0.2, py5.height*0.8)
        hue = 60 # Yellow burst
        for _ in range(5):
            r = Ripple(x + random.uniform(-50, 50), y + random.uniform(-50, 50), hue)
            ripples.append(r)
            
    py5.stroke_weight(3)
    
    for r in reversed(ripples):
        r.update()
        r.display()
        if r.life <= 0:
            ripples.remove(r)

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

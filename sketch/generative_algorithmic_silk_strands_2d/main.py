from pathlib import Path
import shutil
import subprocess
import sys
import py5
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 3000

class Particle:
    def __init__(self):
        self.reset()
        # Random initial time offset so they don't all look the same
        self.time_offset = random.uniform(0, 100)
        
    def reset(self):
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.px = self.x
        self.py = self.y
        # Base hue based on position
        self.base_hue = (self.x / SIZE[0] * 120 + 200) % 360 # Blue to Purple to Pink
        
    def update(self, time_val):
        self.px = self.x
        self.py = self.y
        
        # 3D noise for wind direction
        angle = py5.os_noise(self.x * 0.002, self.y * 0.002, time_val * 0.5 + self.time_offset) * py5.TWO_PI * 4
        
        # Velocity
        speed = 5
        self.x += py5.cos(angle) * speed
        self.y += py5.sin(angle) * speed
        
        # Wrap around
        if self.x < 0 or self.x > SIZE[0] or self.y < 0 or self.y > SIZE[1]:
            self.reset()
            # If wrapped, don't draw a line from old to new position
            self.px = self.x
            self.py = self.y

    def draw(self, time_val):
        hue = (self.base_hue + time_val * 20) % 360
        py5.stroke(hue, 80, 100, 15) # Very low alpha for silk effect
        py5.line(self.px, self.py, self.x, self.y)

particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Gradual fade for motion trails instead of clear
    py5.no_stroke()
    py5.fill(0, 0, 5, 10)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    time_val = py5.frame_count * 0.01
    
    for p in particles:
        p.update(time_val)
        p.draw(time_val)

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

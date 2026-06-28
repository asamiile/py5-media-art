from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

NUM_PARTICLES = 15000
particles = []

class Particle:
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.life = random.randint(50, 200)
        self.max_life = self.life

    def update(self, w, h, t):
        # Determine angle from noise field
        noise_val = py5.os_noise(self.x * 0.002, self.y * 0.002, t * 0.1)
        angle = noise_val * py5.TWO_PI * 4
        
        # Move particle
        speed = 4.0
        self.x += math.cos(angle) * speed
        self.y += math.sin(angle) * speed
        
        self.life -= 1
        
        # Reset if dead or off screen
        if self.life <= 0 or self.x < 0 or self.x > w or self.y < 0 or self.y > h:
            self.x = random.uniform(0, w)
            self.y = random.uniform(0, h)
            self.life = random.randint(50, 200)
            self.max_life = self.life

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(10, 80, 15)
    py5.no_stroke()
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle(py5.width, py5.height))

def draw():
    # Motion blur effect
    py5.fill(10, 80, 15, 8)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    for p in particles:
        p.update(py5.width, py5.height, t)
        
        # Determine color from position
        n = py5.os_noise(p.x * 0.001, p.y * 0.001, t * 0.05)
        hue = (n * 180 + 180 + py5.frame_count * 0.1) % 360
        
        # Fade based on life
        alpha = py5.remap(p.life, 0, p.max_life, 0, 255)
        
        py5.fill(hue, 80, 100, alpha)
        py5.circle(p.x, p.y, 3)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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

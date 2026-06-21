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

NUM_PARTICLES = 10000

class InkParticle:
    def __init__(self):
        # Start at the center with a small random offset
        a = random.uniform(0, py5.PI * 2)
        r = random.uniform(0, 20)
        self.x = SIZE[0] / 2 + py5.cos(a) * r
        self.y = SIZE[1] / 2 + py5.sin(a) * r
        self.vx = 0
        self.vy = 0
        
    def update(self, time_val):
        # Curl noise approximation
        scale = 0.002
        n1 = py5.os_noise(self.x * scale, self.y * scale, time_val)
        n2 = py5.os_noise(self.x * scale + 1000, self.y * scale + 1000, time_val)
        
        angle = py5.remap(n1, 0, 1, 0, py5.PI * 4)
        force = py5.remap(n2, 0, 1, 0.5, 2.0)
        
        # Outward bias
        dx = self.x - SIZE[0] / 2
        dy = self.y - SIZE[1] / 2
        dist = math.hypot(dx, dy)
        out_angle = math.atan2(dy, dx)
        
        # Mix noise angle and outward angle
        mix_ratio = 0.3 # 30% outward bias
        final_angle = angle * (1 - mix_ratio) + out_angle * mix_ratio
        
        self.vx += py5.cos(final_angle) * force * 0.1
        self.vy += py5.sin(final_angle) * force * 0.1
        
        # Friction
        self.vx *= 0.95
        self.vy *= 0.95
        
        self.x += self.vx
        self.y += self.vy

particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(30, 10, 95) # Off-white paper color
    py5.no_stroke()
    
    for _ in range(NUM_PARTICLES):
        particles.append(InkParticle())

def draw():
    time_val = py5.frame_count * 0.005
    
    # Don't clear background, let trails accumulate
    
    py5.fill(220, 80, 20, 5) # Dark blue ink, very transparent
    for p in particles:
        p.update(time_val)
        py5.circle(p.x, p.y, 2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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

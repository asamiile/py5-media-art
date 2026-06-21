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
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.vx = 0
        self.vy = 0
        self.hue_offset = random.uniform(0, 360)
        self.speed = random.uniform(1, 4)
        
    def update(self, frame):
        # Noise field
        noise_val = py5.os_noise(self.x * 0.002, self.y * 0.002, frame * 0.005)
        angle = noise_val * py5.TWO_PI * 4
        
        self.vx = py5.cos(angle) * self.speed
        self.vy = py5.sin(angle) * self.speed
        
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around edges
        if self.x < 0: self.x = SIZE[0]
        if self.x > SIZE[0]: self.x = 0
        if self.y < 0: self.y = SIZE[1]
        if self.y > SIZE[1]: self.y = 0
        
    def draw(self, frame):
        hue = (180 + py5.sin(frame * 0.01 + self.hue_offset) * 60) % 360
        py5.stroke(hue, 80, 100, 50)
        py5.point(self.x, self.y)

particles = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0, 0, 5)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Fade background to create trails
    py5.fill(0, 0, 5, 10)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    for p in particles:
        p.update(py5.frame_count)
        p.draw(py5.frame_count)
        
    py5.blend_mode(py5.BLEND)

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

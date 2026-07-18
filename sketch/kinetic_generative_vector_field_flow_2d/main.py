from pathlib import Path
import shutil
import subprocess
import sys
import math
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

NUM_PARTICLES = 20000

class Particle:
    def __init__(self):
        self.reset()
        self.life = random.random()

    def reset(self):
        self.x = random.uniform(0, SIZE[0])
        self.y = random.uniform(0, SIZE[1])
        self.life = 0.0

    def update(self, loop_t, speed):
        nx = self.x * 0.0015
        ny = self.y * 0.0015
        
        R = 0.6
        cx = math.cos(loop_t) * R
        cy = math.sin(loop_t) * R
        
        angle_noise = py5.os_noise(nx, ny, cx, cy) * py5.TWO_PI * 5
        
        self.x += math.cos(angle_noise) * speed
        self.y += math.sin(angle_noise) * speed
        
        self.life += 1.0 / (FPS * 2.5) 
        if self.life > 1.0:
            self.reset()
            
        if self.x < 0: self.x += SIZE[0]
        if self.x > SIZE[0]: self.x -= SIZE[0]
        if self.y < 0: self.y += SIZE[1]
        if self.y > SIZE[1]: self.y -= SIZE[1]

particles = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())
        
    py5.background(240, 80, 5)
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    
    py5.fill(250, 80, 3, 20)
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.5)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    for p in particles:
        old_x, old_y = p.x, p.y
        p.update(loop_t, 16.0)
        
        if abs(p.x - old_x) < 50 and abs(p.y - old_y) < 50:
            hue = (p.x * 0.03 + p.y * 0.03 + t * 360) % 360
            alpha = math.sin(p.life * py5.PI) * 120
            
            py5.stroke(hue, 90, 95, alpha)
            py5.line(old_x, old_y, p.x, p.y)

    py5.color_mode(py5.RGB, 255)

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

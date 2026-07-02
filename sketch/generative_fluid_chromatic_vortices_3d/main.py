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

NUM_PARTICLES = 4000

class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.uniform(-SIZE[0]*0.5, SIZE[0]*1.5)
        self.y = random.uniform(-SIZE[1]*0.5, SIZE[1]*1.5)
        self.z = random.uniform(-500, 500)
        self.px = self.x
        self.py = self.y
        self.pz = self.z
        
        self.hue = random.uniform(0, 360)
        
    def update(self, time_val):
        self.px = self.x
        self.py = self.y
        self.pz = self.z
        
        # 3D Vector field
        noise_scale = 0.003
        angle_x = py5.os_noise(self.x * noise_scale, self.y * noise_scale, time_val) * py5.TWO_PI * 4
        angle_y = py5.os_noise(self.x * noise_scale + 100, self.y * noise_scale, time_val) * py5.TWO_PI * 4
        
        speed = 8
        self.x += py5.cos(angle_x) * speed
        self.y += py5.sin(angle_y) * speed
        self.z += py5.sin(angle_x + angle_y) * speed * 0.5
        
        # Bound check - reset if it goes too far out
        if self.x < -SIZE[0]*0.5 or self.x > SIZE[0]*1.5 or self.y < -SIZE[1]*0.5 or self.y > SIZE[1]*1.5:
            self.reset()
            self.px = self.x
            self.py = self.y
            self.pz = self.z

    def draw(self, time_val):
        color_shift = (self.hue + time_val * 50) % 360
        py5.stroke(color_shift, 80, 100, 40)
        py5.line(self.px, self.py, self.pz, self.x, self.y, self.z)

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    # Motion blur effect
    py5.no_stroke()
    py5.fill(0, 0, 5, 20)
    py5.push_matrix()
    py5.translate(0, 0, -500) # Draw big background far back
    py5.rect(-SIZE[0], -SIZE[1], SIZE[0]*3, SIZE[1]*3)
    py5.pop_matrix()
    
    py5.blend_mode(py5.ADD)
    
    # Camera
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    time_val = py5.frame_count * 0.01
    
    # Slow dramatic rotation
    py5.rotate_x(time_val * 0.2)
    py5.rotate_y(time_val * 0.3)
    
    # Draw all particles centered around 0,0,0
    py5.translate(-SIZE[0]/2, -SIZE[1]/2, 0)
    
    py5.stroke_weight(3)
    
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

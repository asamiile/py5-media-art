from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle parameters
NUM_PARTICLES = 3000
particles = []

class Particle:
    def __init__(self):
        self.angle = py5.random(py5.TWO_PI)
        self.radius = py5.random(100, SIZE[0] * 0.8)
        self.y = py5.random(-SIZE[1], SIZE[1])
        self.speed_angle = py5.random(0.01, 0.05)
        self.speed_y = py5.random(2, 10)
        self.size = py5.random(5, 20)
        # Deep cyan and electric blue
        self.hue = py5.random(180, 220)

    def update(self, frame_ratio):
        # Swirling hurricane motion
        self.angle += self.speed_angle + py5.os_noise(self.radius * 0.01, self.y * 0.01, frame_ratio * 2) * 0.05
        self.y -= self.speed_y
        
        # Funnel shape: radius depends on y
        target_radius = py5.remap(self.y, -SIZE[1], SIZE[1], SIZE[0] * 0.8, 50)
        self.radius = py5.lerp(self.radius, target_radius, 0.05)

        if self.y < -SIZE[1]:
            self.y = SIZE[1]
            self.radius = SIZE[0] * 0.8

    def draw(self):
        py5.push_matrix()
        x = py5.cos(self.angle) * self.radius
        z = py5.sin(self.angle) * self.radius
        py5.translate(x, self.y, z)
        
        # Orient to center
        py5.rotate_y(-self.angle)
        
        py5.fill(self.hue, 255, 255, 150)
        py5.no_stroke()
        py5.box(self.size, self.size * 3, self.size)
        py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_PARTICLES):
        particles.append(Particle())

def draw():
    py5.background(10, 20, 30)
    py5.lights()
    py5.ambient_light(180, 255, 100)
    py5.directional_light(200, 255, 255, 0, 1, -1)
    
    # Camera position
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    py5.rotate_x(py5.radians(-20))
    py5.rotate_y(py5.frame_count * 0.005)
    
    py5.blend_mode(py5.ADD)
    
    frame_ratio = py5.frame_count / TOTAL_FRAMES
    
    for p in particles:
        p.update(frame_ratio)
        p.draw()
        
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

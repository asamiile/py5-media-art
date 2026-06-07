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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Particle:
    def __init__(self):
        self.angle = random.uniform(0, py5.TWO_PI)
        self.speed = random.uniform(0.02, 0.08)
        self.tube_angle = random.uniform(0, py5.TWO_PI)
        self.tube_speed = random.uniform(-0.05, 0.05)
        self.color_hue = random.choice([200, 220, 20])
        self.radius = random.uniform(2, 6)
        
    def update(self):
        self.angle += self.speed
        self.tube_angle += self.tube_speed

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    
    for _ in range(800):
        particles.append(Particle())

def draw():
    py5.background(10, 100, 5) # Deep navy black
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.005)
    
    R = py5.width * 0.4 # Major radius
    r = py5.width * 0.08 # Minor radius
    
    py5.blend_mode(py5.ADD)
    
    # Draw Torus shell
    py5.no_fill()
    py5.stroke(220, 80, 40, 30)
    py5.stroke_weight(1)
    
    steps_major = 60
    steps_minor = 20
    
    for i in range(steps_major):
        theta1 = py5.TWO_PI * i / steps_major
        theta2 = py5.TWO_PI * (i + 1) / steps_major
        
        py5.begin_shape(py5.LINES)
        for j in range(steps_minor):
            phi = py5.TWO_PI * j / steps_minor
            
            x1 = (R + r * math.cos(phi)) * math.cos(theta1)
            y1 = (R + r * math.cos(phi)) * math.sin(theta1)
            z1 = r * math.sin(phi)
            
            x2 = (R + r * math.cos(phi)) * math.cos(theta2)
            y2 = (R + r * math.cos(phi)) * math.sin(theta2)
            z2 = r * math.sin(phi)
            
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
        py5.end_shape()
        
    py5.no_stroke()
    
    # Draw Particles
    for p in particles:
        p.update()
        px = (R + r * math.cos(p.tube_angle)) * math.cos(p.angle)
        py = (R + r * math.cos(p.tube_angle)) * math.sin(p.angle)
        pz = r * math.sin(p.tube_angle)
        
        py5.push_matrix()
        py5.translate(px, py, pz)
        py5.fill(p.color_hue, 90, 100, 200)
        py5.sphere(p.radius)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

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

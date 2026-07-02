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

class PlasmaParticle:
    def __init__(self):
        self.reset()
        r = random.uniform(0, 300)
        theta = random.uniform(0, 2 * py5.PI)
        phi = random.uniform(0, py5.PI)
        self.x = r * py5.sin(phi) * py5.cos(theta)
        self.y = r * py5.sin(phi) * py5.sin(theta)
        self.z = r * py5.cos(phi)
        
    def reset(self):
        self.x = random.uniform(-50, 50)
        self.y = random.uniform(-50, 50)
        self.z = random.uniform(-50, 50)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.vz = random.uniform(-2, 2)
        self.life = random.uniform(0.5, 1.0)
        self.max_life = self.life
        self.color_hue = random.uniform(10, 40)

    def update(self):
        noise_scale = 0.005
        time_offset = py5.frame_count * 0.01
        angle_x = py5.os_noise(self.x * noise_scale, self.y * noise_scale, time_offset) * 4 * py5.PI
        angle_y = py5.os_noise(self.y * noise_scale, self.z * noise_scale, time_offset + 100) * 4 * py5.PI
        
        dist = py5.dist(0, 0, 0, self.x, self.y, self.z)
        pull = 0
        if dist > 300:
            pull = (dist - 300) * 0.05
            
        self.vx += py5.cos(angle_x) * 1.5 - (self.x / dist) * pull if dist > 0 else 0
        self.vy += py5.sin(angle_x) * 1.5 - (self.y / dist) * pull if dist > 0 else 0
        self.vz += py5.sin(angle_y) * 1.5 - (self.z / dist) * pull if dist > 0 else 0
        
        self.vx *= 0.95
        self.vy *= 0.95
        self.vz *= 0.95
        
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        
        self.life -= 0.01
        if self.life <= 0:
            self.reset()

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(3000):
        particles.append(PlasmaParticle())

def draw():
    py5.background(270, 80, 5)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.no_fill()
    py5.stroke_weight(4)
    py5.stroke(180, 80, 100, 80)
    
    for i in range(3):
        py5.push_matrix()
        py5.rotate_x(py5.frame_count * 0.01 * (i + 1))
        py5.rotate_y(py5.frame_count * 0.015 * (i + 1) + py5.PI / 4 * i)
        py5.rotate_z(py5.frame_count * 0.005 * (i + 1))
        
        py5.circle(0, 0, 800)
        py5.stroke_weight(1)
        py5.stroke(180, 80, 100, 40)
        py5.circle(0, 0, 780)
        py5.circle(0, 0, 820)
        py5.pop_matrix()
        
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    for p in particles:
        p.update()
        alpha = (p.life / p.max_life) * 80
        size = (p.life / p.max_life) * 15
        py5.fill(p.color_hue, 90, 100, alpha)
        
        py5.push_matrix()
        py5.translate(p.x, p.y, p.z)
        py5.box(size)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
    py5.pop_matrix()

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

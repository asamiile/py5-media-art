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
        self.reset()
        
    def reset(self):
        self.x = random.uniform(-600, 600)
        self.y = random.uniform(-600, 600)
        self.z = random.uniform(-600, 600)
        self.life = random.uniform(50, 150)
        self.max_life = self.life
        self.hue = random.choice([45, 10, 280]) # Gold, Red, Violet
        self.size = random.uniform(2, 6)

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_stroke()
    
    for _ in range(3000):
        particles.append(Particle())

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.015
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    
    noise_scale = 0.005
    
    for p in particles:
        # Flowfield based on 3D noise (incorporating t into z)
        angle_x = py5.noise(p.x * noise_scale, p.y * noise_scale, p.z * noise_scale + t) * py5.TWO_PI * 4
        angle_y = py5.noise(p.y * noise_scale, p.z * noise_scale, p.x * noise_scale + t) * py5.TWO_PI * 4
        angle_z = py5.noise(p.z * noise_scale, p.x * noise_scale, p.y * noise_scale + t) * py5.TWO_PI * 4
        
        # Velocity
        vx = math.cos(angle_x) * 4
        vy = math.sin(angle_y) * 4
        vz = math.sin(angle_z) * 4
        
        p.x += vx
        p.y += vy
        p.z += vz
        p.life -= 1
        
        # Wrapping
        if p.x > 800: p.x = -800
        if p.x < -800: p.x = 800
        if p.y > 800: p.y = -800
        if p.y < -800: p.y = 800
        if p.z > 800: p.z = -800
        if p.z < -800: p.z = 800
        
        if p.life <= 0:
            p.reset()
            
        alpha = py5.remap(p.life, 0, p.max_life, 0, 150)
        
        py5.push_matrix()
        py5.translate(p.x, p.y, p.z)
        
        # Core
        py5.fill(p.hue, 80, 100, alpha)
        py5.sphere(p.size)
        
        # Glow
        py5.fill(p.hue, 100, 100, alpha * 0.3)
        py5.sphere(p.size * 3)
        
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

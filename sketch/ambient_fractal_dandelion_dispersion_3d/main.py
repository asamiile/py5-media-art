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

class Seed:
    def __init__(self):
        r = random.uniform(10, 50)
        theta = random.uniform(0, 2 * py5.PI)
        phi = random.uniform(0, py5.PI)
        self.orig_x = r * py5.sin(phi) * py5.cos(theta)
        self.orig_y = r * py5.sin(phi) * py5.sin(theta)
        self.orig_z = r * py5.cos(phi)
        
        self.x = self.orig_x
        self.y = self.orig_y
        self.z = self.orig_z
        
        # Explosion velocity
        speed = random.uniform(2, 6)
        dist = py5.dist(0, 0, 0, self.x, self.y, self.z) + 0.1
        self.vx = (self.x / dist) * speed
        self.vy = (self.y / dist) * speed
        self.vz = (self.z / dist) * speed
        
        self.life = 1.0
        self.delay = random.uniform(0, 60) # Frame delay before explosion
        self.rot_speed = random.uniform(0.01, 0.05)
        self.rot_axis = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))

    def update(self, frame):
        if frame < self.delay:
            return
            
        noise_scale = 0.002
        time_offset = py5.frame_count * 0.01
        
        angle_x = py5.os_noise(self.x * noise_scale, self.y * noise_scale, time_offset) * 4 * py5.PI
        angle_y = py5.os_noise(self.y * noise_scale, self.z * noise_scale, time_offset + 100) * 4 * py5.PI
        
        self.vx += py5.cos(angle_x) * 0.1
        self.vy += py5.sin(angle_x) * 0.1
        self.vz += py5.sin(angle_y) * 0.1
        
        self.vx *= 0.98
        self.vy *= 0.98
        self.vz *= 0.98
        
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        
        self.life -= 0.002
        if self.life < 0:
            self.life = 0

seeds = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(2500):
        seeds.append(Seed())

def draw():
    py5.background(0)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera slow rotation and zoom out
    py5.rotate_y(py5.frame_count * 0.002)
    py5.scale(1.0 - (py5.frame_count / TOTAL_FRAMES) * 0.5)
    
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    for s in seeds:
        s.update(py5.frame_count)
        if s.life <= 0:
            continue
            
        alpha = s.life * 60
        py5.stroke(200, 40, 100, alpha) # Ethereal white/blue
        py5.stroke_weight(1)
        
        py5.push_matrix()
        py5.translate(s.x, s.y, s.z)
        
        py5.rotate_x(py5.frame_count * s.rot_speed * s.rot_axis[0])
        py5.rotate_y(py5.frame_count * s.rot_speed * s.rot_axis[1])
        py5.rotate_z(py5.frame_count * s.rot_speed * s.rot_axis[2])
        
        # Draw a little cross/seed shape
        s_size = 10 * s.life
        py5.line(-s_size, 0, 0, s_size, 0, 0)
        py5.line(0, -s_size, 0, 0, s_size, 0)
        py5.line(0, 0, -s_size, 0, 0, s_size)
        
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

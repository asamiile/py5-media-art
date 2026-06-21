from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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

class Shard:
    def __init__(self):
        self.x = py5.random(-100, 100)
        self.y = py5.random(-100, 100)
        self.z = py5.random(-100, 100)
        self.rx = py5.random(py5.TWO_PI)
        self.ry = py5.random(py5.TWO_PI)
        self.rz = py5.random(py5.TWO_PI)
        
        self.size_x = py5.random(10, 80)
        self.size_y = py5.random(10, 80)
        self.size_z = py5.random(10, 80)
        
        self.hue = py5.random(200, 300) # Blues and purples
        
        # Explosion velocity
        dist = max(1, np.linalg.norm([self.x, self.y, self.z]))
        self.vx = self.x / dist * py5.random(5, 20)
        self.vy = self.y / dist * py5.random(5, 20)
        self.vz = self.z / dist * py5.random(5, 20)
        
        self.vrx = py5.random(-0.2, 0.2)
        self.vry = py5.random(-0.2, 0.2)
        self.vrz = py5.random(-0.2, 0.2)
        
        self.fractured = False

    def update(self, t, is_fractured):
        if is_fractured and not self.fractured:
            self.fractured = True
            
        if self.fractured:
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            self.rx += self.vrx
            self.ry += self.vry
            self.rz += self.vrz
            
            # Gravity? No, zero-g space explosion
            self.vx *= 0.98
            self.vy *= 0.98
            self.vz *= 0.98
            
    def draw(self, is_fractured):
        py5.push_matrix()
        # If not fractured, they form a tight cluster (the "crystal")
        if not is_fractured:
            py5.translate(self.x * 0.5, self.y * 0.5, self.z * 0.5)
        else:
            py5.translate(self.x, self.y, self.z)
            
        py5.rotate_x(self.rx)
        py5.rotate_y(self.ry)
        py5.rotate_z(self.rz)
        
        # Draw translucent crystal shard
        py5.fill(self.hue, 80, 100, 40)
        py5.stroke(self.hue, 90, 100, 80)
        py5.stroke_weight(2)
        
        # Actually a box is fine, looks like a crystal lattice block
        py5.box(self.size_x, self.size_y, self.size_z)
        py5.pop_matrix()

shards = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for _ in range(300):
        shards.append(Shard())

def draw():
    py5.background(10, 5, 20)
    
    py5.translate(py5.width/2, py5.height/2, -500)
    
    t = py5.frame_count
    
    # Rotate entire scene
    py5.rotate_y(t * 0.01)
    py5.rotate_x(py5.sin(t * 0.005) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    # Fracture occurs at frame 300 (5 seconds)
    fracture_frame = 300
    is_fractured = t > fracture_frame
    
    # Shake effect right before fracture
    if fracture_frame - 60 < t <= fracture_frame:
        intensity = py5.remap(t, fracture_frame - 60, fracture_frame, 0, 30)
        py5.translate(py5.random(-intensity, intensity), py5.random(-intensity, intensity), py5.random(-intensity, intensity))
    
    for s in shards:
        s.update(t, is_fractured)
        s.draw(is_fractured)
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
            
        import os
        os._exit(0)

py5.run_sketch()

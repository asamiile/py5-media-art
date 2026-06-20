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

# Particles making up the mitochondrion
class MitoParticle:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.dissolved = False
        self.dissolve_time = py5.random(TOTAL_FRAMES * 0.2, TOTAL_FRAMES * 0.8)
        self.hue = py5.random(0, 40) # Red/Orange for mitochondria

    def update(self, t):
        if py5.frame_count > self.dissolve_time:
            self.dissolved = True
            
        if self.dissolved:
            # Swarm behavior, bounded by vacuole
            self.vx += py5.random(-1, 1)
            self.vy += py5.random(-1, 1)
            self.vz += py5.random(-1, 1)
            
            # Repel from center slightly to fill the vacuole
            d = py5.dist(0, 0, 0, self.x, self.y, self.z)
            if d < 300:
                self.vx += self.x * 0.001
                self.vy += self.y * 0.001
                self.vz += self.z * 0.001
                
            # Containment by vacuole (radius ~350)
            if d > 350:
                self.vx -= self.x * 0.01
                self.vy -= self.y * 0.01
                self.vz -= self.z * 0.01
                
            self.vx *= 0.95
            self.vy *= 0.95
            self.vz *= 0.95
            
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            
            self.hue = py5.lerp(self.hue, 120, 0.05) # Turn green as it digests
            
    def draw(self):
        py5.push_matrix()
        py5.translate(self.x, self.y, self.z)
        py5.fill(self.hue, 80, 100, 80)
        py5.box(8)
        py5.pop_matrix()

particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    
    # Construct a pill-like mitochondrial shape
    for _ in range(2000):
        # random point in cylinder-ish shape
        r = py5.random(0, 80)
        ang = py5.random(py5.TWO_PI)
        x = r * py5.cos(ang)
        y = r * py5.sin(ang)
        z = py5.random(-150, 150)
        
        # Round the ends
        if z > 100:
            r2 = py5.remap(z, 100, 150, 80, 0)
            if r > r2: continue
        elif z < -100:
            r2 = py5.remap(z, -100, -150, 80, 0)
            if r > r2: continue
            
        particles.append(MitoParticle(x, y, z))

def draw():
    py5.background(10, 5, 15)
    
    py5.translate(py5.width/2, py5.height/2, -400)
    
    # Rotate scene
    py5.rotate_x(py5.frame_count * 0.01)
    py5.rotate_y(py5.frame_count * 0.015)
    
    py5.blend_mode(py5.ADD)
    
    # Draw vacuole boundary
    py5.push_matrix()
    py5.stroke(200, 80, 80, 20)
    py5.stroke_weight(2)
    py5.fill(200, 80, 20, 10)
    py5.sphere_detail(30)
    py5.sphere(360)
    py5.pop_matrix()
    
    py5.no_stroke()
    
    for p in particles:
        p.update(py5.frame_count)
        p.draw()
        
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

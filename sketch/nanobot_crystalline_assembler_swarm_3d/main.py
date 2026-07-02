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

class Boid:
    def __init__(self):
        self.x = random.uniform(-400, 400)
        self.y = random.uniform(-400, 400)
        self.z = random.uniform(-400, 400)
        
        theta = random.uniform(0, py5.TWO_PI)
        phi = random.uniform(0, py5.PI)
        speed = 5
        self.vx = speed * math.sin(phi) * math.cos(theta)
        self.vy = speed * math.sin(phi) * math.sin(theta)
        self.vz = speed * math.cos(phi)
        
        self.hue = random.choice([160, 190]) # Emerald Green, Cyan
        
boids = []
num_boids = 800

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    for _ in range(num_boids):
        boids.append(Boid())

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    time = py5.frame_count * 0.01
    progress = py5.frame_count / TOTAL_FRAMES
    
    py5.rotate_y(progress * py5.TWO_PI)
    py5.rotate_x(math.sin(progress * py5.TWO_PI) * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Assembly target
    tx = py5.noise(time) * 600 - 300
    ty = py5.noise(time + 100) * 600 - 300
    tz = py5.noise(time + 200) * 600 - 300
    
    # Swarm logic
    for i, b in enumerate(boids):
        # Noise force
        nx = py5.noise(b.x * 0.005, time) - 0.5
        ny = py5.noise(b.y * 0.005, time + 10) - 0.5
        nz = py5.noise(b.z * 0.005, time + 20) - 0.5
        
        # Seek target
        dx = tx - b.x
        dy = ty - b.y
        dz = tz - b.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.001
        
        pull = 0.5 if dist > 200 else -2.0 # Pull then repel to form shell
        
        b.vx += nx * 2 + (dx/dist) * pull
        b.vy += ny * 2 + (dy/dist) * pull
        b.vz += nz * 2 + (dz/dist) * pull
        
        # Limit speed
        speed = math.sqrt(b.vx**2 + b.vy**2 + b.vz**2)
        if speed > 10:
            b.vx = (b.vx / speed) * 10
            b.vy = (b.vy / speed) * 10
            b.vz = (b.vz / speed) * 10
            
        # Containment
        r = 600
        if b.x*b.x + b.y*b.y + b.z*b.z > r*r:
            b.vx -= b.x * 0.005
            b.vy -= b.y * 0.005
            b.vz -= b.z * 0.005
            
        b.x += b.vx
        b.y += b.vy
        b.z += b.vz
        
    # Draw connections
    py5.stroke_weight(2)
    for i in range(len(boids)):
        b1 = boids[i]
        
        # Draw boid
        py5.push_matrix()
        py5.translate(b1.x, b1.y, b1.z)
        py5.no_stroke()
        py5.fill(b1.hue, 80, 100, 150)
        py5.box(5)
        py5.pop_matrix()
        
        # Connect nearby
        count = 0
        for j in range(i + 1, len(boids)):
            b2 = boids[j]
            dx = b1.x - b2.x
            dy = b1.y - b2.y
            dz = b1.z - b2.z
            dist_sq = dx*dx + dy*dy + dz*dz
            
            if dist_sq < 4000: # Distance 63
                alpha = py5.remap(dist_sq, 0, 4000, 200, 0)
                py5.stroke(b1.hue, 50, 100, alpha)
                py5.line(b1.x, b1.y, b1.z, b2.x, b2.y, b2.z)
                count += 1
                if count > 4: # Max 4 connections per boid for performance and aesthetics
                    break

    py5.blend_mode(py5.BLEND)

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

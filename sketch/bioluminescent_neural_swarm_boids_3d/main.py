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
        
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.vz = random.uniform(-2, 2)
        
        self.hue = random.choice([160, 200, 300]) # Green, Blue, Magenta
        self.history = []

boids = []
num_boids = 400

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
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    
    max_speed = 8
    max_force = 0.2
    perception = 100
    
    # Simple flocking approximation
    for i, b in enumerate(boids):
        cohesion_x = cohesion_y = cohesion_z = 0
        align_x = align_y = align_z = 0
        separation_x = separation_y = separation_z = 0
        count = 0
        
        for j, other in enumerate(boids):
            if i != j:
                d = math.sqrt((b.x - other.x)**2 + (b.y - other.y)**2 + (b.z - other.z)**2)
                if 0 < d < perception:
                    cohesion_x += other.x
                    cohesion_y += other.y
                    cohesion_z += other.z
                    
                    align_x += other.vx
                    align_y += other.vy
                    align_z += other.vz
                    
                    if d < perception / 2:
                        separation_x += (b.x - other.x) / d
                        separation_y += (b.y - other.y) / d
                        separation_z += (b.z - other.z) / d
                    
                    count += 1
                    
        if count > 0:
            cohesion_x /= count
            cohesion_y /= count
            cohesion_z /= count
            
            align_x /= count
            align_y /= count
            align_z /= count
            
            # Steer towards cohesion
            vx_steer = (cohesion_x - b.x) * 0.01
            vy_steer = (cohesion_y - b.y) * 0.01
            vz_steer = (cohesion_z - b.z) * 0.01
            
            # Align
            vx_steer += align_x * 0.05
            vy_steer += align_y * 0.05
            vz_steer += align_z * 0.05
            
            # Separate
            vx_steer += separation_x * 0.1
            vy_steer += separation_y * 0.1
            vz_steer += separation_z * 0.1
            
            b.vx += vx_steer
            b.vy += vy_steer
            b.vz += vz_steer
            
        # Center gravity
        b.vx -= b.x * 0.001
        b.vy -= b.y * 0.001
        b.vz -= b.z * 0.001
        
        # Limit speed
        speed = math.sqrt(b.vx**2 + b.vy**2 + b.vz**2)
        if speed > max_speed:
            b.vx = (b.vx / speed) * max_speed
            b.vy = (b.vy / speed) * max_speed
            b.vz = (b.vz / speed) * max_speed
            
        b.x += b.vx
        b.y += b.vy
        b.z += b.vz
        
        b.history.append((b.x, b.y, b.z))
        if len(b.history) > 15:
            b.history.pop(0)
            
    # Render
    py5.no_fill()
    for b in boids:
        py5.stroke(b.hue, 80, 100, 150)
        py5.stroke_weight(2)
        py5.begin_shape(py5.LINE_STRIP)
        for i, pos in enumerate(b.history):
            alpha = py5.remap(i, 0, len(b.history), 0, 150)
            py5.stroke(b.hue, 80, 100, alpha)
            py5.vertex(pos[0], pos[1], pos[2])
        py5.end_shape()
        
        py5.push_matrix()
        py5.translate(b.x, b.y, b.z)
        py5.no_stroke()
        py5.fill(b.hue, 90, 100, 200)
        py5.sphere(4)
        py5.pop_matrix()
        
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

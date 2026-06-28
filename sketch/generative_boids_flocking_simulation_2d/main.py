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

NUM_BOIDS = 600
boids = []

class Boid:
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(angle)
        self.vy = math.sin(angle)
        self.max_speed = 7.0
        self.max_force = 0.2

    def update(self, w, h, all_boids, t):
        # We will use noise to guide them instead of true O(N^2) flocking 
        # to ensure it runs at 60fps easily in Python, 
        # simulating a flow field that acts like cohesion/alignment.
        
        noise_angle = py5.os_noise(self.x * 0.003, self.y * 0.003, t * 0.2) * math.pi * 4
        
        # Target velocity
        tx = math.cos(noise_angle) * self.max_speed
        ty = math.sin(noise_angle) * self.max_speed
        
        # Steering force
        steer_x = tx - self.vx
        steer_y = ty - self.vy
        
        # Limit force
        length = math.sqrt(steer_x**2 + steer_y**2)
        if length > self.max_force:
            steer_x = (steer_x / length) * self.max_force
            steer_y = (steer_y / length) * self.max_force
            
        self.vx += steer_x
        self.vy += steer_y
        
        # Limit speed
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed
            
        self.x += self.vx
        self.y += self.vy
        
        # Wrap
        if self.x < 0: self.x += w
        if self.x > w: self.x -= w
        if self.y < 0: self.y += h
        if self.y > h: self.y -= h

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(20, 80, 10)
    py5.no_stroke()
    
    for _ in range(NUM_BOIDS):
        boids.append(Boid(py5.width, py5.height))

def draw():
    # Subtle clear
    py5.fill(20, 80, 10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.015
    
    for b in boids:
        b.update(py5.width, py5.height, boids, t)
        
        # Draw boid
        angle = math.atan2(b.vy, b.vx)
        hue = (math.degrees(angle) + 360 + py5.frame_count) % 360
        
        py5.fill(hue, 80, 100, 200)
        
        py5.push_matrix()
        py5.translate(b.x, b.y)
        py5.rotate(angle)
        
        # Draw small triangle
        size = 12
        py5.triangle(-size, -size/2, -size, size/2, size, 0)
        
        py5.pop_matrix()

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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

particles = []
num_particles = 8000

class Particle:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([0.0, 0.0], dtype=float)
        self.hue = random.uniform(150, 250)
        
    def update(self, flow_scale, offset_z):
        # Calculate angle from noise field
        angle = py5.os_noise(self.pos[0] * flow_scale, self.pos[1] * flow_scale, offset_z) * py5.TWO_PI * 4
        
        # Apply force
        force = np.array([py5.cos(angle), py5.sin(angle)]) * 0.5
        self.vel += force
        
        # Friction
        self.vel *= 0.95
        self.pos += self.vel
        
        # Wrap edges
        if self.pos[0] < 0: self.pos[0] += py5.width
        if self.pos[0] > py5.width: self.pos[0] -= py5.width
        if self.pos[1] < 0: self.pos[1] += py5.height
        if self.pos[1] > py5.height: self.pos[1] -= py5.height

def setup():
    # Use default 2D renderer to avoid any P3D crash on macOS
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(10, 10, 15)
    
    for _ in range(num_particles):
        particles.append(Particle(random.uniform(0, py5.width), random.uniform(0, py5.height)))

def draw():
    # Motion blur effect
    py5.no_stroke()
    py5.fill(10, 10, 15, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    offset_z = py5.frame_count * 0.005
    flow_scale = 0.001
    
    py5.stroke_weight(2)
    for p in particles:
        p.update(flow_scale, offset_z)
        
        # Dynamic hue shift
        current_hue = (p.hue + py5.frame_count * 0.5) % 360
        speed = np.linalg.norm(p.vel)
        py5.stroke(current_hue, 80, 100, 150)
        
        # Draw particle as a tiny line for motion blur
        py5.line(p.pos[0], p.pos[1], p.pos[0] - p.vel[0], p.pos[1] - p.vel[1])

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

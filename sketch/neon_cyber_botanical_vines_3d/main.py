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

VINES = []
NUM_VINES = 40

class Vine:
    def __init__(self, idx):
        self.idx = idx
        self.points = []
        self.theta = random.uniform(0, py5.TWO_PI)
        self.y = -SIZE[1]
        self.radius = random.uniform(100, 600)
        self.speed = random.uniform(5, 12)
        self.growth_angle = random.uniform(0.01, 0.03)
        self.hue = py5.random(80, 140) if random.random() > 0.4 else py5.random(260, 300)
        
    def update(self):
        self.y += self.speed
        self.theta += self.growth_angle
        
        nx = py5.os_noise(self.y * 0.005, self.idx * 10) * 200
        nz = py5.os_noise(self.y * 0.005 + 100, self.idx * 10) * 200
        
        x = py5.cos(self.theta) * self.radius + nx
        z = py5.sin(self.theta) * self.radius + nz
        
        self.points.append((x, self.y, z))
        if len(self.points) > 150:
            self.points.pop(0)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(NUM_VINES):
        VINES.append(Vine(i))

def draw():
    py5.background(0)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(0.3)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(4)
    
    for vine in VINES:
        vine.update()
        py5.stroke(vine.hue, 90, 100, 60)
        py5.begin_shape()
        for p in vine.points:
            py5.vertex(*p)
        py5.end_shape()
        
        if vine.points:
            py5.push_matrix()
            py5.translate(*vine.points[-1])
            py5.no_stroke()
            py5.fill(vine.hue, 50, 100, 100)
            py5.sphere(10)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
        import os
        os._exit(0)

py5.run_sketch()

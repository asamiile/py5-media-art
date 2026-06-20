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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RINGS = 30

class Ring:
    def __init__(self, i):
        self.id = i
        self.radius = 400 + py5.random(-50, 50) if i > 10 else 200 + py5.random(-30, 30)
        self.rot_x = random.uniform(0, py5.TWO_PI)
        self.rot_y = random.uniform(0, py5.TWO_PI)
        self.rot_z = random.uniform(0, py5.TWO_PI)
        self.speed_x = random.uniform(-0.02, 0.02)
        self.speed_y = random.uniform(-0.02, 0.02)
        self.speed_z = random.uniform(-0.02, 0.02)
        self.hue = random.uniform(180, 280)
        self.points = int(random.uniform(20, 100))
        self.dots = []
        for _ in range(self.points):
            if random.random() > 0.5:
                self.dots.append(random.uniform(0, py5.TWO_PI))

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
    global rings
    rings = [Ring(i) for i in range(NUM_RINGS)]

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Global rotation
    py5.rotate_x(t * 0.1)
    py5.rotate_y(t * 0.15)
    
    # Draw core sphere
    py5.no_stroke()
    py5.fill(200, 80, 50, 40)
    py5.sphere_detail(10)
    py5.sphere(150 + 20 * py5.sin(t*2))
    
    # Draw rings
    py5.no_fill()
    for ring in rings:
        py5.push_matrix()
        
        py5.rotate_x(ring.rot_x + t * ring.speed_x)
        py5.rotate_y(ring.rot_y + t * ring.speed_y)
        py5.rotate_z(ring.rot_z + t * ring.speed_z)
        
        # Draw ring track
        py5.stroke(ring.hue, 80, 30, 60)
        py5.stroke_weight(1)
        
        py5.begin_shape()
        res = 60
        for i in range(res + 1):
            angle = (i / res) * py5.TWO_PI
            py5.vertex(ring.radius * py5.cos(angle), ring.radius * py5.sin(angle), 0)
        py5.end_shape(py5.CLOSE)
        
        # Draw data points on ring
        py5.stroke(ring.hue, 90, 100, 90)
        py5.stroke_weight(4)
        for dot_angle in ring.dots:
            a = dot_angle + t * ring.speed_z * 2
            x = ring.radius * py5.cos(a)
            y = ring.radius * py5.sin(a)
            py5.point(x, y, 0)
            
            # Occasional line to core
            if py5.os_noise(ring.id, dot_angle, t * 0.1) > 0.8:
                py5.stroke_weight(1)
                py5.stroke((ring.hue + 50) % 360, 80, 80, 40)
                py5.line(x, y, 0, 0, 0, 0)
                py5.stroke_weight(4)
                py5.stroke(ring.hue, 90, 100, 90)
                
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

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

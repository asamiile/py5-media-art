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

class QuantumParticle:
    def __init__(self):
        self.pos = np.array([random.uniform(-400, 400), random.uniform(-400, 400), random.uniform(-400, 400)])
        self.target = self.pos.copy()
        self.hue = random.uniform(180, 320)
        self.energy = 0
        
    def update(self):
        if random.random() < 0.05:
            self.target = np.array([random.uniform(-400, 400), random.uniform(-400, 400), random.uniform(-400, 400)])
            self.energy = 1.0
            
        self.pos += (self.target - self.pos) * 0.2
        self.energy *= 0.9

particles = [QuantumParticle() for _ in range(500)]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw():
    py5.no_stroke()
    py5.fill(5, 5)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    py5.camera(
        py5.width/2 + py5.cos(t) * 1000, py5.height/2 + py5.sin(t*0.5) * 800, 1000,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t)
    
    # draw containment grid
    py5.stroke(200, 80, 50, 10)
    py5.stroke_weight(1)
    py5.no_fill()
    py5.box(800)
    
    py5.stroke_weight(3)
    for p in particles:
        p.update()
        brightness = 50 + p.energy * 50
        py5.stroke(p.hue, 80, brightness, 50)
        
        py5.push_matrix()
        py5.translate(p.pos[0], p.pos[1], p.pos[2])
        if p.energy > 0.1:
            py5.box(10 * p.energy)
        else:
            py5.point(0, 0, 0)
        py5.pop_matrix()
        
        # draw tunneling line
        if p.energy > 0.5:
            py5.stroke(p.hue, 80, brightness, 30)
            py5.line(p.pos[0], p.pos[1], p.pos[2], p.target[0], p.target[1], p.target[2])

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

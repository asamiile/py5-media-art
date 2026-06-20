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

class Chromosome:
    def __init__(self, angle, r):
        # Starts somewhat scattered near equator
        self.x = py5.cos(angle) * r + py5.random(-50, 50)
        self.y = py5.random(-100, 100) # Dist from equator
        self.z = py5.sin(angle) * r + py5.random(-50, 50)
        self.target_y = py5.random(-20, 20) # Moves to metaphase plate
        
    def get_pos(self, t):
        # Evolve over time towards equator
        y = py5.remap(t, 0, 1, self.y, self.target_y)
        return np.array([self.x, y, self.z])

class Microtubule:
    def __init__(self, pole, chromosome):
        self.pole = pole
        self.chromosome = chromosome
        # Waver params
        self.offset = py5.random(100)
        self.speed = py5.random(0.02, 0.05)

    def draw(self, t):
        p1 = self.pole
        p2 = self.chromosome.get_pos(t)
        
        # We'll draw a bezier curve instead of a straight line to simulate bending under tension
        dist = np.linalg.norm(p2 - p1)
        
        # Control points pulled outward by noise
        mid = (p1 + p2) / 2
        noise_vec = np.array([
            py5.os_noise(mid[0] * 0.01, t * self.speed + self.offset),
            py5.os_noise(mid[1] * 0.01, t * self.speed + self.offset + 100),
            py5.os_noise(mid[2] * 0.01, t * self.speed + self.offset + 200)
        ]) * 2 - 1
        
        cp = mid + noise_vec * (dist * 0.3)
        
        py5.no_fill()
        # Green microtubules
        py5.stroke(120, 80, 100, 60)
        py5.stroke_weight(2)
        
        py5.begin_shape()
        py5.vertex(*p1)
        py5.quadratic_vertex(*cp, *p2)
        py5.end_shape()

chromosomes = []
microtubules = []
pole1 = np.array([0, -400, 0])
pole2 = np.array([0, 400, 0])

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(150):
        c = Chromosome(py5.random(py5.TWO_PI), py5.random(50, 300))
        chromosomes.append(c)
        # Connect to both poles
        microtubules.append(Microtubule(pole1, c))
        microtubules.append(Microtubule(pole2, c))

def draw():
    py5.background(0, 0, 5) # Dark void
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.translate(py5.width/2, py5.height/2, -400)
    
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Draw poles (centrosomes)
    py5.no_stroke()
    py5.fill(60, 80, 100, 80) # Yellowish centers
    
    py5.push_matrix()
    py5.translate(*pole1)
    py5.sphere_detail(10)
    py5.sphere(20)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(*pole2)
    py5.sphere(20)
    py5.pop_matrix()
    
    # Draw Microtubules
    for mt in microtubules:
        mt.draw(t)
        
    # Draw Chromosomes
    for c in chromosomes:
        pos = c.get_pos(t)
        py5.push_matrix()
        py5.translate(*pos)
        py5.fill(280, 80, 100, 90) # Purple chromosomes
        
        # Simple X shape
        py5.rotate_z(py5.sin(t * py5.TWO_PI + c.x) * py5.PI)
        py5.box(10, 30, 10)
        py5.rotate_z(py5.PI/2)
        py5.box(10, 30, 10)
        
        py5.pop_matrix()

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

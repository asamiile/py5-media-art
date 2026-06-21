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

# The central vacuole
class Vacuole:
    def __init__(self):
        self.x = py5.width / 2
        self.y = py5.height / 2
        self.radius = 150.0
        self.nodes = []
        num_nodes = 40
        for i in range(num_nodes):
            ang = py5.TWO_PI * i / num_nodes
            self.nodes.append([
                self.x + py5.cos(ang) * self.radius,
                self.y + py5.sin(ang) * self.radius
            ])

    def update(self, t):
        # Move center slightly
        self.x = py5.width / 2 + py5.cos(t * 0.5) * 100
        self.y = py5.height / 2 + py5.sin(t * 0.3) * 100
        
        # Deform boundary nodes
        num_nodes = len(self.nodes)
        for i in range(num_nodes):
            ang = py5.TWO_PI * i / num_nodes
            noise_val = py5.os_noise(self.x * 0.01 + py5.cos(ang), self.y * 0.01 + py5.sin(ang), t)
            rad = self.radius + py5.remap(noise_val, 0, 1, -50, 50)
            self.nodes[i][0] = self.x + py5.cos(ang) * rad
            self.nodes[i][1] = self.y + py5.sin(ang) * rad

    def draw(self):
        py5.fill(280, 80, 30, 80) # deep purple body
        py5.stroke(280, 90, 80, 100)
        py5.stroke_weight(4)
        
        py5.begin_shape()
        for node in self.nodes:
            py5.curve_vertex(node[0], node[1])
        # close the loop smoothly
        for i in range(3):
            py5.curve_vertex(self.nodes[i][0], self.nodes[i][1])
        py5.end_shape()

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = py5.random(-1, 1)
        self.vy = py5.random(-1, 1)
        self.size = py5.random(5, 15)
        self.hue = py5.random(60, 120) # yellow-green organelle
        self.digested = False
        self.alpha = 100

    def update(self, v_x, v_y, v_rad):
        if self.digested:
            self.alpha -= 2
            self.size *= 0.95
            return
            
        dx = v_x - self.x
        dy = v_y - self.y
        dist = py5.dist(self.x, self.y, v_x, v_y)
        
        # Pull towards vacuole
        if dist < v_rad * 3:
            force = 10.0 / (dist + 1)
            self.vx += dx * force * 0.001
            self.vy += dy * force * 0.001
            
        # Add friction
        self.vx *= 0.98
        self.vy *= 0.98
        
        self.x += self.vx + py5.random(-2, 2)
        self.y += self.vy + py5.random(-2, 2)
        
        if dist < v_rad * 0.8:
            self.digested = True

    def draw(self):
        if self.alpha > 0:
            py5.fill(self.hue, 80, 100, self.alpha)
            py5.no_stroke()
            py5.circle(self.x, self.y, self.size)

vacuole = None
particles = []

def setup():
    global vacuole
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    vacuole = Vacuole()
    
    for _ in range(300):
        # Spawn outside
        ang = py5.random(py5.TWO_PI)
        r = py5.random(400, 1000)
        particles.append(Particle(py5.width/2 + py5.cos(ang)*r, py5.height/2 + py5.sin(ang)*r))

def draw():
    py5.background(10, 10, 15, 40) # trails
    
    t = py5.frame_count * 0.02
    
    vacuole.update(t)
    
    # Sort particles so undigested are drawn first, or blend
    py5.blend_mode(py5.ADD)
    for p in particles:
        p.update(vacuole.x, vacuole.y, vacuole.radius)
        p.draw()
        
    py5.blend_mode(py5.BLEND)
    vacuole.draw()

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

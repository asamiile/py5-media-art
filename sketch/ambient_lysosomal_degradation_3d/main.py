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

class Debris:
    def __init__(self, t_offset):
        self.t_offset = t_offset
        self.points = []
        # Create a geometric structure (like a damaged protein or organelle)
        for _ in range(40):
            self.points.append(np.array([py5.random(-50, 50), py5.random(-50, 50), py5.random(-50, 50)]))
            
    def draw(self, t):
        # Progress through the lysosome
        progress = (t * 2 + self.t_offset) % 1.0
        y_pos = py5.remap(progress, 0, 1, -500, 500)
        
        # When inside the lysosome (y near 0), it breaks apart
        breakdown = 1.0 - max(0, min(1.0, 1.0 - abs(y_pos) / 200.0))
        
        py5.push_matrix()
        py5.translate(py5.sin(progress * py5.TWO_PI) * 100, y_pos, py5.cos(progress * py5.TWO_PI) * 100)
        py5.rotate_x(progress * py5.TWO_PI * 2)
        py5.rotate_y(progress * py5.TWO_PI * 3)
        
        py5.stroke(200, 40, 80, 80 * breakdown)
        py5.stroke_weight(2)
        py5.no_fill()
        
        # If breaking down, scatter points
        py5.begin_shape(py5.LINES)
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            
            scatter = (1.0 - breakdown) * 100
            s_p1 = p1 + np.array([py5.random(-scatter, scatter), py5.random(-scatter, scatter), py5.random(-scatter, scatter)])
            s_p2 = p2 + np.array([py5.random(-scatter, scatter), py5.random(-scatter, scatter), py5.random(-scatter, scatter)])
            
            py5.vertex(*s_p1)
            py5.vertex(*s_p2)
        py5.end_shape()
        
        # Draw glowing recovered amino acids when fully broken down
        if breakdown < 0.2:
            py5.no_stroke()
            py5.fill(60, 80, 100, 80)
            for p in self.points:
                s_p = p + np.array([py5.random(-150, 150), py5.random(-150, 150), py5.random(-150, 150)])
                py5.push_matrix()
                py5.translate(*s_p)
                py5.sphere_detail(3)
                py5.sphere(3)
                py5.pop_matrix()
        
        py5.pop_matrix()

class Enzyme:
    def __init__(self):
        self.r = py5.random(100, 280)
        self.theta = py5.random(py5.TWO_PI)
        self.phi = py5.random(py5.PI)
        self.speed = py5.random(0.01, 0.05)
        
    def draw(self, t):
        angle1 = self.theta + t * py5.TWO_PI * self.speed * 10
        angle2 = self.phi + t * py5.TWO_PI * self.speed * 5
        
        x = self.r * py5.sin(angle2) * py5.cos(angle1)
        y = self.r * py5.sin(angle2) * py5.sin(angle1)
        z = self.r * py5.cos(angle2)
        
        # Jitter
        x += py5.random(-10, 10)
        y += py5.random(-10, 10)
        z += py5.random(-10, 10)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.fill(320, 80, 100, 60) # Pinkish acidic enzymes
        py5.no_stroke()
        py5.sphere_detail(4)
        py5.sphere(6)
        py5.pop_matrix()

debris_list = []
enzymes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(5):
        debris_list.append(Debris(i * 0.2))
        
    for _ in range(300):
        enzymes.append(Enzyme())

def draw():
    py5.background(20, 90, 10) # Dark organic interior
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.translate(py5.width/2, py5.height/2, -300)
    
    py5.rotate_y(t * py5.TWO_PI * 0.2)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.1)
    
    py5.blend_mode(py5.ADD)
    
    # Draw Lysosome membrane
    py5.no_fill()
    py5.stroke(180, 80, 80, 20)
    py5.stroke_weight(1)
    py5.sphere_detail(20)
    py5.sphere(300)
    
    # Draw acidic interior environment
    py5.fill(300, 80, 80, 5)
    py5.no_stroke()
    py5.sphere(280)
    
    # Draw Enzymes
    for e in enzymes:
        e.draw(t)
        
    # Draw Debris breaking down
    for d in debris_list:
        d.draw(t)

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

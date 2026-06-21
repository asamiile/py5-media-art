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

class Node:
    def __init__(self, i, total):
        self.i = i
        self.total = total
        # Base parametric position
        self.base_ang = py5.remap(i, 0, total, 0, py5.TWO_PI * 10)
        self.r = 200 + py5.sin(self.base_ang * 0.5) * 50
        
        self.x = self.r * py5.cos(self.base_ang)
        self.y = self.r * py5.sin(self.base_ang)
        self.z = py5.remap(i, 0, total, -300, 300)
        
    def get_pos(self, t):
        # Time varying folding noise
        nx = py5.os_noise(self.x * 0.002, self.y * 0.002, t * 0.05)
        ny = py5.os_noise(self.y * 0.002, self.z * 0.002 + 100, t * 0.05)
        nz = py5.os_noise(self.z * 0.002, self.x * 0.002 + 200, t * 0.05)
        
        # Folding displacement
        disp = 200 * py5.sin(t * py5.PI + self.i * 0.01) # Pulsing folding
        
        fx = self.x + py5.remap(nx, 0, 1, -disp, disp)
        fy = self.y + py5.remap(ny, 0, 1, -disp, disp)
        fz = self.z + py5.remap(nz, 0, 1, -disp, disp)
        
        return fx, fy, fz

nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for i in range(1000):
        nodes.append(Node(i, 1000))

def draw():
    py5.background(0, 0, 5) # Dark space
    
    t = py5.frame_count / float(TOTAL_FRAMES) # 0 to 1 over 10 seconds
    
    py5.translate(py5.width/2, py5.height/2, -200)
    
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw the chromatin fiber
    py5.begin_shape()
    for i, node in enumerate(nodes):
        x, y, z = node.get_pos(t)
        
        # Color based on position in chain and folding state
        hue = (150 + py5.sin(i * 0.01 + t * py5.TWO_PI) * 50) % 360 # Cyans and greens
        py5.stroke(hue, 80, 100, 60)
        
        py5.vertex(x, y, z)
        
        # Occasionally draw a "histone" or nucleosome
        if i % 50 == 0:
            py5.push_matrix()
            py5.translate(x, y, z)
            py5.no_stroke()
            py5.fill(hue, 90, 100, 80)
            py5.sphere_detail(5)
            py5.sphere(8)
            py5.pop_matrix()
            
            # Reset stroke for path
            py5.no_fill()
            
    py5.end_shape()

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

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

class Branch:
    def __init__(self, x, y, angle, thickness, generation):
        self.x = x
        self.y = y
        self.angle = angle
        self.thickness = thickness
        self.generation = generation
        self.active = True
        self.length = 0
        self.max_length = py5.random(10, 50) * (0.9 ** generation)
        
    def update_and_draw(self):
        if not self.active:
            return []
            
        step = 2.0
        nx = self.x + py5.cos(self.angle) * step
        ny = self.y + py5.sin(self.angle) * step
        
        py5.stroke(40, py5.remap(self.generation, 0, 10, 10, 60), 100, 80)
        py5.stroke_weight(self.thickness)
        py5.line(self.x, self.y, nx, ny)
        
        self.x = nx
        self.y = ny
        self.length += step
        
        # Wander slightly
        self.angle += py5.random(-0.1, 0.1)
        
        new_branches = []
        if self.length >= self.max_length:
            self.active = False
            # Branch out
            if self.generation < 15 and py5.random(1) < 0.9:
                num_new = int(py5.random(1, 4))
                for _ in range(num_new):
                    new_angle = self.angle + py5.random(-py5.PI/4, py5.PI/4)
                    new_thick = self.thickness * 0.8
                    new_branches.append(Branch(self.x, self.y, new_angle, new_thick, self.generation + 1))
                    
        return new_branches

branches = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(20, 40, 10) # Dark earthy brown
    
    # Start from center
    for _ in range(5):
        branches.append(Branch(py5.width/2, py5.height/2, py5.random(py5.TWO_PI), 5.0, 0))

def draw():
    # We do NOT clear the background, we just draw progressively
    new_b = []
    
    # Process only a subset of active branches each frame to slow it down 
    # and spread the growth over 10 seconds.
    # Actually, we can process all active ones, but they grow slowly.
    for b in branches:
        if b.active:
            new_b.extend(b.update_and_draw())
            
    branches.extend(new_b)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} | Active Branches: {sum(1 for b in branches if b.active)}")

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

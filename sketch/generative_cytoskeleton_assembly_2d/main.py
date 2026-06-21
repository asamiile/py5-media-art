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

class Filament:
    def __init__(self):
        self.x = py5.random(py5.width)
        self.y = py5.random(py5.height)
        self.length = py5.random(10, 50)
        self.hue = py5.random(100, 160) # Greens (Microtubules)
        if py5.random(1) < 0.3:
            self.hue = py5.random(0, 40) # Reds (Actin)
        self.thickness = py5.random(1, 4)
        
    def draw(self, t):
        # Flow field angle
        angle = py5.os_noise(self.x * 0.005, self.y * 0.005, t * 0.5) * py5.TWO_PI * 2
        
        # Determine polymerization/depolymerization based on a different noise field
        poly = py5.os_noise(self.x * 0.01, self.y * 0.01, t + 100)
        
        current_len = py5.remap(poly, 0.2, 0.8, 0, self.length)
        current_len = max(0, current_len)
        
        if current_len > 0:
            py5.push_matrix()
            py5.translate(self.x, self.y)
            py5.rotate(angle)
            
            py5.stroke(self.hue, 80, 100, 60)
            py5.stroke_weight(self.thickness)
            
            # Assembly line
            py5.line(-current_len/2, 0, current_len/2, 0)
            py5.pop_matrix()
            
            # Slowly drift with flow
            self.x += py5.cos(angle) * 0.5
            self.y += py5.sin(angle) * 0.5
            
            # Wrap
            self.x = self.x % py5.width
            self.y = self.y % py5.height

filaments = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for _ in range(8000):
        filaments.append(Filament())

def draw():
    # Use translucent background to leave slight trails of the assembly
    py5.fill(10, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.02
    
    py5.blend_mode(py5.ADD)
    for f in filaments:
        f.draw(t)
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

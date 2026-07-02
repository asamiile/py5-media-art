from pathlib import Path
import shutil
import subprocess
import sys
import random
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

NUM_JELLIES = 80
jellies = []

class Jelly:
    def __init__(self, idx):
        self.idx = idx
        self.x = random.uniform(0, py5.width)
        self.y = random.uniform(py5.height, py5.height + 1000)
        self.size = random.uniform(50, 150)
        self.speed = random.uniform(2, 6)
        self.hue = random.uniform(160, 220)  # Deep sea blues and cyans
        self.num_tentacles = int(random.uniform(5, 12))
        self.phase_offset = random.uniform(0, py5.TWO_PI)
        
    def update(self, t):
        # Pulse movement
        pulse = py5.sin(t * 10 + self.phase_offset)
        self.y -= self.speed * (1.0 + pulse * 0.5)
        self.x += py5.os_noise(self.idx, t * 2) * 4.0 - 2.0
        
        # Screen wrap
        if self.y < -300:
            self.y = py5.height + 300
            self.x = random.uniform(0, py5.width)
            
    def draw(self, t):
        pulse = py5.sin(t * 10 + self.phase_offset)
        
        py5.push_matrix()
        py5.translate(self.x, self.y)
        
        # Draw bell
        py5.no_stroke()
        bell_width = self.size * (1.0 + pulse * 0.2)
        bell_height = self.size * 0.8 * (1.0 - pulse * 0.1)
        
        py5.fill(self.hue, 80, 100, 30)
        py5.arc(0, 0, bell_width, bell_height, py5.PI, py5.TWO_PI)
        
        py5.fill(self.hue, 60, 100, 60)
        py5.arc(0, 0, bell_width * 0.6, bell_height * 0.6, py5.PI, py5.TWO_PI)
        
        # Draw tentacles
        py5.no_fill()
        py5.stroke(self.hue, 70, 100, 40)
        py5.stroke_weight(self.size * 0.05)
        
        for i in range(self.num_tentacles):
            tx = py5.remap(i, 0, self.num_tentacles - 1, -bell_width/2, bell_width/2)
            
            py5.begin_shape()
            for j in range(10):
                seg_y = j * self.size * 0.4
                noise_val = py5.os_noise(self.idx * 10 + i, j * 0.1, t * 5)
                seg_x = tx + (noise_val - 0.5) * self.size * j * 0.1
                
                # Tentacles contract during pulse
                seg_y *= (1.0 - pulse * 0.1)
                
                py5.curve_vertex(seg_x, seg_y)
            py5.end_shape()
            
        py5.pop_matrix()

def setup():
    global jellies
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 10, 20)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for i in range(NUM_JELLIES):
        jellies.append(Jelly(i))
        
    # Pre-warm
    for _ in range(500):
        for j in jellies:
            j.update(_ / float(TOTAL_FRAMES))

def draw():
    # Motion blur / deep sea murkiness
    py5.blend_mode(py5.BLEND)
    py5.fill(220, 80, 5, 20) # Very dark navy blue
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Sort jellies by size to simulate depth (smaller ones drawn first, in back)
    jellies.sort(key=lambda j: j.size)
    
    for j in jellies:
        j.update(t)
        j.draw(t)

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
        
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

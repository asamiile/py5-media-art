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

NUM_CRYSTALS = 300

class Crystal:
    def __init__(self):
        self.rot_x = random.uniform(0, py5.TWO_PI)
        self.rot_y = random.uniform(0, py5.TWO_PI)
        self.length = random.uniform(100, 600)
        self.width = random.uniform(10, 50)
        self.hue = random.uniform(200, 300)
        self.growth_offset = random.uniform(0, 100)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    global crystals
    crystals = [Crystal() for _ in range(NUM_CRYSTALS)]

def draw_crystal(c, t):
    growth = py5.os_noise(c.growth_offset, t * 0.5)
    current_length = c.length * (0.2 + growth * 0.8)
    
    py5.push_matrix()
    py5.rotate_x(c.rot_x + py5.sin(t*0.5 + c.growth_offset)*0.1)
    py5.rotate_y(c.rot_y + py5.cos(t*0.5 + c.growth_offset)*0.1)
    
    py5.fill(c.hue, 80, 80, 40)
    py5.stroke(c.hue, 100, 100, 80)
    py5.stroke_weight(2)
    
    # Draw pyramid
    py5.begin_shape(py5.TRIANGLES)
    
    # Base
    hw = c.width / 2
    py5.vertex(-hw, -hw, 0)
    py5.vertex( hw, -hw, 0)
    py5.vertex( 0, 0, current_length)
    
    py5.vertex( hw, -hw, 0)
    py5.vertex( hw,  hw, 0)
    py5.vertex( 0, 0, current_length)
    
    py5.vertex( hw,  hw, 0)
    py5.vertex(-hw,  hw, 0)
    py5.vertex( 0, 0, current_length)
    
    py5.vertex(-hw,  hw, 0)
    py5.vertex(-hw, -hw, 0)
    py5.vertex( 0, 0, current_length)
    
    py5.end_shape()
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.camera(
        py5.width/2 + py5.cos(t) * 1000, py5.height/2 - 400, py5.height/2 + py5.sin(t) * 1000,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.5)
    
    for c in crystals:
        draw_crystal(c, t)

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

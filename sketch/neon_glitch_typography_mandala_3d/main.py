from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os
import string

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

RINGS = 8
chars = list(string.ascii_uppercase + string.digits + "!@#$%^&*()")

class Ring:
    def __init__(self, idx):
        self.radius = 100 + idx * 80
        self.count = 8 + idx * 12
        self.speed = (0.01 + np.random.rand()*0.02) * (1 if idx % 2 == 0 else -1)
        self.letters = [np.random.choice(chars) for _ in range(self.count)]

rings = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global rings
    py5.text_font(py5.create_font("Courier", 32))
    py5.text_align(py5.CENTER, py5.CENTER)
    
    for i in range(RINGS):
        rings.append(Ring(i))

def draw():
    py5.background(0) # Pitch black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(py5.PI/4) # Tilt down slightly
    
    py5.blend_mode(py5.ADD)
    
    # Global mandala rotation
    py5.rotate_z(t * 0.1)
    
    for r_idx, r in enumerate(rings):
        # Is this ring glitching?
        glitching = py5.os_noise(r_idx, t*2, 0) > 0.7
        
        py5.push_matrix()
        py5.rotate_z(t * r.speed * 60)
        
        angle_step = py5.TWO_PI / r.count
        
        for i in range(r.count):
            py5.push_matrix()
            
            angle = i * angle_step
            py5.rotate_z(angle)
            
            # Position outwards
            z_glitch = 0
            if glitching:
                z_glitch = np.random.randn() * 100
                
            py5.translate(r.radius, 0, z_glitch)
            
            # Stand letters up so they face camera roughly
            py5.rotate_y(-py5.PI/2)
            py5.rotate_x(py5.PI/2)
            
            if glitching:
                char_to_draw = np.random.choice(chars)
                py5.fill(0, 0, 100, 90) # Pure white
            else:
                char_to_draw = r.letters[i]
                if r_idx % 2 == 0:
                    py5.fill(120, 100, 100, 80) # Acid green
                else:
                    py5.fill(280, 100, 80, 80)  # Deep violet
                    
            py5.text(char_to_draw, 0, 0)
            
            py5.pop_matrix()
            
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        os._exit(0)

py5.run_sketch()

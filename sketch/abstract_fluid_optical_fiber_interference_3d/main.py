from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random
import math

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

NUM_STRANDS = 120
STRAND_LENGTH = 3000
SEGMENTS = 50

class Strand:
    def __init__(self, idx):
        self.idx = idx
        self.angle = random.uniform(0, py5.PI * 2)
        self.radius = random.uniform(100, 800)
        self.hue_base = random.choice([200, 240, 280, 160])
        
    def draw(self, t):
        py5.stroke_weight(random.uniform(2, 6))
        py5.no_fill()
        
        py5.begin_shape()
        for i in range(SEGMENTS + 1):
            z = py5.remap(i, 0, SEGMENTS, -STRAND_LENGTH/2, STRAND_LENGTH/2)
            
            # Add noise to make them twist
            noise_val = py5.os_noise(self.idx * 0.1, z * 0.001, t * 0.02)
            noise_angle = noise_val * py5.PI
            
            x = (self.radius + noise_val * 200) * py5.cos(self.angle + noise_angle + z * 0.001)
            y = (self.radius + noise_val * 200) * py5.sin(self.angle + noise_angle + z * 0.001)
            
            # Interference pulse
            pulse = py5.sin(z * 0.01 - t * 0.1 + self.idx)
            bri = py5.remap(pulse, -1, 1, 40, 100)
            alpha = py5.remap(pulse, -1, 1, 100, 255)
            hue = (self.hue_base + pulse * 20) % 360
            
            py5.stroke(hue, 80, bri, alpha)
            
            # Using point instead of vertex so color can change per segment,
            # wait, vertex color requires py5.stroke to be applied? 
            # In P3D, setting stroke before vertex sets the color for that vertex!
            py5.vertex(x, y, z)
            
        py5.end_shape()

strands = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for i in range(NUM_STRANDS):
        strands.append(Strand(i))

def draw():
    py5.background(0)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    t = py5.frame_count
    
    # Move camera through the strands
    cam_z = (t * 15) % (STRAND_LENGTH / 2)
    py5.translate(0, 0, cam_z)
    
    # Slight rotation of camera
    py5.rotate_z(t * 0.002)
    
    for strand in strands:
        strand.draw(t)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

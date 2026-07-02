from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_RIBBONS = 400
HISTORY_LEN = 30
ribbons = []

class Ribbon:
    def __init__(self):
        self.pos = np.random.uniform(-400, 400, 3)
        self.history = [self.pos.copy() for _ in range(HISTORY_LEN)]
        self.normals = [np.array([0., 1., 0.]) for _ in range(HISTORY_LEN)]
        
        # Color gradient based on initial position
        self.hue_offset = np.random.uniform(0, 1)
        
    def update(self, t):
        # Calculate velocity from 3D noise
        scale = 0.005
        vx = py5.os_noise(self.pos[0]*scale, self.pos[1]*scale, self.pos[2]*scale + t) - 0.5
        vy = py5.os_noise(self.pos[0]*scale + 100, self.pos[1]*scale, self.pos[2]*scale + t) - 0.5
        vz = py5.os_noise(self.pos[0]*scale, self.pos[1]*scale + 100, self.pos[2]*scale + t) - 0.5
        
        vel = np.array([vx, vy, vz]) * 20.0
        
        # Calculate a normal vector for the ribbon (curl approximation)
        nx = py5.os_noise(self.pos[0]*scale, self.pos[1]*scale, self.pos[2]*scale - t) - 0.5
        ny = py5.os_noise(self.pos[0]*scale - 100, self.pos[1]*scale, self.pos[2]*scale - t) - 0.5
        nz = py5.os_noise(self.pos[0]*scale, self.pos[1]*scale - 100, self.pos[2]*scale - t) - 0.5
        
        normal = np.array([nx, ny, nz])
        normal = normal / (np.linalg.norm(normal) + 1e-5)
        
        self.pos += vel
        
        # Boundary wrap
        limit = 600
        for i in range(3):
            if self.pos[i] > limit: self.pos[i] -= limit*2
            if self.pos[i] < -limit: self.pos[i] += limit*2
            
        # Update history
        self.history.pop(0)
        self.history.append(self.pos.copy())
        
        self.normals.pop(0)
        self.normals.append(normal)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
    for _ in range(NUM_RIBBONS):
        ribbons.append(Ribbon())
        
def draw():
    py5.background(5, 10, 25) # Deep Navy
    
    py5.ambient_light(80, 80, 100)
    py5.directional_light(0, 255, 255, 1, 1, -1) # Aqua
    py5.directional_light(255, 0, 255, -1, -1, 1) # Purple
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Global camera rotation
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002)
    
    t = py5.frame_count * 0.015
    
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    ribbon_width = 10.0
    
    for r in ribbons:
        r.update(t)
        
        py5.begin_shape(py5.QUAD_STRIP)
        
        # Determine color based on ribbon
        if r.hue_offset < 0.6:
            py5.fill(0, 200, 255, 100) # Aqua / Teal
        elif r.hue_offset < 0.9:
            py5.fill(138, 43, 226, 100) # Electric Purple
        else:
            py5.fill(255, 127, 80, 150) # Luminous Coral
            
        for i in range(HISTORY_LEN):
            p = r.history[i]
            n = r.normals[i]
            
            # Width fades out at the tail
            w = ribbon_width * (i / HISTORY_LEN)
            
            p1 = p + n * w
            p2 = p - n * w
            
            py5.vertex(p1[0], p1[1], p1[2])
            py5.vertex(p2[0], p2[1], p2[2])
            
        py5.end_shape()

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
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
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

grid_size = 40
spacing = 60
buildings = []
traffic = []

class Building:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.h = py5.noise(x * 0.01, z * 0.01) * 600 + random.uniform(50, 150)
        self.w = random.uniform(20, 50)
        self.d = random.uniform(20, 50)
        self.hue = random.choice([180, 300, 60]) # Cyan, Magenta, Yellow
        
class Vehicle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.z = random.uniform(-grid_size * spacing / 2, grid_size * spacing / 2)
        self.x = random.uniform(-grid_size * spacing / 2, grid_size * spacing / 2)
        self.y = random.uniform(-10, 200) # Flying height
        self.speed = random.uniform(5, 15)
        self.axis = random.choice(['x', 'z'])
        self.dir = random.choice([-1, 1])
        self.hue = random.choice([180, 300])

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    offset = grid_size * spacing / 2
    for ix in range(grid_size):
        for iz in range(grid_size):
            if random.random() > 0.3: # Leave some gaps for roads
                x = ix * spacing - offset
                z = iz * spacing - offset
                buildings.append(Building(x, z))
                
    for _ in range(500):
        traffic.append(Vehicle())

def draw():
    py5.background(10, 100, 5) # Dark abyss
    
    # Camera flight
    cam_x = py5.frame_count * 5
    cam_z = py5.frame_count * 2
    
    # Wrap camera to keep it inside the city
    wrap_limit = grid_size * spacing / 2
    cx = (cam_x + wrap_limit) % (wrap_limit * 2) - wrap_limit
    cz = (cam_z + wrap_limit) % (wrap_limit * 2) - wrap_limit
    
    py5.camera(cx, -400, cz + 600,  # Eye
               cx + 100, 0, cz - 100,     # Target
               0, 1, 0)             # Up
               
    py5.blend_mode(py5.ADD)
    
    # Draw buildings
    py5.stroke(200, 50, 20, 100)
    py5.stroke_weight(1)
    
    for b in buildings:
        # Distance fade
        d = math.sqrt((b.x - cx)**2 + (b.z - cz)**2)
        if d > 1500: continue
        
        alpha = py5.remap(d, 500, 1500, 200, 0)
        
        py5.push_matrix()
        py5.translate(b.x, -b.h / 2, b.z)
        py5.fill(b.hue, 80, 50, alpha * 0.3)
        py5.stroke(b.hue, 90, 80, alpha)
        py5.box(b.w, b.h, b.d)
        py5.pop_matrix()
        
    # Draw traffic
    py5.no_stroke()
    for v in traffic:
        if v.axis == 'x':
            v.x += v.speed * v.dir
            if v.x > wrap_limit: v.x = -wrap_limit
            if v.x < -wrap_limit: v.x = wrap_limit
        else:
            v.z += v.speed * v.dir
            if v.z > wrap_limit: v.z = -wrap_limit
            if v.z < -wrap_limit: v.z = wrap_limit
            
        d = math.sqrt((v.x - cx)**2 + (v.z - cz)**2)
        if d > 1500: continue
        
        alpha = py5.remap(d, 500, 1500, 255, 0)
        
        py5.push_matrix()
        py5.translate(v.x, -v.y, v.z)
        py5.fill(v.hue, 100, 100, alpha)
        # stretch based on speed
        if v.axis == 'x':
            py5.box(v.speed * 2, 3, 3)
        else:
            py5.box(3, 3, v.speed * 2)
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

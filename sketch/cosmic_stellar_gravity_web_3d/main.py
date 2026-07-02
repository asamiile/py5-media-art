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

class Star:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.ox = x
        self.oy = y
        self.oz = z
        self.hue = random.choice([200, 280, 0]) # Cyan, Purple, White

stars = []
grid_size = 20
spacing = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    offset = grid_size * spacing / 2
    for ix in range(grid_size):
        for iy in range(grid_size):
            for iz in range(grid_size):
                if random.random() > 0.8: # Sparse
                    x = ix * spacing - offset
                    y = iy * spacing - offset
                    z = iz * spacing - offset
                    stars.append(Star(x, y, z))

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.blend_mode(py5.ADD)
    
    # Pulsating gravity wells
    time_factor = py5.frame_count * 0.05
    well1_x = math.sin(time_factor) * 300
    well1_y = math.cos(time_factor * 1.3) * 300
    well1_z = math.sin(time_factor * 0.8) * 300
    
    well2_x = math.cos(time_factor * 1.1) * 300
    well2_y = math.sin(time_factor * 0.9) * 300
    well2_z = math.cos(time_factor * 1.5) * 300
    
    py5.stroke_weight(2)
    
    for s in stars:
        # Calculate pull from wells
        d1 = math.sqrt((s.ox - well1_x)**2 + (s.oy - well1_y)**2 + (s.oz - well1_z)**2)
        d2 = math.sqrt((s.ox - well2_x)**2 + (s.oy - well2_y)**2 + (s.oz - well2_z)**2)
        
        pull1 = 5000 / (d1 + 10)
        pull2 = 5000 / (d2 + 10)
        
        dx1 = (well1_x - s.ox) / (d1 + 1) * pull1
        dy1 = (well1_y - s.oy) / (d1 + 1) * pull1
        dz1 = (well1_z - s.oz) / (d1 + 1) * pull1
        
        dx2 = (well2_x - s.ox) / (d2 + 1) * pull2
        dy2 = (well2_y - s.oy) / (d2 + 1) * pull2
        dz2 = (well2_z - s.oz) / (d2 + 1) * pull2
        
        s.x = s.ox + dx1 + dx2
        s.y = s.oy + dy1 + dy2
        s.z = s.oz + dz1 + dz2
        
        # Color based on displacement
        disp = math.sqrt((s.x - s.ox)**2 + (s.y - s.oy)**2 + (s.z - s.oz)**2)
        alpha = py5.remap(disp, 0, 100, 50, 255)
        
        sat = 100 if s.hue != 0 else 0
        py5.stroke(s.hue, sat, 100, alpha)
        
        py5.push_matrix()
        py5.translate(s.x, s.y, s.z)
        py5.point(0, 0, 0)
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

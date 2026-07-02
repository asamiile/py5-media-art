from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import Voronoi
import random

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

NUM_POINTS = 150

class Seed:
    def __init__(self):
        self.x = random.uniform(-100, SIZE[0] + 100)
        self.y = random.uniform(-100, SIZE[1] + 100)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.hue_base = random.choice([200, 260, 320, 40, 160])
        self.sat = random.uniform(50, 100)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # Bounce off walls loosely
        if self.x < -200 or self.x > SIZE[0] + 200:
            self.vx *= -1
        if self.y < -200 or self.y > SIZE[1] + 200:
            self.vy *= -1

seeds = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Add seeds, plus some static seeds far outside to bound the voronoi regions
    for _ in range(NUM_POINTS):
        seeds.append(Seed())
        
    # Bounding points
    bounds = [
        (-1000, -1000), (SIZE[0]+1000, -1000), 
        (-1000, SIZE[1]+1000), (SIZE[0]+1000, SIZE[1]+1000)
    ]
    for bx, by in bounds:
        s = Seed()
        s.x = bx
        s.y = by
        s.vx = 0
        s.vy = 0
        seeds.append(s)

def draw():
    py5.background(10)
    
    # Gather points
    points = np.array([[s.x, s.y] for s in seeds])
    
    # Compute Voronoi
    try:
        vor = Voronoi(points)
    except Exception:
        # Ignore QHull errors if points become colinear
        return
        
    py5.stroke(0, 0, 100, 100) # Bright white lines for shattered glass effect
    py5.stroke_weight(4)
    
    time_val = py5.frame_count * 0.05
    
    # Draw regions
    for point_idx, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        
        if not region or -1 in region:
            continue
            
        polygon = [vor.vertices[i] for i in region]
        
        # Calculate centroid to pulse brightness
        cx = np.mean([p[0] for p in polygon])
        cy = np.mean([p[1] for p in polygon])
        
        seed = seeds[point_idx]
        
        # Color pulsing
        dist_center = np.hypot(cx - SIZE[0]/2, cy - SIZE[1]/2)
        pulse = py5.sin(dist_center * 0.005 - time_val)
        bri = py5.remap(pulse, -1, 1, 40, 100)
        
        hue = (seed.hue_base + pulse * 20) % 360
        
        py5.fill(hue, seed.sat, bri, 200)
        
        py5.begin_shape()
        for px, py_pos in polygon:
            py5.vertex(px, py_pos)
        py5.end_shape(py5.CLOSE)

    # Update seeds
    for s in seeds:
        s.update()

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

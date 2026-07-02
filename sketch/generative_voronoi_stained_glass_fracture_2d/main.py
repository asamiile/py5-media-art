from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
from scipy.spatial import Voronoi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_SEEDS = 150
seeds = []

class Seed:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hue_offset = random.uniform(0, 360)
        self.noise_offset_x = random.uniform(0, 1000)
        self.noise_offset_y = random.uniform(0, 1000)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize seeds
    for _ in range(NUM_SEEDS):
        seeds.append(Seed(random.uniform(0, SIZE[0]), random.uniform(0, SIZE[1])))

def draw():
    py5.background(0)
    
    time_t = py5.frame_count * 0.005
    
    # Update seed positions using noise
    points = []
    for s in seeds:
        nx = py5.os_noise(s.noise_offset_x, time_t)
        ny = py5.os_noise(s.noise_offset_y, time_t)
        # Drift gently
        s.x += (nx - 0.5) * 4
        s.y += (ny - 0.5) * 4
        
        # Keep within bounds by wrapping
        s.x = s.x % py5.width
        s.y = s.y % py5.height
        
        points.append([s.x, s.y])
        
    # Add dummy points far outside to ensure bounded regions for the visible cells
    margin = 2000
    points.extend([
        [-margin, -margin], [py5.width + margin, -margin],
        [-margin, py5.height + margin], [py5.width + margin, py5.height + margin]
    ])
    
    try:
        vor = Voronoi(points)
    except Exception as e:
        # Occasionally scipy's Voronoi might fail if points are perfectly aligned
        pass
        
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.stroke(0)
    py5.stroke_weight(5) # Thick stained glass leading
    
    for i, region_index in enumerate(vor.point_region[:NUM_SEEDS]):
        region = vor.regions[region_index]
        if not -1 in region and len(region) > 0:
            polygon = [vor.vertices[v] for v in region]
            
            # Draw cell
            py5.begin_shape()
            s = seeds[i]
            # Color shifts slowly
            current_hue = (s.hue_offset + time_t * 50) % 360
            # Calculate distance from center to affect brightness (vignette)
            dist_to_center = np.sqrt((s.x - py5.width/2)**2 + (s.y - py5.height/2)**2)
            brightness = py5.remap(dist_to_center, 0, py5.width/1.5, 100, 20)
            
            py5.fill(current_hue, 90, brightness, 220)
            
            for p in polygon:
                py5.vertex(p[0], p[1])
            py5.end_shape(py5.CLOSE)

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

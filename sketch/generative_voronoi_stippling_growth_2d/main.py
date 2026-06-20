from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.spatial import Delaunay

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

points = []
new_points_per_frame = 5

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(240) # Off-white background
    
    # Initialize with a few seed points in the center
    for _ in range(10):
        points.append([
            py5.width / 2 + py5.random(-100, 100),
            py5.height / 2 + py5.random(-100, 100)
        ])

def draw():
    py5.background(240, 240, 240, 25) # Slight trailing fade
    
    # Add new points near existing ones, favoring empty space
    # Simple simulation of growth:
    for _ in range(new_points_per_frame):
        if len(points) == 0: continue
        # pick a random existing point
        idx = int(py5.random(len(points)))
        p = points[idx]
        
        # random angle and distance
        ang = py5.random(py5.TWO_PI)
        dist = py5.random(20, 80)
        
        new_p = [p[0] + py5.cos(ang) * dist, p[1] + py5.sin(ang) * dist]
        
        # boundary check
        if 0 < new_p[0] < py5.width and 0 < new_p[1] < py5.height:
            points.append(new_p)
            
    # Compute Delaunay
    pts_array = np.array(points)
    if len(pts_array) > 3:
        tri = Delaunay(pts_array)
        
        py5.stroke(20, 50) # Dark grey, low opacity
        py5.stroke_weight(1.5)
        py5.no_fill()
        
        # Render edges
        for simplex in tri.simplices:
            p1 = pts_array[simplex[0]]
            p2 = pts_array[simplex[1]]
            p3 = pts_array[simplex[2]]
            
            # Avoid long edges
            d1 = np.linalg.norm(p1 - p2)
            d2 = np.linalg.norm(p2 - p3)
            d3 = np.linalg.norm(p3 - p1)
            
            if d1 < 150 and d2 < 150 and d3 < 150:
                py5.triangle(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
                
        py5.fill(0)
        py5.no_stroke()
        for p in points:
            py5.circle(p[0], p[1], 4)

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

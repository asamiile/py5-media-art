from pathlib import Path
import shutil
import subprocess
import sys
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

# Voronoi is not natively built into py5 core without some math.
# We will do a pixel-shader-like approach using manhattan distance or euclidean distance to nearest points.
# Since python loops per pixel are slow, we will use a small resolution grid (e.g. 10x10) or numpy vectorized ops.

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    
def draw():
    t = py5.frame_count * 0.02
    
    # Generate point coordinates using numpy for 100 points
    num_points = 100
    points = np.zeros((num_points, 2))
    for i in range(num_points):
        # Parametric paths for points
        px = py5.width/2 + py5.sin(t * 0.5 + i) * (py5.width/2) * py5.os_noise(i, t * 0.1)
        py = py5.height/2 + py5.cos(t * 0.6 + i) * (py5.height/2) * py5.os_noise(i + 100, t * 0.1)
        points[i] = [px, py]
        
    py5.background(0)
    
    res = 12 # Resolution of the "pixels"
    
    # To optimize, we won't do full numpy broadcast for 1920x1080.
    # Instead, we will draw large rects for each cell, using standard python loops.
    # It might be slow, so we keep resolution blocky.
    
    for y in range(0, py5.height, res):
        for x in range(0, py5.width, res):
            # Find closest point
            # We can just iterate or use numpy
            # Let's use simple numpy distance
            diff = points - np.array([x, y])
            dist_sq = diff[:, 0]**2 + diff[:, 1]**2
            min_idx = np.argmin(dist_sq)
            min_dist = np.sqrt(dist_sq[min_idx])
            
            # Use min_idx to get cell properties
            px, py = points[min_idx]
            
            # Reaction diffusion simulated color
            val = py5.os_noise(px * 0.005, py * 0.005, t)
            
            # Edge effect
            # Find second closest to draw borders
            # Sort distances
            dist_sq[min_idx] = np.inf
            second_min_dist = np.sqrt(np.min(dist_sq))
            
            border_dist = second_min_dist - min_dist
            
            if border_dist < 4:
                py5.fill(0, 0, 100) # White border
            else:
                hue = py5.remap(val, 0, 1, 200, 360) % 360
                sat = py5.remap(border_dist, 0, 50, 100, 50)
                bri = py5.remap(min_dist, 0, 200, 100, 20)
                py5.fill(hue, sat, bri)
                
            py5.rect(x, y, res, res)

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

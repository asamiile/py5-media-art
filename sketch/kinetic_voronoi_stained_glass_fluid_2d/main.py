from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.spatial import Voronoi
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
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 600

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global seed_offsets, seed_colors, boundary_points
    
    # Each point gets a unique noise offset for movement
    seed_offsets = np.random.rand(NUM_POINTS, 2) * 1000.0
    
    # Each point gets a vibrant stained-glass color
    hues = np.random.rand(NUM_POINTS)
    sats = np.random.uniform(0.6, 1.0, NUM_POINTS)
    vals = np.random.uniform(0.5, 1.0, NUM_POINTS)
    
    py5.color_mode(py5.HSB, 1.0)
    seed_colors = [py5.color(h, s, v, 0.9) for h, s, v in zip(hues, sats, vals)]
    py5.color_mode(py5.RGB, 255)
    
    # Far-away boundary points to force closed Voronoi regions inside the screen
    M = max(SIZE) * 5
    boundary_points = np.array([
        [-M, -M], [M, -M], [M, M], [-M, M],
        [SIZE[0]/2, -M], [SIZE[0]/2, M], [-M, SIZE[1]/2], [M, SIZE[1]/2]
    ])
    
def draw():
    py5.background(10, 10, 15)
    
    progress = py5.frame_count / TOTAL_FRAMES
    time_val = progress * py5.PI * 2.0
    
    # Generate moving points using Perlin noise
    pts = np.zeros((NUM_POINTS, 2))
    
    for i in range(NUM_POINTS):
        # We want smooth looping movement. 
        # Using 2D noise in a circle in the noise space gives perfect looping.
        nx = seed_offsets[i, 0] + np.cos(time_val) * 0.5
        ny = seed_offsets[i, 0] + np.sin(time_val) * 0.5
        
        px = py5.noise(nx, ny) * py5.width * 1.5 - py5.width * 0.25
        
        nx2 = seed_offsets[i, 1] + np.cos(time_val) * 0.5
        ny2 = seed_offsets[i, 1] + np.sin(time_val) * 0.5
        
        py = py5.noise(nx2, ny2) * py5.height * 1.5 - py5.height * 0.25
        
        pts[i] = [px, py]
        
    # Combine with boundary points
    all_points = np.vstack([pts, boundary_points])
    
    # Compute Voronoi
    vor = Voronoi(all_points)
    
    py5.stroke(0)
    py5.stroke_weight(4.0)
    
    # Draw regions
    for i in range(NUM_POINTS):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        if -1 in region or len(region) == 0:
            continue
            
        py5.fill(seed_colors[i])
        
        polygon = vor.vertices[region]
        
        # Draw the polygon using py5 shape
        py5.begin_shape()
        for x, y in polygon:
            py5.vertex(float(x), float(y))
        py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

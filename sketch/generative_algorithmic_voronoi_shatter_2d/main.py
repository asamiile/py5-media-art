from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 300
points = np.zeros((NUM_POINTS, 2), dtype=np.float32)
noise_offsets = np.zeros((NUM_POINTS, 2), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    # Initialize random starting offsets for noise
    for i in range(NUM_POINTS):
        noise_offsets[i, 0] = py5.random(1000)
        noise_offsets[i, 1] = py5.random(1000)

def update_points():
    time = py5.frame_count * 0.005
    for i in range(NUM_POINTS):
        # Base wander using noise
        nx = py5.os_noise(noise_offsets[i, 0], time)
        ny = py5.os_noise(noise_offsets[i, 1], time)
        
        # Map noise to screen bounds (with padding to avoid edge artifacts)
        # We expand the bounds slightly so points can wander off screen and come back
        points[i, 0] = py5.remap(nx, -1, 1, -200, py5.width + 200)
        points[i, 1] = py5.remap(ny, -1, 1, -200, py5.height + 200)

def draw():
    # Erase trail smoothly
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    update_points()
    
    # Compute Voronoi
    try:
        vor = Voronoi(points)
        
        # We will draw the finite edges of the Voronoi diagram
        edges = []
        for ridge_indices in vor.ridge_vertices:
            # -1 means the ridge goes to infinity
            if ridge_indices[0] != -1 and ridge_indices[1] != -1:
                p1 = vor.vertices[ridge_indices[0]]
                p2 = vor.vertices[ridge_indices[1]]
                edges.append((p1, p2))
                
        # Draw edges
        for p1, p2 in edges:
            # Skip if completely outside screen
            if (p1[0] < 0 and p2[0] < 0) or (p1[0] > py5.width and p2[0] > py5.width):
                continue
            if (p1[1] < 0 and p2[1] < 0) or (p1[1] > py5.height and p2[1] > py5.height):
                continue
                
            # Distance of edge to center
            cx, cy = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
            dist_to_center = np.sqrt((cx - py5.width/2)**2 + (cy - py5.height/2)**2)
            max_dist = py5.width / 1.5
            normalized_dist = min(dist_to_center / max_dist, 1.0)
            
            # Hot pink glowing edges
            hue = 320 # Pink/Magenta
            sat = 90
            bri = py5.remap(normalized_dist, 0, 1, 100, 20)
            alpha = py5.remap(normalized_dist, 0, 1, 100, 30)
            
            py5.stroke(hue, sat, bri, alpha)
            
            # Edges closer to center are thicker
            sw = py5.remap(normalized_dist, 0, 1, 6.0, 1.0)
            py5.stroke_weight(sw)
            
            py5.line(p1[0], p1[1], p2[0], p2[1])
            
    except Exception as e:
        # qhull error if points are collinear, etc. just skip frame
        print(f"Skipping frame due to Voronoi error: {e}")
            
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

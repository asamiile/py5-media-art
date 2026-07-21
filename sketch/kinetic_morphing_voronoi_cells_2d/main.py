from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.spatial import Voronoi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

NUM_CELLS = 150

# We need extra points outside the boundary to close edge cells
margin = 500
extra_points = np.array([
    [-margin, -margin],
    [SIZE[0]+margin, -margin],
    [-margin, SIZE[1]+margin],
    [SIZE[0]+margin, SIZE[1]+margin],
    [SIZE[0]/2, -margin*2],
    [SIZE[0]/2, SIZE[1]+margin*2],
    [-margin*2, SIZE[1]/2],
    [SIZE[0]+margin*2, SIZE[1]/2]
])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    global seeds, offsets
    seeds = np.random.uniform(0, 1, (NUM_CELLS, 2))
    offsets = np.random.uniform(0, 1000, NUM_CELLS)

def draw():
    py5.background(10)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Calculate current point positions
    pts = []
    for i in range(NUM_CELLS):
        nx = py5.noise(offsets[i] + t * 2.0)
        ny = py5.noise(offsets[i] + 1000 + t * 2.0)
        pts.append([nx * SIZE[0], ny * SIZE[1]])
        
    pts = np.array(pts)
    all_pts = np.vstack([pts, extra_points])
    
    try:
        vor = Voronoi(all_pts)
        
        py5.stroke(255)
        py5.stroke_weight(4)
        
        for region_index in vor.point_region[:NUM_CELLS]:
            region = vor.regions[region_index]
            if -1 not in region and len(region) > 0:
                polygon = [vor.vertices[i] for i in region]
                
                # Calculate centroid to color based on position
                cx = sum(p[0] for p in polygon) / len(polygon)
                cy = sum(p[1] for p in polygon) / len(polygon)
                
                hue = (cx / SIZE[0] * 180 + cy / SIZE[1] * 180 + t * 360) % 360
                py5.fill(hue, 80, 90, 80)
                
                py5.begin_shape()
                for p in polygon:
                    py5.vertex(float(p[0]), float(p[1]))
                py5.end_shape(py5.CLOSE)
    except Exception as e:
        print(f"Voronoi failed: {e}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
        import os
        os._exit(0)

py5.run_sketch()

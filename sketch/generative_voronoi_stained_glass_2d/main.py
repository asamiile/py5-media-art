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

NUM_POINTS = 300
MARGIN = 200 # Extend points beyond screen to avoid edge artifacts

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global point_bases, point_phases, point_speeds
    
    # Generate points across a wider area to avoid infinite regions creeping in
    point_bases = np.random.rand(NUM_POINTS, 2) * [py5.width + MARGIN*2, py5.height + MARGIN*2] - [MARGIN, MARGIN]
    point_phases = np.random.rand(NUM_POINTS, 2) * py5.TWO_PI
    point_speeds = np.random.rand(NUM_POINTS, 2) * 2.0 + 0.5

def get_color(x, y, t):
    # Dynamic cathedral color palette based on position and time
    nx = x / py5.width
    ny = y / py5.height
    
    # Color cycles through deep ruby, sapphire, amethyst, and gold
    r = int((np.sin(nx * py5.PI + t * py5.TWO_PI) * 0.5 + 0.5) * 200 + 55)
    g = int((np.sin(ny * py5.PI - t * py5.TWO_PI * 1.5) * 0.5 + 0.5) * 150)
    b = int((np.cos((nx+ny) * py5.PI + t * py5.TWO_PI * 0.8) * 0.5 + 0.5) * 255)
    
    return py5.color(r, g, b, 230)

def draw():
    py5.background(0)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Move points
    offsets = np.sin(point_phases + t * py5.TWO_PI * point_speeds) * 150
    points = point_bases + offsets
    
    # Compute Voronoi
    try:
        vor = Voronoi(points)
    except Exception:
        # In rare collinear cases, Voronoi might fail
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
        return
        
    py5.stroke(10) # Dark lead lines
    py5.stroke_weight(py5.width * 0.003)
    
    for point_idx, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        if not region or -1 in region:
            continue
            
        polygon = vor.vertices[region]
        
        # Check if polygon is on screen
        if np.max(polygon[:, 0]) < 0 or np.min(polygon[:, 0]) > py5.width or \
           np.max(polygon[:, 1]) < 0 or np.min(polygon[:, 1]) > py5.height:
            continue
            
        cx, cy = points[point_idx]
        py5.fill(get_color(cx, cy, t))
        
        py5.begin_shape()
        py5.vertices(polygon)
        py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

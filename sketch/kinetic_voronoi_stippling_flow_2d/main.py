from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
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

NUM_POINTS = 1200
PAD = 200 # padding for mirroring points to get closed cells on screen edges

points = np.zeros((NUM_POINTS, 2), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize points randomly
    points[:, 0] = np.random.uniform(0, SIZE[0], NUM_POINTS)
    points[:, 1] = np.random.uniform(0, SIZE[1], NUM_POINTS)

def draw():
    global points
    
    t = py5.frame_count * 0.005
    
    # Move points using a curl noise field
    # We use a simple trigonometric interference field
    px = points[:, 0] * 0.001
    py_coords = points[:, 1] * 0.001
    
    vx = np.sin(py_coords * 3.1 + t) * np.cos(px * 1.7 - t * 1.3) * 5.0
    vy = np.cos(px * 2.5 + t * 0.8) * np.sin(py_coords * 2.1 + t * 1.1) * 5.0
    
    points[:, 0] += vx
    points[:, 1] += vy
    
    # Wrap around edges
    points[:, 0] = points[:, 0] % SIZE[0]
    points[:, 1] = points[:, 1] % SIZE[1]
    
    # To get bounded Voronoi cells, we mirror all points across the screen boundaries
    mirrored = []
    mirrored.append(points)
    mirrored.append(points * [-1, 1]) # left
    mirrored.append(points * [1, -1]) # top
    mirrored.append(points * [-1, -1]) # top-left
    
    p_right = points.copy()
    p_right[:, 0] = SIZE[0] + (SIZE[0] - points[:, 0])
    mirrored.append(p_right) # right
    
    p_bottom = points.copy()
    p_bottom[:, 1] = SIZE[1] + (SIZE[1] - points[:, 1])
    mirrored.append(p_bottom) # bottom
    
    p_br = p_bottom.copy()
    p_br[:, 0] = SIZE[0] + (SIZE[0] - points[:, 0])
    mirrored.append(p_br) # bottom-right
    
    p_tr = p_right.copy()
    p_tr[:, 1] = points[:, 1] * -1
    mirrored.append(p_tr) # top-right
    
    p_bl = p_bottom.copy()
    p_bl[:, 0] = points[:, 0] * -1
    mirrored.append(p_bl) # bottom-left
    
    all_points = np.vstack(mirrored)
    
    # Compute Voronoi diagram
    vor = Voronoi(all_points)
    
    py5.background(5, 10, 25) # Deep oceanic blue
    
    py5.stroke(100, 255, 255, 100)
    py5.stroke_weight(2)
    
    # Render finite regions for the original points (indices 0 to NUM_POINTS-1)
    for i in range(NUM_POINTS):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        if not -1 in region and len(region) > 2:
            polygon = vor.vertices[region]
            
            # Simple area calculation via shoelace formula
            x = polygon[:, 0]
            y = polygon[:, 1]
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            
            # Map area to color
            # Small areas = bright cyan/teal, Large areas = dark blue
            norm_area = np.clip(area / 15000.0, 0, 1)
            
            r = int(5 + 20 * norm_area)
            g = int(255 - 200 * norm_area)
            b = int(255 - 100 * norm_area)
            
            py5.fill(r, g, b, 200)
            
            py5.begin_shape()
            for vx, vy in polygon:
                py5.vertex(vx, vy)
            py5.end_shape(py5.CLOSE)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

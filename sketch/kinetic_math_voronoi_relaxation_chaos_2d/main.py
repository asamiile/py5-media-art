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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Increase point count for high detail
N = 15000
margin = 200
bounds_min = np.array([-margin, -margin])
bounds_max = np.array([SIZE[0]+margin, SIZE[1]+margin])

pts = np.random.uniform(bounds_min, bounds_max, (N, 2))

bound_pts = np.array([
    [-margin*2, -margin*2],
    [SIZE[0]+margin*2, -margin*2],
    [SIZE[0]+margin*2, SIZE[1]+margin*2],
    [-margin*2, SIZE[1]+margin*2]
])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    global pts
    py5.background(240, 100, 10)  # Very dark blue
    
    t = py5.frame_count / TOTAL_FRAMES * np.pi * 2
    
    all_pts = np.vstack([pts, bound_pts])
    vor = Voronoi(all_pts)
    
    centroids = np.zeros_like(pts)
    
    py5.no_stroke()
    
    # Target average area
    avg_area = (SIZE[0] * SIZE[1]) / N
    
    for i in range(N):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        if -1 in region or len(region) == 0:
            centroids[i] = pts[i]
            continue
            
        polygon = vor.vertices[region]
        
        x = polygon[:, 0]
        y = polygon[:, 1]
        a = x[:-1] * y[1:] - x[1:] * y[:-1]
        a = np.append(a, x[-1] * y[0] - x[0] * y[-1])
        area = 0.5 * np.sum(a)
        
        cx = np.sum((x[:-1] + x[1:]) * a[:-1])
        cx += (x[-1] + x[0]) * a[-1]
        cy = np.sum((y[:-1] + y[1:]) * a[:-1])
        cy += (y[-1] + y[0]) * a[-1]
        
        if area != 0:
            cx /= (6.0 * area)
            cy /= (6.0 * area)
            centroids[i] = [cx, cy]
        else:
            centroids[i] = pts[i]
            
        # Color mapping: compressed dense regions = pink/purple, expanded regions = blue/cyan
        norm_area = np.clip(abs(area) / (avg_area * 3.0), 0.0, 1.0)
        hue = 300 - norm_area * 120 # 300 (Magenta) -> 180 (Cyan)
        
        py5.fill(hue, 95, 40 + (1.0-norm_area)*60, 100)
        
        py5.begin_shape()
        for pt in polygon:
            py5.vertex(pt[0], pt[1])
        py5.end_shape(py5.CLOSE)

    # Physics update
    relax_force = centroids - pts
    
    nx = np.sin(pts[:, 1] * 0.003 + t * 1.5) * np.cos(pts[:, 0] * 0.002 - t * 0.5)
    ny = -np.cos(pts[:, 0] * 0.003 - t * 1.5) * np.sin(pts[:, 1] * 0.002 + t * 0.5)
    chaos_force = np.column_stack([nx, ny]) * 10.0
    
    pts += relax_force * 0.05 + chaos_force
    
    pts[:, 0] = np.clip(pts[:, 0], bounds_min[0], bounds_max[0])
    pts[:, 1] = np.clip(pts[:, 1], bounds_min[1], bounds_max[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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

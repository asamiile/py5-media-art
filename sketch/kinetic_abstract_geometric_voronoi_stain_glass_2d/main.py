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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# We will use 100 moving points
NUM_POINTS = 100
points = np.random.uniform(0, max(SIZE), (NUM_POINTS, 2)).astype(np.float32)

# Phantom points to bound the Voronoi regions
phantom_radius = max(SIZE) * 2.0
theta = np.linspace(0, 2*np.pi, 20, endpoint=False)
phantom_pts = np.column_stack((
    np.cos(theta) * phantom_radius + SIZE[0]/2,
    np.sin(theta) * phantom_radius + SIZE[1]/2
))

# Colors for the cells
cell_hues = np.random.uniform(0, 360, NUM_POINTS)
# Ensure some are distinct stained glass colors: reds, blues, yellows
colors_base = np.random.choice([0, 60, 220, 280, 320], NUM_POINTS)
cell_hues = (colors_base + np.random.uniform(-15, 15, NUM_POINTS)) % 360

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 15, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_join(py5.ROUND)

def draw():
    global points, cell_hues
    
    time_val = py5.frame_count * 0.02
    
    # Update points with noise
    speeds = 2.0
    for i in range(NUM_POINTS):
        angle = py5.noise(points[i, 0] * 0.002, points[i, 1] * 0.002, time_val * 0.5) * np.pi * 4.0
        points[i, 0] += np.cos(angle) * speeds
        points[i, 1] += np.sin(angle) * speeds
        
        # Soft bounce off walls
        if points[i, 0] < 0: points[i, 0] += 5
        if points[i, 0] > py5.width: points[i, 0] -= 5
        if points[i, 1] < 0: points[i, 1] += 5
        if points[i, 1] > py5.height: points[i, 1] -= 5

    # Shift colors slowly
    cell_hues = (cell_hues + 0.2) % 360

    # Combine with phantom points
    all_pts = np.vstack((points, phantom_pts))
    
    # Calculate Voronoi
    try:
        vor = Voronoi(all_pts)
    except:
        # If Voronoi fails (e.g. Qhull error from colinear points), skip frame
        pass
        return

    py5.background(10, 15, 10)
    
    py5.stroke_weight(5)
    py5.stroke(10, 15, 10) # Dark lines for stained glass
    
    # Draw regions
    for i in range(NUM_POINTS):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        
        # If -1 is in region, it's an infinite region (shouldn't happen with phantoms)
        if -1 not in region and len(region) > 0:
            polygon = [vor.vertices[v] for v in region]
            
            # Draw
            py5.fill(cell_hues[i], 80, 90, 85)
            
            py5.begin_shape()
            for p in polygon:
                py5.vertex(p[0], p[1])
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

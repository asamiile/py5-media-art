from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import scipy.spatial

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
import py5

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def get_points(time):
    # Create radial phyllotaxis-like seeds that drift outwards
    points = []
    num_points = 200
    for i in range(1, num_points):
        # time causes expansion
        r = 10 * py5.sqrt(i) * (1.0 + py5.sin(time * 0.5) * 0.2 + time * 0.1)
        theta = i * 137.5 + time * 10
        # add some noise
        nx = py5.os_noise(i * 0.1, time * 0.5) * 50 - 25
        ny = py5.os_noise(time * 0.5, i * 0.1) * 50 - 25
        
        px = py5.width/2 + py5.cos(py5.radians(theta)) * r + nx
        py = py5.height/2 + py5.sin(py5.radians(theta)) * r + ny
        points.append([px, py])
        
    # Add boundary points to prevent Voronoi edge collapse
    points.extend([[-500, -500], [py5.width+500, -500], [py5.width+500, py5.height+500], [-500, py5.height+500]])
    return np.array(points)

def draw():
    py5.background(0)
    
    time = py5.frame_count * 0.05
    points = get_points(time)
    
    vor = scipy.spatial.Voronoi(points)
    
    py5.stroke_weight(6)
    py5.stroke(0) # Thick lead lines
    
    for i, region_index in enumerate(vor.point_region[:-4]): # ignore boundaries
        region = vor.regions[region_index]
        if not -1 in region and len(region) > 0:
            polygon = [vor.vertices[v] for v in region]
            
            # Use point coordinates for noise-based color
            pt = points[i]
            hue_val = py5.remap(py5.os_noise(pt[0]*0.002, pt[1]*0.002, time*0.2), 0, 1, 0, 360)
            
            # Saturated jewel tones
            py5.fill(hue_val, 95, 90, 80)
            
            py5.begin_shape()
            for v in polygon:
                py5.vertex(v[0], v[1])
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

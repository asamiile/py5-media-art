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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 500
points = np.random.uniform(-200, max(SIZE) + 200, (NUM_POINTS, 2)).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)

def get_noise_field(pts, time_val):
    # A simple analytical "noise" field using combined sines
    scale = 0.003
    angles = np.sin(pts[:, 0] * scale + time_val) * np.cos(pts[:, 1] * scale + time_val * 0.8) * np.pi * 2.0
    return angles

def draw():
    global points
    
    time_val = py5.frame_count * 0.02
    
    # Update points
    angles = get_noise_field(points, time_val)
    speeds = 5.0
    points[:, 0] += np.cos(angles) * speeds
    points[:, 1] += np.sin(angles) * speeds
    
    # Wrap around or reflect if they go way out of bounds
    out_of_bounds = (points[:, 0] < -400) | (points[:, 0] > py5.width + 400) | \
                    (points[:, 1] < -400) | (points[:, 1] > py5.height + 400)
    if np.any(out_of_bounds):
        num_out = np.sum(out_of_bounds)
        points[out_of_bounds, 0] = np.random.uniform(0, py5.width, num_out)
        points[out_of_bounds, 1] = np.random.uniform(0, py5.height, num_out)
    
    # Calculate Delaunay triangulation
    tri = Delaunay(points)
    simplices = tri.simplices
    
    # Render
    # Fade background slightly for a nice trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 20, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # We can calculate centers to determine color
    p1 = points[simplices[:, 0]]
    p2 = points[simplices[:, 1]]
    p3 = points[simplices[:, 2]]
    
    centers = (p1 + p2 + p3) / 3.0
    
    # Calculate area to map to brightness
    # Area = 0.5 * |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)|
    areas = 0.5 * np.abs(p1[:, 0]*(p2[:, 1] - p3[:, 1]) + 
                         p2[:, 0]*(p3[:, 1] - p1[:, 1]) + 
                         p3[:, 0]*(p1[:, 1] - p2[:, 1]))
                         
    # Limit max area
    areas = np.clip(areas, 0, 10000)
    
    # Map coordinates to hue
    hues = (centers[:, 0] * 0.1 + centers[:, 1] * 0.1 + time_val * 20.0) % 360
    
    # Brightness inversely proportional to area (small triangles = bright)
    brightness = 100.0 - (areas / 10000.0) * 80.0
    alpha = 40.0 - (areas / 10000.0) * 35.0
    
    # Use begin_shape for fast rendering
    py5.begin_shape(py5.TRIANGLES)
    py5.no_stroke()
    
    for i in range(len(simplices)):
        py5.fill(hues[i], 80, brightness[i], alpha[i])
        py5.vertex(p1[i, 0], p1[i, 1])
        py5.vertex(p2[i, 0], p2[i, 1])
        py5.vertex(p3[i, 0], p3[i, 1])
        
    py5.end_shape()
    
    # Draw points as well to look like a constellation
    py5.stroke(255, 30)
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for p in points:
        py5.vertex(p[0], p[1])
    py5.end_shape()

    py5.blend_mode(py5.BLEND)

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

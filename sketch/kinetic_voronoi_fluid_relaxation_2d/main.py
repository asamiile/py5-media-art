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

NUM_CELLS = 4000
NOISE_SCALE = 0.002
SPEED = 3.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors
    W, H = SIZE
    
    # Initialize points uniformly with some padding to prevent boundary issues
    pos = np.random.uniform(-100, W + 100, (NUM_CELLS, 2))
    
    # Assign colors based on initial Y position
    colors = np.zeros((NUM_CELLS, 3))
    colors[:, 0] = (pos[:, 1] / H * 120 + 200) % 360 # Hue (cyan to magenta to purple)
    colors[:, 1] = 90
    colors[:, 2] = 100

def draw():
    global pos
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    W, H = SIZE
    t = py5.frame_count * 0.01
    
    # Compute fluid-like movement using Py5 open simplex noise
    # To vectorize noise, we use a simple procedural pseudo-curl
    # But since Py5 os_noise isn't vectorized out-of-the-box in python easily, we'll use numpy math for a fake curl field.
    
    x = pos[:, 0] * NOISE_SCALE
    y = pos[:, 1] * NOISE_SCALE
    
    # Fake curl noise using multiple sines and cosines
    vx = np.sin(y * 3.1 + t) * np.cos(x * 1.5 - t) + np.sin(y * 1.2 - t * 0.5)
    vy = -np.cos(x * 3.1 - t) * np.sin(y * 1.5 + t) - np.cos(x * 1.2 + t * 0.5)
    
    # Move points
    pos[:, 0] += vx * SPEED
    pos[:, 1] += vy * SPEED
    
    # Wrap around (toroidal), but Voronoi doesn't like toroidal easily without tiling.
    # Instead, we just let them drift and bounce off padded walls.
    bounce_x = (pos[:, 0] < -200) | (pos[:, 0] > W + 200)
    bounce_y = (pos[:, 1] < -200) | (pos[:, 1] > H + 200)
    
    # If they go too far, reset them to the opposite side
    pos[pos[:, 0] < -200, 0] += (W + 400)
    pos[pos[:, 0] > W + 200, 0] -= (W + 400)
    pos[pos[:, 1] < -200, 1] += (H + 400)
    pos[pos[:, 1] > H + 200, 1] -= (H + 400)
    
    # Compute Voronoi
    try:
        vor = Voronoi(pos)
    except:
        # qhull error fallback
        py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
        return
        
    # Draw Voronoi ridges
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    
    # To colorize lines, we can use the average color of the two points sharing the ridge.
    # vor.ridge_points contains the indices of the two points sharing the ridge.
    # vor.ridge_vertices contains the indices of the vertices of the ridge.
    
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        if v1 == -1 or v2 == -1:
            continue
            
        pt1 = vor.vertices[v1]
        pt2 = vor.vertices[v2]
        
        # Fast bounds check
        if (pt1[0] < 0 and pt2[0] < 0) or (pt1[0] > W and pt2[0] > W) or \
           (pt1[1] < 0 and pt2[1] < 0) or (pt1[1] > H and pt2[1] > H):
            continue
            
        c = colors[p1] # Just use color of one of the generating points
        py5.stroke(c[0], c[1], c[2], 150)
        py5.vertex(pt1[0], pt1[1])
        py5.vertex(pt2[0], pt2[1])
        
    py5.end_shape()

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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import math

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

# We will generate a grid of points
STEP = 4 # resolution of the sand points

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100)
    
    # Pre-generate a 2D meshgrid of coordinates scaled from -1 to 1
    global X, Y, X_coords, Y_coords
    x_range = np.arange(0, py5.width, STEP)
    y_range = np.arange(0, py5.height, STEP)
    
    # Grid in screen coordinates
    X_coords, Y_coords = np.meshgrid(x_range, y_range)
    X_coords = X_coords.flatten()
    Y_coords = Y_coords.flatten()
    
    # Grid in normalized coordinates (-1 to 1) for the math equation
    X = (X_coords / py5.width) * 2 - 1
    Y = (Y_coords / py5.height) * 2 - 1

def draw():
    py5.background(20, 10, 10) # Dark muted warm brown
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # The Chladni equation depends on m, n parameters
    # We will smoothly interpolate them using a looping noise or sine wave
    # Let m transition from 2 to 7, and n from 4 to 9
    m = py5.remap(math.sin(t * py5.TWO_PI), -1, 1, 2.0, 7.0)
    n = py5.remap(math.cos(t * py5.TWO_PI), -1, 1, 4.0, 9.0)
    
    # Evaluate the Chladni standing wave equation over the normalized grid
    # Equation: v = a * sin(n * pi * x) * sin(m * pi * y) + b * sin(m * pi * x) * sin(n * pi * y)
    term1 = np.sin(n * np.pi * X) * np.sin(m * np.pi * Y)
    term2 = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    
    # Modulate a and b to break symmetry slightly over time
    a = 1.0
    b = 1.0 + math.sin(t * py5.TWO_PI * 2.0) * 0.2
    
    V = a * term1 + b * term2
    
    # The sand gathers where V is close to 0 (the nodes)
    threshold = 0.15 # Width of the sand lines
    
    mask = np.abs(V) < threshold
    
    # Get the coordinates where the mask is true
    sand_x = X_coords[mask]
    sand_y = Y_coords[mask]
    
    # Add a tiny bit of random jitter to the sand to make it look organic
    jitter_x = np.random.normal(0, 1.5, size=sand_x.shape)
    jitter_y = np.random.normal(0, 1.5, size=sand_y.shape)
    
    points_to_draw = np.column_stack((sand_x + jitter_x, sand_y + jitter_y))
    
    py5.stroke(40, 15, 90, 200) # Off-white sand color
    py5.stroke_weight(2)
    
    if len(points_to_draw) > 0:
        py5.points(points_to_draw)

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

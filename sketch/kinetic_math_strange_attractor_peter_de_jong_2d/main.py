from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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

# Number of points to compute per frame
NUM_POINTS = 500_000

# We will use numpy to calculate the Peter de Jong attractor iteratively
def compute_attractor(a, b, c, d, num_iters):
    # Initialize arrays
    x = np.zeros(num_iters, dtype=np.float32)
    y = np.zeros(num_iters, dtype=np.float32)
    
    # We can't easily vectorize the sequential dependency x_n+1 = f(x_n), 
    # but we can run multiple parallel chains from random start points.
    num_chains = 10000
    iters_per_chain = num_iters // num_chains
    
    px = np.random.uniform(-1, 1, num_chains).astype(np.float32)
    py_coord = np.random.uniform(-1, 1, num_chains).astype(np.float32)
    
    all_x = []
    all_y = []
    
    for _ in range(iters_per_chain):
        # Peter de Jong equations
        nx = np.sin(a * py_coord) - np.cos(b * px)
        ny = np.sin(c * px) - np.cos(d * py_coord)
        px = nx
        py_coord = ny
        all_x.append(px)
        all_y.append(py_coord)
        
    # Stack and flatten
    return np.stack(all_x).flatten(), np.stack(all_y).flatten()

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(220, 90, 10) # Midnight blue
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.fill(220, 90, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.005
    
    # Smoothly animate parameters a, b, c, d
    a = 1.4 + np.sin(time_val * 1.3) * 0.4
    b = -2.3 + np.cos(time_val * 0.9) * 0.5
    c = 2.4 + np.sin(time_val * 1.1) * 0.3
    d = -2.1 + np.cos(time_val * 1.5) * 0.4
    
    # Compute points
    x, y = compute_attractor(a, b, c, d, NUM_POINTS)
    
    # Map points to screen coordinates
    # The Peter de Jong attractor points are in range roughly [-2, 2]
    # We map them to the screen with a margin
    scale = min(py5.width, py5.height) * 0.22
    screen_x = py5.width / 2 + x * scale
    screen_y = py5.height / 2 + y * scale
    
    # Draw points
    # Using point() in a loop is slow, we use Py5Shape or points() if available.
    # py5 has py5.points() which takes a 2D numpy array.
    pts = np.column_stack((screen_x, screen_y))
    
    # Determine color based on time
    hue = (40 + np.sin(time_val) * 20) % 360 # Golden/yellow shifting to orange
    py5.stroke(float(hue), 60, 100, 2) # Very low alpha since there are 500k points
    py5.stroke_weight(1)
    py5.points(pts)

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

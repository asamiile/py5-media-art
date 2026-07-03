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

NUM_BUBBLES = 1500
x = np.random.uniform(0, SIZE[0], NUM_BUBBLES).astype(np.float32)
y = np.random.uniform(0, SIZE[1], NUM_BUBBLES).astype(np.float32)
r = np.zeros(NUM_BUBBLES, dtype=np.float32)
growing = np.ones(NUM_BUBBLES, dtype=bool)
lifespan = np.random.uniform(60, 300, NUM_BUBBLES)
age = np.zeros(NUM_BUBBLES)

# To avoid full O(N^2) every frame in Python we will just do a simple NumPy broadcast.
# 1500 is very small for modern CPUs in numpy.

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(220, 90, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(3)

def draw():
    global x, y, r, growing, lifespan, age
    
    # Trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(220, 90, 10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    time_val = py5.frame_count * 0.05
    
    # Grow bubbles
    r[growing] += 1.5
    age += 1
    
    # Check collisions (only growing ones need to stop)
    # Calculate distance matrix using numpy
    # We only care if dist < r_i + r_j
    # To optimize slightly, we only check growing bubbles against all others
    
    growing_idx = np.where(growing)[0]
    
    if len(growing_idx) > 0:
        # Broadcasting
        dx = x[growing_idx, np.newaxis] - x
        dy = y[growing_idx, np.newaxis] - y
        dist_sq = dx**2 + dy**2
        min_dist_sq = (r[growing_idx, np.newaxis] + r + 2.0)**2
        
        # We must ignore self collision
        np.fill_diagonal(dist_sq[:, growing_idx], np.inf)
        
        # Check if any distance is less than sum of radii
        collision = np.any(dist_sq < min_dist_sq, axis=1)
        growing[growing_idx[collision]] = False
        
    # Check bounds
    hit_bounds = (x - r < 0) | (x + r > py5.width) | (y - r < 0) | (y + r > py5.height)
    growing[hit_bounds] = False
    
    # Pop old bubbles
    popped = age > lifespan
    
    if np.any(popped):
        num_popped = np.sum(popped)
        r[popped] = 0
        x[popped] = np.random.uniform(0, py5.width, num_popped)
        y[popped] = np.random.uniform(0, py5.height, num_popped)
        growing[popped] = True
        age[popped] = 0
        lifespan[popped] = np.random.uniform(60, 300, num_popped)
        
    # Draw bubbles
    py5.begin_shape(py5.LINES)
    # We could use ellipse, but py5.ellipse in a loop for 1500 items is a bit slow.
    # Actually, 1500 ellipses in py5 is easily 60fps.
    py5.end_shape()
    
    # Draw circles
    for i in range(NUM_BUBBLES):
        if r[i] > 1:
            hue = (200 + r[i] * 2.0 + time_val * 5.0) % 360
            alpha = max(0, 100 - (age[i] / lifespan[i]) * 100)
            py5.stroke(hue, 80, 100, alpha)
            
            # Draw a solid circle with fill instead of just outline for a better foam effect
            # Fill with very low opacity
            py5.fill(hue, 90, 80, alpha * 0.2)
            py5.ellipse(x[i], y[i], r[i]*2, r[i]*2)

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

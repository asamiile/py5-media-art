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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 10000
STEPS_PER_FRAME = 30

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(5, 5, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global start_x, start_y, particle_colors
    
    # Initialize uniform starting positions
    start_x = np.random.uniform(-3.0, 3.0, NUM_PARTICLES)
    start_y = np.random.uniform(-3.0, 3.0, NUM_PARTICLES)
    
    # Pre-generate colors for the particles
    # We will draw points in large batches, so assigning colors isn't natively easy in a single py5.points() call
    # if we want exactly one color per point. 
    # But since it's an additive glowing dust cloud, a solid ethereal color for all points per frame works beautifully.
    
def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    progress = py5.frame_count / TOTAL_FRAMES
    time_val = progress * py5.PI * 2.0
    
    # Seamlessly looping parameters using Perlin noise circles
    # This prevents the chaotic attractor from jumping or stuttering
    n1 = py5.noise(np.cos(time_val) * 0.5 + 10, np.sin(time_val) * 0.5 + 10)
    n2 = py5.noise(np.cos(time_val) * 0.5 + 20, np.sin(time_val) * 0.5 + 20)
    n3 = py5.noise(np.cos(time_val) * 0.5 + 30, np.sin(time_val) * 0.5 + 30)
    n4 = py5.noise(np.cos(time_val) * 0.5 + 40, np.sin(time_val) * 0.5 + 40)
    
    # Base attractive parameters with a tiny drift
    a = -1.4 + (n1 - 0.5) * 0.2
    b = 1.6 + (n2 - 0.5) * 0.2
    c = 1.0 + (n3 - 0.5) * 0.2
    d = 0.7 + (n4 - 0.5) * 0.2
    
    x = start_x.copy()
    y = start_y.copy()
    
    # We will accumulate all 1,500,000 points generated in this frame into one huge array
    all_x = np.zeros(NUM_PARTICLES * STEPS_PER_FRAME)
    all_y = np.zeros(NUM_PARTICLES * STEPS_PER_FRAME)
    
    for i in range(STEPS_PER_FRAME):
        # Clifford Attractor equations
        x_new = np.sin(a * y) + c * np.cos(a * x)
        y_new = np.sin(b * x) + d * np.cos(b * y)
        x = x_new
        y = y_new
        
        idx_start = i * NUM_PARTICLES
        idx_end = idx_start + NUM_PARTICLES
        all_x[idx_start:idx_end] = x
        all_y[idx_start:idx_end] = y

    # The attractor naturally falls within the range [-3, 3] approximately.
    # Map to screen coordinates.
    screen_x = py5.remap(all_x, -2.5, 2.5, 0, py5.width)
    screen_y = py5.remap(all_y, -2.5, 2.5, py5.height, 0)
    
    # Format for py5.points
    pts = np.column_stack((screen_x, screen_y))
    
    # An ethereal, pulsing cyan/purple based on progress
    r = int(100 + 100 * np.sin(time_val))
    g = int(150 + 100 * np.cos(time_val))
    b_val = 255
    
    py5.stroke(r, g, b_val, 15)
    py5.stroke_weight(2.0)
    
    py5.points(pts)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

from pathlib import Path
import shutil
import subprocess
import sys
import math
import py5
import numpy as np

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

SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0

NUM_PARTICLES = 30000

# To make the stream continuous, we track 'ages' for particles and reset them
x_vals = np.random.uniform(-1, 1, NUM_PARTICLES)
y_vals = np.random.uniform(-1, 1, NUM_PARTICLES)
z_vals = np.random.uniform(20, 25, NUM_PARTICLES)
ages = np.random.uniform(0, 1000, NUM_PARTICLES)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    
def draw():
    global x_vals, y_vals, z_vals, ages
    
    # Motion blur / fade effect
    py5.no_stroke()
    py5.fill(0, 0, 0, 10) # 10% opacity black
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    dt = 0.01
    
    dx = SIGMA * (y_vals - x_vals) * dt
    dy = (x_vals * (RHO - z_vals) - y_vals) * dt
    dz = (x_vals * y_vals - BETA * z_vals) * dt
    
    x_vals += dx
    y_vals += dy
    z_vals += dz
    ages += 1
    
    # Reset particles that are too old to keep the simulation thick at the origin
    reset_mask = ages > 400
    if np.any(reset_mask):
        x_vals[reset_mask] = np.random.uniform(-0.1, 0.1, np.sum(reset_mask))
        y_vals[reset_mask] = np.random.uniform(-0.1, 0.1, np.sum(reset_mask))
        z_vals[reset_mask] = np.random.uniform(20.0, 21.0, np.sum(reset_mask))
        ages[reset_mask] = 0
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    rot_y = t * 0.5
    cos_ry = math.cos(rot_y)
    sin_ry = math.sin(rot_y)
    
    rot_x = math.sin(t * 0.3) * 0.4
    cos_rx = math.cos(rot_x)
    sin_rx = math.sin(rot_x)
    
    py5.stroke_weight(2)
    
    # We will use numpy to calculate the points to speed it up!
    ox = x_vals
    oy = y_vals
    oz = z_vals - 25.0
    
    rx1 = ox * cos_ry - oz * sin_ry
    rz1 = ox * sin_ry + oz * cos_ry
    
    ry2 = oy * cos_rx - rz1 * sin_rx
    rz2 = oy * sin_rx + rz1 * cos_rx
    
    scale = 1200 / (1200 + rz2)
    px = rx1 * scale * 30
    py_coord = ry2 * scale * 30
    
    # Draw points in Python loop (py5 doesn't have vectorized point drawing)
    for i in range(NUM_PARTICLES):
        hue = (10 + ages[i] * 0.5 + t * 20) % 360
        py5.stroke(hue, 90, 100, 70)
        py5.point(px[i], py_coord[i])

    py5.color_mode(py5.RGB, 255)

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

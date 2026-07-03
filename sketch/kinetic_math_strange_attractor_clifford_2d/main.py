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

NUM_PARTICLES = 300000
x = np.random.uniform(-2, 2, NUM_PARTICLES).astype(np.float32)
y = np.random.uniform(-2, 2, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 5)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global x, y
    
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 5, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.005
    
    # Smoothly varying parameters for the Clifford Attractor
    a = 1.4 + np.sin(time_val * 1.3) * 0.5
    b = 1.7 + np.cos(time_val * 0.9) * 0.4
    c = 1.1 + np.sin(time_val * 1.1) * 0.3
    d = 0.8 + np.cos(time_val * 0.7) * 0.5
    
    # Update particles using Clifford map equations
    # For speed, we do a few iterations per frame to let them traverse the shape
    for _ in range(2):
        xn = np.sin(a * y) + c * np.cos(a * x)
        yn = np.sin(b * x) + d * np.cos(b * y)
        x = xn
        y = yn
        
    # Map to screen coordinates
    # Clifford attractor generally bounds within [-3, 3] or so
    scale = min(py5.width, py5.height) * 0.18
    screen_x = x * scale + py5.width / 2
    screen_y = y * scale + py5.height / 2
    
    # Color based on position and time
    hues = (180 + x * 20 + y * 20 + time_val * 100) % 360
    
    # Draw points
    py5.stroke_weight(1.0)
    
    # Fast drawing by grouping colors into bins, or we can just draw all points as a single color 
    # to be extremely fast, or slightly grouped.
    num_bins = 20
    bin_size = NUM_PARTICLES // num_bins
    
    for b_idx in range(num_bins):
        start = b_idx * bin_size
        end = start + bin_size
        
        # Take the average hue for this bin (approximation for speed)
        h = np.mean(hues[start:end])
        py5.stroke(h, 80, 100, 10)
        
        pts = np.column_stack((screen_x[start:end], screen_y[start:end]))
        py5.points(pts)

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

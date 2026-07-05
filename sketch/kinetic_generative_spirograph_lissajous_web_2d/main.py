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

# Keep a history of points
HISTORY_SIZE = 600
history = np.zeros((HISTORY_SIZE, 2))
history_idx = 0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 90, 5)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.blend_mode(py5.ADD)

def draw():
    global history, history_idx
    
    time_val = py5.frame_count * 0.05
    
    # Calculate new point using complex Lissajous / harmonograph equations
    # Using multiple frequencies for complex web
    f1, f2, f3, f4 = 3.01, 2.05, 1.99, 4.02
    d1, d2, d3, d4 = 0.002, 0.001, 0.0015, 0.0005
    
    # Phase shifts that evolve over time
    p1 = time_val * 0.1
    p2 = time_val * 0.15
    p3 = time_val * 0.05
    p4 = time_val * 0.2
    
    # Radii
    R = py5.height * 0.35
    
    # Damping envelope
    env = 1.0 # No damping, continuous
    
    x = py5.width/2 + env * R * (np.sin(time_val * f1 + p1) + 0.5 * np.sin(time_val * f2 + p2))
    y = py5.height/2 + env * R * (np.cos(time_val * f3 + p3) + 0.5 * np.cos(time_val * f4 + p4))
    
    # Record history
    history[history_idx % HISTORY_SIZE] = [x, y]
    current_idx = history_idx
    history_idx += 1
    
    if history_idx > 1:
        # Draw lines connecting the new point to past points
        py5.begin_shape(py5.LINES)
        
        # We only look at points that have been populated
        valid_points = min(history_idx, HISTORY_SIZE)
        
        for i in range(valid_points):
            idx = (current_idx - i) % HISTORY_SIZE
            px, py = history[idx]
            
            # The older the point, the lower the alpha. 
            # We also modulate hue based on age to get a gradient web
            dist = i / HISTORY_SIZE
            
            # Only connect if we want a web
            # We connect to points that are at specific phase offsets to create geometric patterns
            if i % 15 == 0 or i % 45 == 0:
                hue = (280 + dist * 100 + time_val * 10) % 360
                alpha = 80 * (1.0 - dist)
                py5.stroke(hue, 90, 100, alpha)
                py5.stroke_weight(1.5)
                py5.vertex(x, y)
                py5.vertex(px, py)
                
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

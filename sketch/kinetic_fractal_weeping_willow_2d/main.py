from pathlib import Path
import shutil
import subprocess
import sys
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

MAX_DEPTH = 13

def branch(length, depth):
    if depth > MAX_DEPTH:
        return
        
    # Calculate a unique noise value for this depth and time
    # This creates a sweeping wind effect that travels up the tree
    time_offset = py5.frame_count * 0.015
    wind = py5.os_noise(depth * 0.5, time_offset) * 0.4
    
    # Base angle spreads branches apart
    base_angle = 0.4 + (depth * 0.02)
    
    # Weeping effect: branches tend to point downwards more at higher depths
    droop = depth * 0.05
    
    py5.stroke_weight(max(1.0, (MAX_DEPTH - depth) * 1.2))
    
    # Color: Trunk is dark, tips are bright weeping willow green/gold
    r = py5.remap(depth, 0, MAX_DEPTH, 20, 150)
    g = py5.remap(depth, 0, MAX_DEPTH, 30, 255)
    b = py5.remap(depth, 0, MAX_DEPTH, 40, 100)
    alpha = py5.remap(depth, 0, MAX_DEPTH, 255, 150)
    
    py5.stroke(r, g, b, alpha)
    py5.line(0, 0, 0, -length)
    py5.translate(0, -length)
    
    # Draw leaf at tip
    if depth > MAX_DEPTH - 3:
        py5.push_style()
        py5.no_stroke()
        py5.fill(180, 255, 100, 80)
        py5.circle(0, 0, 6 + (MAX_DEPTH - depth) * 2)
        py5.pop_style()
    
    # Right branch
    py5.push_matrix()
    py5.rotate(base_angle + wind + droop)
    branch(length * 0.76, depth + 1)
    py5.pop_matrix()
    
    # Left branch
    py5.push_matrix()
    py5.rotate(-base_angle + wind + droop)
    branch(length * 0.76, depth + 1)
    py5.pop_matrix()

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 15, 12)
    
    py5.blend_mode(py5.ADD)
    
    py5.push_matrix()
    # Move to bottom center of screen
    py5.translate(SIZE[0] / 2, SIZE[1])
    
    # Draw the recursive tree
    branch(400, 0)
    
    py5.pop_matrix()

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

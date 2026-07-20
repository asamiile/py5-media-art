from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_gear(x, y, r, num_teeth, angle, depth):
    if depth == 0 or r < 10:
        return
        
    py5.push_matrix()
    py5.translate(x, y)
    py5.rotate(angle)
    
    c_r = int(py5.remap(depth, 5, 0, 100, 255))
    c_g = int(py5.remap(depth, 5, 0, 50, 200))
    c_b = int(py5.remap(depth, 5, 0, 20, 100))
    alpha = 150
    
    py5.stroke(c_r, c_g, c_b, alpha)
    py5.stroke_weight(py5.remap(depth, 5, 0, 1, 5))
    py5.no_fill()
    py5.ellipse(0, 0, r * 2, r * 2)
    
    for i in range(4):
        py5.rotate(py5.HALF_PI)
        py5.line(0, 0, r, 0)
        
    teeth_h = r * 0.15
    for i in range(num_teeth):
        theta = py5.TWO_PI * i / num_teeth
        px1 = r * np.cos(theta)
        py1 = r * np.sin(theta)
        px2 = (r + teeth_h) * np.cos(theta)
        py2 = (r + teeth_h) * np.sin(theta)
        py5.line(px1, py1, px2, py2)
        
    py5.pop_matrix()
    
    num_children = 3
    child_r = r * 0.4
    child_teeth = int(num_teeth * 0.4)
    if child_teeth < 4: child_teeth = 4
    
    for i in range(num_children):
        theta = py5.TWO_PI * i / num_children + angle * (1 if depth % 2 == 0 else -1)
        dist = r + child_r + teeth_h
        cx = x + dist * np.cos(theta)
        cy = y + dist * np.sin(theta)
        
        child_angle = -angle * (r / child_r)
        
        draw_gear(cx, cy, child_r, child_teeth, child_angle, depth - 1)

def draw():
    py5.background(20, 25, 30)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    draw_gear(SIZE[0]/2, SIZE[1]/2, 500, 48, t, 6)

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

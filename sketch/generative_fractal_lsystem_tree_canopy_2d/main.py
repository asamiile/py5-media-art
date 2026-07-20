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
    
def draw_branch(len_branch, depth, max_depth, t):
    if depth == 0:
        return
        
    py5.stroke_weight(depth * 1.5)
    
    r = int(py5.remap(depth, max_depth, 0, 10, 100))
    g = int(py5.remap(depth, max_depth, 0, 200, 255))
    b = int(py5.remap(depth, max_depth, 0, 150, 255))
    alpha = int(py5.remap(depth, max_depth, 0, 150, 255))
    
    py5.stroke(r, g, b, alpha)
    py5.line(0, 0, 0, -len_branch)
    
    py5.translate(0, -len_branch)
    
    nx = py5.model_x(0, 0, 0) * 0.002
    ny = py5.model_y(0, 0, 0) * 0.002
    wind = (py5.os_noise(nx, ny, t) - 0.5) * py5.PI * 0.5
    
    angle = py5.PI / 6.0 + wind * (1.0 - depth/max_depth)
    
    py5.push_matrix()
    py5.rotate(angle)
    draw_branch(len_branch * 0.75, depth - 1, max_depth, t)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate(-angle + wind*0.5)
    draw_branch(len_branch * 0.7, depth - 1, max_depth, t)
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 20, 35, 100)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    num_trees = 5
    for i in range(num_trees):
        py5.push_matrix()
        x_pos = (i + 1) * SIZE[0] / (num_trees + 1)
        py5.translate(x_pos, SIZE[1] + 100)
        draw_branch(400, 11, 11, t + i * 10)
        py5.pop_matrix()

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

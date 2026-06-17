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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

MAX_DEPTH = 8

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def branch(length, depth, time_t):
    if depth == 0:
        return
        
    py5.stroke_weight(depth * 0.8)
    hue = (time_t * 30 + depth * 25) % 360
    py5.stroke(hue, 80, 100, 200)
    
    py5.line(0, 0, 0, 0, -length, 0)
    py5.translate(0, -length, 0)
    
    angle1 = 0.5 + 0.3 * np.sin(time_t + depth)
    angle2 = 0.6 + 0.2 * np.cos(time_t * 1.5 - depth)
    
    # Branch 1
    py5.push_matrix()
    py5.rotate_x(angle1)
    py5.rotate_y(angle2)
    branch(length * 0.7, depth - 1, time_t)
    py5.pop_matrix()
    
    # Branch 2
    py5.push_matrix()
    py5.rotate_x(-angle1)
    py5.rotate_y(-angle2)
    branch(length * 0.7, depth - 1, time_t)
    py5.pop_matrix()
    
    # Branch 3 (adds 3D volume)
    py5.push_matrix()
    py5.rotate_z(angle2)
    py5.rotate_y(angle1)
    branch(length * 0.7, depth - 1, time_t)
    py5.pop_matrix()
    
    # Branch 4 (adds 3D volume)
    py5.push_matrix()
    py5.rotate_z(-angle2)
    py5.rotate_y(-angle1)
    branch(length * 0.7, depth - 1, time_t)
    py5.pop_matrix()

def draw():
    py5.background(0)
    
    time_t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height, -200)
    
    cam_angle = time_t * 0.3
    py5.rotate_y(cam_angle)
    
    py5.blend_mode(py5.ADD)
    
    # Draw multiple roots for a denser structure
    for i in range(4):
        py5.push_matrix()
        py5.rotate_y(py5.HALF_PI * i)
        branch(300, MAX_DEPTH, time_t)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            sys.stdout.flush()
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

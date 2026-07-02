from pathlib import Path
import shutil
import subprocess
import sys
import math
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.sphere_detail(15)

def branch(len, depth, max_depth, time):
    if depth == 0:
        return
        
    py5.stroke(280, 50, 90, 200) # Amethyst / Chrome
    py5.stroke_weight(depth * 2)
    
    # Simulate liquid metal flow with spheres
    num_spheres = 5
    for i in range(num_spheres):
        t = (time * 5 + i / num_spheres + depth) % 1.0
        # Smooth step
        t = t * t * (3 - 2 * t)
        
        py5.push_matrix()
        py5.translate(0, -len * t, 0)
        py5.no_stroke()
        py5.fill(0, 0, 95, 255) # Silver
        py5.sphere(depth * 3 * py5.sin(t * py5.PI))
        py5.pop_matrix()
        
    py5.line(0, 0, 0, 0, -len, 0)
    
    py5.translate(0, -len, 0)
    
    # Branching angles animated by noise
    n_angle1 = (py5.noise(depth, time) - 0.5) * py5.PI
    n_angle2 = (py5.noise(depth + 10, time + 10) - 0.5) * py5.PI
    
    base_angle = py5.PI / 4
    
    py5.push_matrix()
    py5.rotate_z(base_angle + n_angle1)
    py5.rotate_x(n_angle2)
    branch(len * 0.7, depth - 1, max_depth, time)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate_z(-base_angle + n_angle2)
    py5.rotate_x(-n_angle1)
    branch(len * 0.7, depth - 1, max_depth, time)
    py5.pop_matrix()
    
    # 3D third branch
    py5.push_matrix()
    py5.rotate_x(base_angle + n_angle1)
    py5.rotate_y(n_angle2)
    branch(len * 0.6, depth - 1, max_depth, time)
    py5.pop_matrix()

def draw():
    py5.background(270, 90, 15) # Deep violet
    py5.ambient_light(280, 80, 40)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(280, 100, 100, -1, -1, 0)
    
    py5.translate(py5.width / 2, py5.height, -200)
    
    time = (py5.frame_count % TOTAL_FRAMES) / TOTAL_FRAMES
    
    py5.rotate_y(time * py5.TWO_PI)
    
    # Draw fractal tree
    branch(400, 7, 7, time)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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

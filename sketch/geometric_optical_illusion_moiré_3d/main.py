from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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

pts1 = []
pts2 = []

def generate_fibonacci_sphere(samples, radius):
    points = []
    phi = math.pi * (3.0 - math.sqrt(5.0))  # golden angle in radians
    
    for i in range(samples):
        y = 1 - (i / float(samples - 1)) * 2  # y goes from 1 to -1
        r = math.sqrt(1 - y * y)  # radius at y
        
        theta = phi * i  # golden angle increment
        
        x = math.cos(theta) * r
        z = math.sin(theta) * r
        
        points.append((x * radius, y * radius, z * radius))
    return points

def setup():
    global pts1, pts2
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    pts1 = generate_fibonacci_sphere(20000, 400)
    pts2 = generate_fibonacci_sphere(20000, 420)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    
    py5.stroke_weight(2)
    
    # Inner sphere
    py5.push_matrix()
    py5.rotate_y(t * 0.1)
    py5.rotate_x(t * 0.05)
    py5.stroke(200, 80, 100, 80)
    py5.begin_shape(py5.POINTS)
    for p in pts1:
        py5.vertex(*p)
    py5.end_shape()
    py5.pop_matrix()
    
    # Outer sphere
    py5.push_matrix()
    py5.rotate_y(-t * 0.12)
    py5.rotate_x(-t * 0.03)
    py5.stroke(300, 80, 100, 80)
    py5.begin_shape(py5.POINTS)
    for p in pts2:
        py5.vertex(*p)
    py5.end_shape()
    py5.pop_matrix()


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

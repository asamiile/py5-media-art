from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global stones
    stones = []
    for _ in range(6):
        stones.append({
            'x': random.uniform(-400, 400),
            'y': random.uniform(-400, 400),
            'r': random.uniform(30, 90)
        })

def draw():
    py5.background(40, 10, 90)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    cam_angle = py5.frame_count * 0.001
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(cam_angle)
    
    py5.directional_light(0, 0, 100, -1, 1, -1)
    py5.ambient_light(40, 10, 70)
    
    py5.no_stroke()
    py5.fill(40, 15, 85)
    
    res = 120
    size_box = 1600
    step = size_box / res
    
    time_val = py5.frame_count * 0.01
    
    for i in range(res):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(res + 1):
            for k in [0, 1]:
                xi = i + k
                yj = j
                if xi > res:
                    continue
                
                x = -size_box/2 + xi * step
                y = -size_box/2 + yj * step
                
                min_d = 9999
                for s in stones:
                    dx = x - s['x']
                    dy = y - s['y']
                    d = math.sqrt(dx*dx + dy*dy)
                    if d < min_d: min_d = d
                
                n = py5.os_noise(x * 0.003, y * 0.003, time_val * 0.2)
                ripple = math.sin((min_d + n * 100) * 0.15) * 8
                
                landscape = py5.os_noise(x * 0.002, y * 0.002) * 60
                
                z = ripple + landscape
                
                # Normal vectors for lighting (approximate)
                py5.normal(0, 0, 1)
                py5.vertex(x, y, z)
        py5.end_shape()
        
    py5.fill(0, 0, 15)
    py5.no_stroke()
    for s in stones:
        py5.push_matrix()
        # Find rough z height at stone pos
        lx = s['x']
        ly = s['y']
        landscape = py5.os_noise(lx * 0.002, ly * 0.002) * 60
        py5.translate(lx, ly, landscape + s['r'] * 0.3)
        py5.rotate_x(lx)
        py5.rotate_y(ly)
        py5.sphere_detail(20)
        py5.sphere(s['r'])
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
            
        import os
        os._exit(0)

py5.run_sketch()

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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)

def draw():
    py5.background(10, 5, 5)
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Global camera rotation
    py5.rotate_x(-math.pi / 6 + math.sin(t * math.pi * 2) * 0.2)
    py5.rotate_y(t * math.pi * 2)
    
    N = 12
    spacing = 60
    offset = (N - 1) * spacing / 2.0
    
    for x in range(N):
        for y in range(N):
            for z in range(N):
                px = x * spacing - offset
                py = y * spacing - offset
                pz = z * spacing - offset
                
                rx, ry, rz = px, py, pz
                
                # Twist around Y based on X slice
                angle_y = math.sin(t * math.pi * 4 + x * 0.3) * math.pi
                nx = rx * math.cos(angle_y) - rz * math.sin(angle_y)
                nz = rx * math.sin(angle_y) + rz * math.cos(angle_y)
                rx, rz = nx, nz
                
                # Twist around X based on Y slice
                angle_x = math.sin(t * math.pi * 4 + y * 0.3) * math.pi
                ny = ry * math.cos(angle_x) - rz * math.sin(angle_x)
                nz = ry * math.sin(angle_x) + rz * math.cos(angle_x)
                ry, rz = ny, nz
                
                py5.push_matrix()
                py5.translate(rx, ry, rz)
                
                # Box also rotates on its own
                py5.rotate_x(angle_x)
                py5.rotate_y(angle_y)
                
                dist_to_center = math.sqrt(rx*rx + ry*ry + rz*rz)
                intensity = py5.remap(dist_to_center, 0, offset*1.8, 255, 10)
                
                if intensity < 0: intensity = 0
                
                # Brass / Orange / Cyan palette
                col_r = 255
                col_g = 150 + 100 * math.sin(x * 0.5)
                col_b = 50 + 200 * math.cos(y * 0.5)
                
                py5.stroke(col_r, col_g, col_b, intensity)
                py5.box(spacing * 0.4)
                py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        import os
        os._exit(0)

py5.run_sketch()

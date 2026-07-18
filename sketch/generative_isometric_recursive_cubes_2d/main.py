from pathlib import Path
import shutil
import subprocess
import sys
import random
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

import math
ANGLE = math.pi / 6

def iso_project(x, y, z):
    px = (x - y) * math.cos(ANGLE)
    py = (x + y) * math.sin(ANGLE) - z
    return px, py

def draw_iso_cube(x, y, z, s, color_top, color_left, color_right):
    px, py = iso_project(x, y, z)
    
    p0x, p0y = iso_project(x, y, z + s)
    p1x, p1y = iso_project(x + s, y, z + s)
    p2x, p2y = iso_project(x + s, y, z)
    p3x, p3y = iso_project(x + s, y + s, z)
    p4x, p4y = iso_project(x, y + s, z)
    p5x, p5y = iso_project(x, y + s, z + s)
    pcx, pcy = iso_project(x + s, y + s, z + s)
    
    py5.no_stroke()
    
    py5.fill(*color_top)
    py5.begin_shape()
    py5.vertex(p0x, p0y)
    py5.vertex(p1x, p1y)
    py5.vertex(pcx, pcy)
    py5.vertex(p5x, p5y)
    py5.end_shape(py5.CLOSE)
    
    py5.fill(*color_left)
    py5.begin_shape()
    py5.vertex(p5x, p5y)
    py5.vertex(pcx, pcy)
    py5.vertex(p3x, p3y)
    py5.vertex(p4x, p4y)
    py5.end_shape(py5.CLOSE)
    
    py5.fill(*color_right)
    py5.begin_shape()
    py5.vertex(pcx, pcy)
    py5.vertex(p1x, p1y)
    py5.vertex(p2x, p2y)
    py5.vertex(p3x, p3y)
    py5.end_shape(py5.CLOSE)

def subdivide_cube(x, y, z, s, depth, max_depth, t):
    n = py5.os_noise(x * 0.003, y * 0.003, z * 0.003 + t)
    
    if depth < max_depth and n > 0.45:
        ns = s / 2
        for dz in (0, ns):
            for dy in (0, ns):
                for dx in (0, ns):
                    subdivide_cube(x + dx, y + dy, z + dz, ns, depth + 1, max_depth, t)
    else:
        if depth >= max_depth - 1 and n > 0.6:
            ct = (255, 50, 150)
            cl = (200, 20, 100)
            cr = (150, 10, 70)
        else:
            base = py5.remap(depth, 0, max_depth, 220, 80)
            ct = (base, base + 5, base + 10)
            cl = (base * 0.7, base * 0.7 + 5, base * 0.7 + 10)
            cr = (base * 0.4, base * 0.4 + 5, base * 0.4 + 10)
            
        draw_iso_cube(x, y, z, s, ct, cl, cr)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(20, 25, 30)
    
    py5.push_matrix()
    py5.translate(SIZE[0] / 2, SIZE[1] / 2 + 400)
    
    t = py5.frame_count * 0.01
    
    # Adjust depth bounds based on performance
    subdivide_cube(-500, -500, 0, 1000, 0, 4, t)
    
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

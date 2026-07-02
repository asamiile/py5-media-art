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

klein_shape = None

def klein_figure8(u, v):
    a = 3.0
    r = a + math.cos(u/2) * math.sin(v) - math.sin(u/2) * math.sin(2*v)
    x = r * math.cos(u)
    y = r * math.sin(u)
    z = math.sin(u/2) * math.sin(v) + math.cos(u/2) * math.sin(2*v)
    scale = 180.0
    return x * scale, y * scale, z * scale

def setup():
    global klein_shape
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    klein_shape = py5.create_shape()
    klein_shape.begin_shape(py5.QUADS)
    klein_shape.no_fill()
    klein_shape.stroke_weight(1)
    
    u_steps = 150
    v_steps = 80
    u_max = 2 * math.pi
    v_max = 2 * math.pi
    for i in range(u_steps):
        u1 = (i / u_steps) * u_max
        u2 = ((i + 1) / u_steps) * u_max
        for j in range(v_steps):
            v1 = (j / v_steps) * v_max
            v2 = ((j + 1) / v_steps) * v_max
            p1 = klein_figure8(u1, v1)
            p2 = klein_figure8(u2, v1)
            p3 = klein_figure8(u2, v2)
            p4 = klein_figure8(u1, v2)
            klein_shape.vertex(*p1)
            klein_shape.vertex(*p2)
            klein_shape.vertex(*p3)
            klein_shape.vertex(*p4)
    klein_shape.end_shape()

def draw():
    py5.background(5, 5, 8)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    rot_x = math.sin(t * math.pi * 2) * 0.5
    rot_y = t * math.pi * 4
    rot_z = math.cos(t * math.pi * 2) * 0.5
    
    py5.rotate_x(rot_x)
    py5.rotate_y(rot_y)
    py5.rotate_z(rot_z)
    
    # Red pass
    py5.push_matrix()
    py5.scale(1.0 + math.sin(t * math.pi * 2) * 0.02)
    klein_shape.set_stroke(py5.color(255, 40, 40, 100))
    py5.shape(klein_shape)
    py5.pop_matrix()
    
    # Green pass
    py5.push_matrix()
    py5.rotate_y(0.02)
    klein_shape.set_stroke(py5.color(40, 255, 40, 100))
    py5.shape(klein_shape)
    py5.pop_matrix()
    
    # Blue pass
    py5.push_matrix()
    py5.rotate_x(0.02)
    py5.scale(1.0 - math.sin(t * math.pi * 2) * 0.02)
    klein_shape.set_stroke(py5.color(40, 40, 255, 100))
    py5.shape(klein_shape)
    py5.pop_matrix()
    
    py5.blend_mode(py5.BLEND)

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

from pathlib import Path
import shutil
import subprocess
import sys
import math
import random
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
    py5.no_stroke()

def draw_gear(radius, teeth, t_offset, color_hue):
    py5.push_matrix()
    py5.rotate_z(t_offset)
    py5.fill(color_hue, 90, 100, 150)
    
    py5.begin_shape(py5.QUAD_STRIP)
    for i in range(teeth * 2 + 1):
        angle = py5.TWO_PI * i / (teeth * 2)
        r_outer = radius + (20 if i % 2 == 0 else -10)
        r_inner = radius - 40
        
        py5.vertex(r_inner * math.cos(angle), r_inner * math.sin(angle), 0)
        py5.vertex(r_outer * math.cos(angle), r_outer * math.sin(angle), 0)
    py5.end_shape()
    py5.pop_matrix()

def draw():
    py5.background(10, 100, 5) # Dark abyss
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    py5.rotate_x(py5.frame_count * 0.005)
    py5.rotate_y(py5.frame_count * 0.01)
    
    py5.blend_mode(py5.ADD)
    
    # Layered gears
    t = py5.frame_count * 0.02
    
    py5.push_matrix()
    py5.translate(0, 0, -100)
    draw_gear(300, 24, t, 180)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(0, 0, 0)
    draw_gear(200, 16, -t * 1.5, 320)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(0, 0, 100)
    draw_gear(100, 8, t * 2, 60)
    py5.pop_matrix()
    
    # Connective tissue (sparks)
    py5.stroke(200, 50, 100, 100)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.begin_shape(py5.LINES)
    for i in range(50):
        a1 = py5.random(py5.TWO_PI)
        a2 = py5.random(py5.TWO_PI)
        py5.vertex(300 * math.cos(a1), 300 * math.sin(a1), -100)
        py5.vertex(200 * math.cos(a2), 200 * math.sin(a2), 0)
    py5.end_shape()
    py5.no_stroke()
        
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

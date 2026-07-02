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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.ADD)
    py5.no_fill()

def draw_moire_circle(cx, cy, radius, num_lines, angle_offset, hue):
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(angle_offset)
    py5.stroke(hue, 80, 100, 180)
    py5.stroke_weight(2.0)
    for i in range(num_lines):
        r = radius * (i / num_lines)
        py5.circle(0, 0, r * 2)
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    cx1 = py5.width / 2 + np.sin(t) * 200
    cy1 = py5.height / 2 + np.cos(t * 0.8) * 200
    
    cx2 = py5.width / 2 + np.sin(t * 1.2) * 200
    cy2 = py5.height / 2 + np.cos(t * 1.5) * 200
    
    cx3 = py5.width / 2 + np.sin(t * 0.7) * 200
    cy3 = py5.height / 2 + np.cos(t * 1.1) * 200
    
    radius = py5.height * 0.8
    num_lines = 100
    
    draw_moire_circle(cx1, cy1, radius, num_lines, t, (t * 50) % 360)
    draw_moire_circle(cx2, cy2, radius, num_lines, -t * 1.5, (t * 50 + 120) % 360)
    draw_moire_circle(cx3, cy3, radius, num_lines, t * 2, (t * 50 + 240) % 360)

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
            
        import os
        os._exit(0)

py5.run_sketch()

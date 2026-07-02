from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw_hexagon(r):
    py5.begin_shape()
    for i in range(6):
        angle = py5.TWO_PI / 6 * i
        py5.vertex(py5.cos(angle) * r, py5.sin(angle) * r)
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(0, 0, 5)
    py5.no_fill()
    py5.stroke_weight(2)
    
    t = py5.frame_count * 0.005
    
    r = 80
    dx = r * 1.5
    dy = r * py5.sqrt(3)
    
    cols = int(py5.width / dx) + 4
    rows = int(py5.height / dy) + 4
    
    # Layer 1
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.rotate(t)
    py5.translate(-py5.width/2, -py5.height/2)
    
    for i in range(-2, cols):
        for j in range(-2, rows):
            x = i * dx
            y = j * dy
            if i % 2 != 0:
                y += dy / 2
            
            hue = (i * 10 + j * 10 + py5.frame_count) % 360
            py5.stroke(hue, 80, 100, 80)
            
            py5.push_matrix()
            py5.translate(x, y)
            draw_hexagon(r * 0.9)
            py5.pop_matrix()
    py5.pop_matrix()
    
    # Layer 2
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.rotate(-t * 1.5)
    py5.translate(-py5.width/2, -py5.height/2)
    
    for i in range(-2, cols):
        for j in range(-2, rows):
            x = i * dx
            y = j * dy
            if i % 2 != 0:
                y += dy / 2
                
            hue = (180 + i * 10 + j * 10 - py5.frame_count) % 360
            py5.stroke(hue, 80, 100, 80)
            
            py5.push_matrix()
            py5.translate(x, y)
            draw_hexagon(r * 0.9)
            py5.pop_matrix()
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
            
        import os
        os._exit(0)

py5.run_sketch()

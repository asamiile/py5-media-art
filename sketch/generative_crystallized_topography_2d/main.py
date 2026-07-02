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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 10)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.rect_mode(py5.CENTER)

def draw():
    # translucent fade for trails
    py5.no_stroke()
    py5.fill(10, 10, 10, 5)
    py5.rect(py5.width/2, py5.height/2, py5.width, py5.height)
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width/2, py5.height/2)
    
    # draw growing geometric crystal shards
    for i in range(15):
        angle = py5.os_noise(i, t * 0.5) * py5.TWO_PI * 4
        dist = py5.os_noise(i+100, t * 0.3) * (py5.width * 0.4)
        
        x = py5.cos(angle) * dist
        y = py5.sin(angle) * dist
        
        size = py5.os_noise(i+200, t) * 150
        
        hue = (120 + i * 15 + t * 20) % 360
        py5.stroke(hue, 80, 90, 40)
        py5.no_fill()
        py5.stroke_weight(2)
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(py5.os_noise(i+300, t) * py5.TWO_PI * 2)
        
        py5.triangle(-size/2, size/2, size/2, size/2, 0, -size/2)
        py5.pop_matrix()


    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

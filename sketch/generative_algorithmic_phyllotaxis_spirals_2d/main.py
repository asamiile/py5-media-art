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
    py5.background(10, 10, 10)
    py5.no_stroke()

def draw():
    # Motion blur
    py5.fill(10, 10, 10, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.5
    
    py5.translate(py5.width/2, py5.height/2)
    
    c = 25 # scaling factor
    
    # Draw new phyllotaxis points, multiple per frame to build the pattern quickly
    num_per_frame = 30
    for i in range(num_per_frame):
        n = py5.frame_count * num_per_frame + i
        angle = n * 137.5 * (py5.PI / 180) # golden angle
        r = c * py5.sqrt(n)
        
        # Animate the angle slightly over time for a twisting effect
        angle += t * 0.01 * (1 if n % 2 == 0 else -1)
        
        x = r * py5.cos(angle)
        y = r * py5.sin(angle)
        
        hue = (n * 0.1 + py5.frame_count * 2) % 360
        
        size = py5.remap(n, 0, TOTAL_FRAMES * num_per_frame, 2, 40)
        
        py5.fill(hue, 90, 100, 90)
        py5.circle(x, y, size)
        
        # Stop drawing if it reaches the edges
        if r > py5.width * 0.6:
            break

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

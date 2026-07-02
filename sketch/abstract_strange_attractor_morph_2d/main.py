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
    py5.color_mode(py5.RGB, 255)
    py5.background(0)

def draw():
    # Subtle fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    # Peter de Jong attractor parameters mutating over time
    a = 1.4 + math.sin(time * 0.7) * 0.3
    b = -2.3 + math.cos(time * 0.5) * 0.4
    c = 2.4 + math.sin(time * 0.3) * 0.5
    d = -2.1 + math.cos(time * 0.8) * 0.2
    
    x = 0.0
    y = 0.0
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.stroke(125, 249, 255, 30) # Electric blue
    py5.stroke_weight(1)
    
    iters = 200000 # High density particle drawing
    
    # Optimization using pre-computed scale
    scale_x = py5.width * 0.2
    scale_y = py5.height * 0.2
    
    for _ in range(iters):
        nx = math.sin(a * y) - math.cos(b * x)
        ny = math.sin(c * x) - math.cos(d * y)
        x = nx
        y = ny
        
        py5.point(x * scale_x, y * scale_y)
        
        # Adding a secondary color randomly
        if py5.random(1) < 0.1:
            py5.stroke(178, 0, 237, 50) # Purple
        else:
            py5.stroke(125, 249, 255, 30)

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

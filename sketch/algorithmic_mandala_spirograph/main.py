from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Keep trails by adding a black transparent box in front of camera
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2)
    
    num_petals = 12
    points_per_petal = 200
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Outer and inner radius parameters that evolve over time
    R = 400 + np.sin(time * 0.5) * 100
    r = 150 + np.cos(time * 0.7) * 50
    d = 200 + np.sin(time * 1.1) * 100
    
    for i in range(num_petals):
        py5.push_matrix()
        py5.rotate(i * py5.TWO_PI / num_petals + time * 0.1)
        
        py5.begin_shape(py5.LINE_STRIP)
        
        hue = (i * (360 / num_petals) + time * 50) % 360
        py5.stroke(hue, 90, 100, 30) 
            
        for t in range(points_per_petal):
            pt = t * 0.1 + time
            
            # Hypotrochoid equations
            x = (R - r) * np.cos(pt) + d * np.cos((R - r) / r * pt)
            y = (R - r) * np.sin(pt) - d * np.sin((R - r) / r * pt)
            
            py5.vertex(x, y)
            
        py5.end_shape()
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

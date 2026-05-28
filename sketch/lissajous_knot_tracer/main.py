from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from collections import deque

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

MAX_TRAIL = 200
trail = deque(maxlen=MAX_TRAIL)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.05
    
    # Calculate current point
    # Complex lissajous parameters
    a, b, c = 3, 2, 5
    A, B, C = 400, 400, 300
    
    x = A * np.sin(a * time) * np.cos(time * 0.2)
    y = B * np.sin(b * time + py5.PI/4) * np.sin(time * 0.3)
    z = C * np.cos(c * time)
    
    trail.append((x, y, z))
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_x(time * 0.1)
    py5.rotate_y(time * 0.15)
    
    py5.no_fill()
    py5.stroke_weight(4)
    
    # Draw trail
    if len(trail) > 1:
        py5.begin_shape()
        for i, (tx, ty, tz) in enumerate(trail):
            # Alpha fades out
            alpha = py5.remap(i, 0, len(trail), 0, 100)
            hue = (time * 20 + i) % 360
            
            py5.stroke(hue, 90, 100, alpha)
            py5.vertex(tx, ty, tz)
        py5.end_shape()
        
        # Draw glowing outer shell
        py5.stroke_weight(15)
        py5.begin_shape()
        for i, (tx, ty, tz) in enumerate(trail):
            alpha = py5.remap(i, 0, len(trail), 0, 30)
            hue = (time * 20 + i) % 360
            py5.stroke(hue, 90, 100, alpha)
            py5.vertex(tx, ty, tz)
        py5.end_shape()

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

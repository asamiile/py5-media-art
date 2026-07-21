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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_POINTS = 1200
t_array = np.linspace(0, np.pi * 2, NUM_POINTS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5, 5, 10)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.blend_mode(py5.ADD)
    
    # Phase shifts that animate over time
    time = py5.frame_count * 0.015
    delta1 = time * 1.5
    delta2 = time * 0.8
    
    # Complex Lissajous parameters
    a, b = 5, 4
    c, d = 3, 7
    
    R = SIZE[1] * 0.45
    
    # Generate points
    x = np.sin(a * t_array + delta1) * np.cos(c * t_array) * R * (SIZE[0]/SIZE[1])
    y = np.sin(b * t_array + delta2) * np.cos(d * t_array) * R
    
    pts = np.column_stack((x, y))
    
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # String art connection offsets
    offsets = [1, 20, 50, 150, 400]
    colors = [
        (255, 255, 255, 150),
        (0, 200, 255, 80),
        (255, 50, 100, 60),
        (100, 50, 255, 40),
        (255, 150, 0, 30)
    ]
    
    for k, color in zip(offsets, colors):
        py5.stroke(*color)
        py5.begin_shape(py5.LINES)
        for i in range(NUM_POINTS):
            p1 = pts[i]
            p2 = pts[(i + k) % NUM_POINTS]
            py5.vertex(p1[0], p1[1])
            py5.vertex(p2[0], p2[1])
        py5.end_shape()

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

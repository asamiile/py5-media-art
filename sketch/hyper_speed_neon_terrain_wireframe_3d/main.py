from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols = 0
rows = 0
scl = 40
w = 3000
h = 2500
terrain = []

def setup():
    global cols, rows, terrain
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    cols = w // scl
    rows = h // scl
    terrain = [[0 for _ in range(rows)] for _ in range(cols)]

def draw():
    global terrain
    py5.background(10, 100, 5) # Dark abyss
    
    flying = py5.frame_count * 0.1
    
    # Calculate terrain heights
    yoff = flying
    for y in range(rows):
        xoff = 0
        for x in range(cols):
            terrain[x][y] = py5.remap(py5.noise(xoff, yoff), 0, 1, -200, 300)
            xoff += 0.1
        yoff += 0.1
        
    py5.translate(py5.width / 2, py5.height / 2 + 100, -200)
    py5.rotate_x(py5.PI / 3)
    py5.translate(-w / 2, -h / 2, 0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw terrain mesh
    for y in range(rows - 1):
        # Calculate color based on depth
        hue = (10 + py5.frame_count * 0.5 + y * 2) % 360 # Orange/Red shifting
        alpha = py5.remap(y, 0, rows, 0, 255)
        
        py5.stroke(hue, 90, 100, alpha * 0.6)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            py5.vertex(x * scl, y * scl, terrain[x][y])
            py5.vertex(x * scl, (y + 1) * scl, terrain[x][y + 1])
        py5.end_shape()
        
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

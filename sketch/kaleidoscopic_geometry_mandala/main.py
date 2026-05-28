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

def polygon(x, y, radius, npoints):
    angle = py5.TWO_PI / npoints
    py5.begin_shape()
    for a in np.arange(0, py5.TWO_PI, angle):
        sx = x + np.cos(a) * radius
        sy = y + np.sin(a) * radius
        py5.vertex(sx, sy)
    py5.end_shape(py5.CLOSE)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2)
    
    num_layers = 12
    num_shapes_per_layer = 6
    
    for i in range(num_layers):
        py5.push_matrix()
        
        # Rotate the entire layer
        py5.rotate(time * 0.1 * (1 if i % 2 == 0 else -1) + i * 0.1)
        
        # Calculate dynamic radius and size
        radius = 100 + i * 80 + np.sin(time * 0.5 + i) * 50
        shape_size = 50 + i * 20 + np.sin(time * 0.8 + i) * 30
        
        for j in range(num_shapes_per_layer):
            angle = j * py5.TWO_PI / num_shapes_per_layer
            
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            
            py5.push_matrix()
            py5.translate(x, y)
            
            # Rotate individual shape
            py5.rotate(time * 1.5 + j)
            
            # Color
            hue = (time * 10 + i * 30 + j * 10) % 360
            py5.stroke(hue, 90, 100, 60)
            py5.stroke_weight(3)
            py5.no_fill()
            
            # Alternate shape types
            sides = 3 if i % 3 == 0 else (4 if i % 3 == 1 else 6)
            
            polygon(0, 0, shape_size, sides)
            
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

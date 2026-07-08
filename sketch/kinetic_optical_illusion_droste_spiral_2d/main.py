from pathlib import Path
import shutil
import subprocess
import sys
import math
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

SCALE_FACTOR = 0.85
NUM_LAYERS = 90
NUM_SIDES = 6

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    py5.background(10)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = (py5.frame_count % TOTAL_FRAMES) / TOTAL_FRAMES
    
    zoom = math.pow(1.0 / SCALE_FACTOR, t)
    
    base_rotation = t * (py5.TWO_PI / NUM_SIDES)
    
    py5.scale(zoom)
    py5.rotate(base_rotation)
    
    base_radius = max(SIZE) * 2.0
    
    for i in range(NUM_LAYERS):
        layer_scale = math.pow(SCALE_FACTOR, i)
        
        offset = i - t 
        
        layer_rotation = math.sin(offset * 0.15) * 0.6
        
        py5.push_matrix()
        py5.scale(layer_scale)
        py5.rotate(layer_rotation)
        
        if i % 2 == 0:
            py5.fill(10, 100)
        else:
            py5.fill(90, 100)
            
        hue = (t * 360 + i * 15) % 360
        py5.stroke(hue, 80, 100)
        py5.stroke_weight(3 / layer_scale) 
        
        py5.begin_shape()
        for j in range(NUM_SIDES):
            angle = j * py5.TWO_PI / NUM_SIDES
            
            tx = math.cos(t * py5.TWO_PI)
            ty = math.sin(t * py5.TWO_PI)
            
            n_val = py5.noise(
                math.cos(angle) * 1.5 + tx * 0.5,
                math.sin(angle) * 1.5 + ty * 0.5,
                i * 0.15
            )
            
            r = base_radius + py5.remap(n_val, 0, 1, -base_radius * 0.15, base_radius * 0.15)
            
            x = math.cos(angle) * r
            y = math.sin(angle) * r
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)
        
        py5.pop_matrix()

    py5.color_mode(py5.RGB, 255)

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

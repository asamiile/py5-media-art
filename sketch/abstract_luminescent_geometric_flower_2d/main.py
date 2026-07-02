from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 5, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    time_val = py5.frame_count * 0.02
    
    num_layers = 10
    
    for j in range(num_layers):
        layer_scale = py5.remap(j, 0, num_layers, 0.2, 1.5)
        # Each layer rotates slightly differently
        py5.rotate(time_val * 0.1 * (1 if j % 2 == 0 else -1))
        
        hue = (time_val * 50 + j * 36) % 360
        py5.stroke(hue, 80, 100, 150)
        py5.no_fill()
        py5.stroke_weight(2)
        
        py5.begin_shape()
        num_points = 200
        for i in range(num_points + 3): # +3 to loop smoothly with curve_vertex
            # To make it a closed loop, modulo the index
            idx = i % num_points
            angle = py5.TWO_PI * idx / num_points
            
            # The 'petals' math
            # Modulate the radius with a sine wave of the angle
            base_radius = SIZE[1] * 0.3 * layer_scale
            petal_freq = 5 + j # Number of petals varies by layer
            
            radius_mod = py5.sin(angle * petal_freq + time_val) * (SIZE[1] * 0.1 * layer_scale)
            r = base_radius + radius_mod
            
            x = py5.cos(angle) * r
            y = py5.sin(angle) * r
            py5.curve_vertex(x, y)
            
        py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_LAYERS = 30

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw_layer(i, time_t):
    # Determine base parameters for this layer
    radius = (NUM_LAYERS - i) * (py5.width / (2.5 * NUM_LAYERS))
    sides = 3 + (i % 6)
    
    # Alternating rotation direction
    direction = 1 if i % 2 == 0 else -1
    rotation = direction * time_t * (0.5 + i * 0.05)
    
    # Breathing scale
    scale = 1.0 + 0.15 * np.sin(time_t * 2 + i * 0.5)
    
    # Thickness pulses
    weight = 2 + 10 * (0.5 + 0.5 * np.sin(time_t * 5 - i))
    
    # Hue shifting
    hue = (time_t * 50 + i * 15) % 360
    
    py5.push_matrix()
    py5.rotate(rotation)
    py5.scale(scale)
    
    py5.stroke(hue, 90, 100, 200)
    py5.stroke_weight(weight)
    py5.no_fill()
    
    # Draw polygon
    py5.begin_shape()
    for j in range(sides):
        angle = py5.TWO_PI * j / sides
        py5.vertex(radius * np.cos(angle), radius * np.sin(angle))
    py5.end_shape(py5.CLOSE)
    
    # Draw connecting lines to center for inner layers to add complexity
    if i > NUM_LAYERS // 2:
        for j in range(sides):
            angle = py5.TWO_PI * j / sides
            py5.line(0, 0, radius * np.cos(angle), radius * np.sin(angle))
            
    py5.pop_matrix()

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 80)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    time_t = py5.frame_count * 0.02
    
    for i in range(NUM_LAYERS):
        draw_layer(i, time_t)

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

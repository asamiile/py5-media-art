from pathlib import Path
import shutil
import subprocess
import sys
import random
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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_shard(x, y, r, sides, angle_offset, c):
    py5.fill(c)
    py5.begin_shape()
    for i in range(sides):
        angle = angle_offset + py5.TWO_PI / sides * i
        # slight deformation
        r_mod = r * (0.8 + 0.4 * py5.noise(i, py5.frame_count * 0.01))
        py5.vertex(x + py5.cos(angle) * r_mod, y + py5.sin(angle) * r_mod)
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(0, 0, 0)
    # Additive blending
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    t = py5.frame_count * 0.005
    cx, cy = py5.width / 2, py5.height / 2
    
    layers = 8
    segments = 12
    
    # Base chromatic colors
    colors = [
        py5.color(255, 0, 0),   # Red
        py5.color(0, 255, 0),   # Green
        py5.color(0, 0, 255)    # Blue
    ]
    
    for l in range(layers):
        radius = py5.remap(l, 0, layers, py5.width * 0.1, py5.width * 0.8)
        base_angle = t * (1 if l % 2 == 0 else -1) * (1.0 - l * 0.1)
        
        for s in range(segments):
            angle = base_angle + py5.TWO_PI / segments * s
            
            x = cx + py5.cos(angle) * radius
            y = cy + py5.sin(angle) * radius
            
            # Draw each RGB channel slightly offset based on distance from center (chromatic aberration)
            aberration_amount = radius * 0.02 * py5.sin(t * 5 + l)
            
            for i, c in enumerate(colors):
                offset_x = py5.cos(angle) * aberration_amount * (i - 1)
                offset_y = py5.sin(angle) * aberration_amount * (i - 1)
                
                # Shape size oscillates
                shape_r = (py5.width * 0.05) + (py5.width * 0.02 * py5.sin(t * 10 + s))
                
                py5.push_matrix()
                py5.translate(x + offset_x, y + offset_y)
                py5.rotate(angle * 2)
                draw_shard(0, 0, shape_r, 3, t * 2, c)
                py5.pop_matrix()
                
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
            
        import os
        os._exit(0)

py5.run_sketch()

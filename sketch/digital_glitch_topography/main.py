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

cols, rows = 0, 0
scl = 40
w = 3000
h = 3000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl

def draw_terrain(channel_color, x_offset):
    py5.push_matrix()
    py5.translate(x_offset, 0, 0)
    py5.stroke(*channel_color)
    py5.no_fill()
    py5.stroke_weight(2)
    
    time_offset = py5.frame_count * 0.1
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            for dy in (0, 1):
                cy = y + dy
                # Low frequency noise for hills
                low_noise = py5.os_noise(x * 0.05, cy * 0.05 - time_offset)
                # High frequency noise for glitch spikes
                high_noise = py5.os_noise(x * 0.5, cy * 0.5 - time_offset * 2)
                
                z = py5.remap(low_noise, 0, 1, -200, 200)
                
                # Apply glitch threshold
                if high_noise > 0.85:
                    z += py5.remap(high_noise, 0.85, 1.0, 0, 800)
                
                px = x * scl - w / 2
                py = cy * scl - h / 2
                py5.vertex(px, py, z)
        py5.end_shape()
        
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2 + 200, -500)
    py5.rotate_x(py5.PI / 3)
    
    # Red, Green, Blue with slight offsets for chromatic aberration
    aberration = 15
    draw_terrain((255, 0, 0), -aberration)
    draw_terrain((0, 255, 0), 0)
    draw_terrain((0, 0, 255), aberration)
    
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
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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

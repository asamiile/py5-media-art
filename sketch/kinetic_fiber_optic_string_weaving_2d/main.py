from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import time
import glob
from PIL import Image

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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = PREVIEW_SIZE # Render internally at 1080p to avoid GC thrashing

# Weaving parameters
NUM_LINES = 3000
I_ARRAY = np.arange(NUM_LINES)

def setup():
    py5.size(OUTPUT_SIZE[0], OUTPUT_SIZE[1])
    py5.no_smooth()
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_fill()
    py5.stroke_weight(2)

coords = np.empty((NUM_LINES * 2, 2), dtype=np.float32)
white_lines = 500
coords_w = np.empty((white_lines * 2, 2), dtype=np.float32)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 16, 80) # Deep indigo trail, #050510 approx, with alpha
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    for struct_id in range(2):
        if struct_id == 0:
            color = (0, 255, 255, 40) # Neon Cyan
            time_offset_mult = 0.003
            a1 = 3 + np.sin(t * 0.2) * 0.5
            b1 = 2
            a2 = 2
            b2 = 3 + np.cos(t * 0.15) * 0.5
            rad_x = py5.width * 0.4
            rad_y = py5.height * 0.4
        else:
            color = (255, 0, 255, 40) # Electric Magenta
            time_offset_mult = 0.004
            a1 = 4 + np.cos(t * 0.25) * 0.5
            b1 = 3
            a2 = 3
            b2 = 4 + np.sin(t * 0.1) * 0.5
            rad_x = py5.width * 0.35
            rad_y = py5.height * 0.45

        time_array = t - I_ARRAY * time_offset_mult
        
        x1 = py5.width / 2 + rad_x * np.sin(a1 * time_array + np.pi/2)
        y1 = py5.height / 2 + rad_y * np.sin(b1 * time_array)
        
        x2 = py5.width / 2 + rad_x * np.sin(a2 * time_array)
        y2 = py5.height / 2 + rad_y * np.sin(b2 * time_array + np.pi/4)
        
        coords[0::2, 0] = x1
        coords[0::2, 1] = y1
        coords[1::2, 0] = x2
        coords[1::2, 1] = y2
        
        py5.stroke(*color)
        py5.begin_shape(py5.LINES)
        py5.vertices(coords)
        py5.end_shape()

    white_lines = 500
    time_array_w = t - np.arange(white_lines) * 0.005
    aw, bw = 5, 4
    x1w = py5.width / 2 + py5.width * 0.4 * np.sin(aw * time_array_w)
    y1w = py5.height / 2 + py5.height * 0.4 * np.cos(bw * time_array_w)
    x2w = py5.width / 2 + py5.width * 0.2 * np.sin(bw * time_array_w)
    y2w = py5.height / 2 + py5.height * 0.2 * np.cos(aw * time_array_w)
    
    coords_w[0::2, 0] = x1w
    coords_w[0::2, 1] = y1w
    coords_w[1::2, 0] = x2w
    coords_w[1::2, 1] = y2w
    
    py5.stroke(255, 255, 255, 100) # Bright White
    py5.begin_shape(py5.LINES)
    py5.vertices(coords_w)
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.tif"))

    print(f"Finished frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.tif"),
            "-vf", "scale=3840:2160",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4")
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.tif")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

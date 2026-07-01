from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_pattern(x, y, radius, num_lines):
    # Vectorized calculation for the pattern
    angles = np.linspace(0, py5.TWO_PI, num_lines, endpoint=False)
    x_coords = x + radius * np.cos(angles)
    y_coords = y + radius * np.sin(angles)
    
    verts = np.empty((num_lines * 2, 2))
    verts[0::2, 0] = x
    verts[0::2, 1] = y
    verts[1::2, 0] = x_coords
    verts[1::2, 1] = y_coords
    
    py5.begin_shape(py5.LINES)
    py5.vertices(verts)
    py5.end_shape()

def draw():
    py5.background(255)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    cx, cy = py5.width / 2, py5.height / 2
    r = py5.width * 0.8
    n_lines = 400
    
    # Layer 1 (Static but changing color)
    # Background color cycle
    py5.stroke(np.interp(np.sin(t * py5.TWO_PI), [-1, 1], [0, 100]), 
               np.interp(np.cos(t * py5.TWO_PI), [-1, 1], [0, 50]), 
               np.interp(np.sin(t * py5.TWO_PI * 1.5), [-1, 1], [50, 150]), 255)
    py5.stroke_weight(py5.width * 0.001)
    draw_pattern(cx, cy, r, n_lines)
    
    # Layer 2 (Rotating and translating)
    py5.push_matrix()
    
    # Translation creates the Moiré effect
    offset_x = np.sin(t * py5.TWO_PI) * (py5.width * 0.05)
    offset_y = np.cos(t * py5.TWO_PI * 2) * (py5.height * 0.05)
    py5.translate(offset_x, offset_y)
    
    # Rotation also adds to the Moiré effect
    rot = np.sin(t * py5.TWO_PI) * py5.PI * 0.02
    py5.translate(cx, cy)
    py5.rotate(rot)
    py5.translate(-cx, -cy)
    
    py5.stroke(0)
    draw_pattern(cx, cy, r, n_lines)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

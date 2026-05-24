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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_radial_grid(num_circles, max_radius):
    for i in range(num_circles):
        r = (i + 1) * max_radius / num_circles
        py5.circle(0, 0, r * 2)

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    # We use 3 overlapping, highly dense grids to create the moiré effect.
    # The grids will translate and rotate slightly.
    
    max_radius = py5.width * 1.5
    num_circles = 100
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Layer 1: Base layer (fixed)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    py5.stroke(200, 80, 80, 70)
    draw_radial_grid(num_circles, max_radius)
    py5.pop_matrix()
    
    # Layer 2: Moving layer (orbits slowly)
    py5.push_matrix()
    offset_x = py5.sin(t * 0.5) * 50
    offset_y = py5.cos(t * 0.5) * 50
    py5.translate(py5.width / 2 + offset_x, py5.height / 2 + offset_y)
    py5.stroke(320, 80, 80, 70)
    draw_radial_grid(num_circles, max_radius)
    py5.pop_matrix()
    
    # Layer 3: Expanding/contracting layer
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    scale_factor = 1.0 + py5.sin(t) * 0.05
    py5.scale(scale_factor)
    py5.stroke(60, 80, 80, 70)
    draw_radial_grid(num_circles, max_radius)
    py5.pop_matrix()
    
    # Layer 4: Linear grating for intense interference
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    py5.rotate(py5.sin(t * 0.2) * py5.PI / 8)
    py5.stroke(0, 0, 100, 50)
    py5.stroke_weight(1.5)
    for i in range(-py5.width, py5.width, 15):
        py5.line(i, -py5.height, i, py5.height)
    py5.pop_matrix()

    # Add a vignette overlay for mood
    py5.no_stroke()
    for r in range(min(py5.width, py5.height) // 2, max(py5.width, py5.height), 20):
        alpha = py5.remap(r, min(py5.width, py5.height) // 2, max(py5.width, py5.height), 0, 80)
        py5.fill(0, 0, 0, alpha)
        py5.circle(py5.width / 2, py5.height / 2, r * 2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

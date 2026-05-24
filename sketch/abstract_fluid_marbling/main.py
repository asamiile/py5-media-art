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

NUM_LINES = 120
POINTS_PER_LINE = 400

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    py5.no_fill()
    py5.stroke_weight(2.5)
    
    t = py5.frame_count * 0.015
    
    # We draw horizontal lines, but deeply deform them
    spacing_y = py5.height / NUM_LINES
    step_x = py5.width / POINTS_PER_LINE
    
    for i in range(NUM_LINES):
        base_y = i * spacing_y
        
        # Color gradient down the screen
        hue = (i / NUM_LINES * 120 + t * 40 + 200) % 360
        py5.stroke(hue, 80, 90, 80)
        
        py5.begin_shape()
        for j in range(POINTS_PER_LINE + 1):
            base_x = j * step_x
            
            # Fluid deformation math
            # Using overlapping sine waves driven by spatial coordinates and time
            # to simulate the swirling eddies of Suminagashi marbling.
            
            nx = base_x * 0.003
            ny = base_y * 0.003
            
            # Eddy 1
            angle1 = py5.noise(nx, ny, t) * py5.TWO_PI * 4
            dx1 = py5.cos(angle1) * 60
            dy1 = py5.sin(angle1) * 60
            
            # Eddy 2 (higher frequency)
            angle2 = py5.noise(nx * 3 + 100, ny * 3 + 100, t * 1.5) * py5.TWO_PI * 2
            dx2 = py5.cos(angle2) * 20
            dy2 = py5.sin(angle2) * 20
            
            # Eddy 3 (global drift)
            dy3 = py5.sin(nx * 5 + t) * 30
            
            final_x = base_x + dx1 + dx2
            final_y = base_y + dy1 + dy2 + dy3
            
            py5.vertex(final_x, final_y)
            
        py5.end_shape()

    # Add a vignette overlay for mood
    py5.no_stroke()
    for r in range(min(py5.width, py5.height) // 2, max(py5.width, py5.height), 20):
        alpha = py5.remap(r, min(py5.width, py5.height) // 2, max(py5.width, py5.height), 0, 50)
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

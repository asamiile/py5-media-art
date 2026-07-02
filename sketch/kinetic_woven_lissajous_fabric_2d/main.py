from pathlib import Path
import shutil
import subprocess
import sys
import math
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_CURVES = 100
POINTS_PER_CURVE = 400

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5, 5, 16)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    t = py5.frame_count * 0.005
    
    cx = py5.width / 2
    cy = py5.height / 2
    max_r = min(py5.width, py5.height) * 0.4
    
    for i in range(NUM_CURVES):
        # Calculate base frequencies for this curve
        # Shift slightly across the population to create the woven moire effect
        base_fx = 3.0 + i * 0.01 + math.sin(t * 0.5) * 0.5
        base_fy = 2.0 + i * 0.015 + math.cos(t * 0.4) * 0.5
        
        # Color mapping: Cyan to Magenta based on index
        ratio = i / NUM_CURVES
        r = int(py5.lerp(0, 255, ratio))
        g = int(py5.lerp(255, 0, ratio))
        b = 255
        
        # Add slight pulse to alpha
        alpha = 40 + math.sin(t * 10 + i * 0.1) * 20
        py5.stroke(r, g, b, alpha)
        
        py5.begin_shape()
        for j in range(POINTS_PER_CURVE):
            # Inner time loop to draw the full curve
            tt = j * 0.02 + t
            
            # Parametric Lissajous with drifting phase
            x = cx + math.sin(tt * base_fx) * max_r * math.cos(tt * 0.1)
            y = cy + math.sin(tt * base_fy + math.pi/2) * max_r * math.sin(tt * 0.15)
            
            py5.vertex(x, y)
        py5.end_shape()
        
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

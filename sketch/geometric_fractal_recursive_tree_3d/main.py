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

MAX_DEPTH = 11

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(len, depth, t):
    if depth == 0:
        return
        
    # Stroke weight thinner as it goes up
    sw = py5.remap(depth, 1, MAX_DEPTH, 0.5, 8.0)
    py5.stroke_weight(sw)
    
    # Color changes from trunk (brown/purple) to leaves (neon cyan/pink)
    hue = py5.remap(depth, 1, MAX_DEPTH, 200, 280) + t * 20
    py5.stroke(hue % 360, 80, 100)
    
    # Draw the branch
    py5.line(0, 0, 0, 0, -len, 0)
    
    # Move to the end of the branch
    py5.translate(0, -len, 0)
    
    # Add wind (noise) that affects thinner branches more
    wind_x = py5.noise(depth * 0.1, t * 1.5) * 0.4 - 0.2
    wind_z = py5.noise(depth * 0.1 + 100, t * 1.5) * 0.4 - 0.2
    
    # Growth animation: branches slowly expand and contract slightly
    growth = py5.sin(t * 2.0 + depth * 0.5) * 0.1 + 0.9
    
    # Right branch
    py5.push_matrix()
    py5.rotate_x(0.3 + wind_x)
    py5.rotate_z(0.4 + wind_z)
    py5.rotate_y(t * 0.5) # Spiral growth
    draw_branch(len * 0.72 * growth, depth - 1, t)
    py5.pop_matrix()
    
    # Left branch
    py5.push_matrix()
    py5.rotate_x(-0.2 + wind_x)
    py5.rotate_z(-0.5 + wind_z)
    py5.rotate_y(-t * 0.3)
    draw_branch(len * 0.68 * growth, depth - 1, t)
    py5.pop_matrix()
    
    # Sometimes add a 3rd branch in 3D
    if depth > 4:
        py5.push_matrix()
        py5.rotate_x(-0.4 + wind_x)
        py5.rotate_z(0.1 + wind_z)
        py5.rotate_y(py5.PI / 2 + t * 0.4)
        draw_branch(len * 0.6 * growth, depth - 1, t)
        py5.pop_matrix()

def draw():
    py5.background(10, 15, 25)
    
    t = py5.frame_count * 0.02
    
    # Setup camera
    py5.translate(py5.width / 2, py5.height - 100, -300)
    
    # Slowly orbit around the tree
    py5.rotate_y(t * 0.3)
    # Tilt down slightly
    py5.rotate_x(-0.2)
    
    # Draw the fractal tree
    draw_branch(280, MAX_DEPTH, t)

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

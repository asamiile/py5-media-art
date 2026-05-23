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

COLS, ROWS = 150, 150
GRID_SPACING = 8

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.05
    
    # 3 moving wave sources (emitters)
    sources = [
        (py5.width/2 + py5.cos(t*0.5)*300, py5.height/2 + py5.sin(t*0.3)*300),
        (py5.width/2 + py5.cos(t*0.2 + py5.PI)*200, py5.height/2 + py5.sin(t*0.7)*400),
        (py5.width/2 + py5.sin(t*0.4)*250, py5.height/2 + py5.cos(t*0.6 + py5.PI/2)*250)
    ]
    
    # Camera setup to look down at an angle
    py5.translate(py5.width / 2, py5.height / 2 + 100, -200)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.1)
    
    # Center the grid
    py5.translate(-COLS * GRID_SPACING / 2, -ROWS * GRID_SPACING / 2)
    
    # We will draw points to represent the quantum wave field
    py5.stroke_weight(4)
    py5.begin_shape(py5.POINTS)
    
    for y in range(ROWS):
        for x in range(COLS):
            world_x = x * GRID_SPACING
            world_y = y * GRID_SPACING
            
            # Absolute position relative to original un-translated canvas for distance calculation
            abs_x = py5.width/2 - COLS*GRID_SPACING/2 + world_x
            abs_y = py5.height/2 - ROWS*GRID_SPACING/2 + world_y
            
            total_wave = 0
            for sx, sy in sources:
                d = py5.dist(abs_x, abs_y, sx, sy)
                # Sine wave rippling outward from the source
                total_wave += py5.sin(d * 0.05 - t * 2.0)
                
            # The resulting height is the interference of the waves
            z = total_wave * 40
            
            # Color is based on the amplitude of the interference
            hue = (total_wave * 40 + t * 20 + 200) % 360
            py5.stroke(hue, 90, 100, 90)
            
            py5.vertex(world_x, world_y, z)
            
    py5.end_shape()

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

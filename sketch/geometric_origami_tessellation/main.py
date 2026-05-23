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

COLS = 30
ROWS = 30
CELL_SIZE = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    # Lighting setup to emphasize origami folds
    py5.ambient_light(40, 40, 40)
    py5.directional_light(200, 10, 100, 1, 1, -1)
    py5.directional_light(255, 20, 80, -1, 0.5, -0.5)
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    # Slow rotation to view the tessellation from different angles
    py5.rotate_x(py5.PI / 3 + py5.sin(t * 0.3) * 0.2)
    py5.rotate_z(t * 0.2)
    
    # Center the grid
    py5.translate(-COLS * CELL_SIZE / 2, -ROWS * CELL_SIZE / 2, 0)
    
    # Fold angle theta oscillates between nearly flat and highly folded
    theta_base = py5.remap(py5.sin(t * 0.5), -1, 1, 0.1, 1.2)
    
    py5.stroke(0, 0, 100, 20)
    py5.stroke_weight(1)
    
    # We will draw the Miura-ori style fold using QUAD_STRIP
    # The grid alternates Z heights to create folds
    for y in range(ROWS - 1):
        py5.begin_shape(py5.QUAD_STRIP)
        for x in range(COLS):
            # Calculate dynamic folding parameters for current vertex
            # Adding noise to the fold angle to make it organic like crumpling paper
            noise_val1 = py5.noise(x * 0.1, y * 0.1, t * 0.5)
            theta1 = theta_base * (0.5 + noise_val1)
            
            noise_val2 = py5.noise(x * 0.1, (y + 1) * 0.1, t * 0.5)
            theta2 = theta_base * (0.5 + noise_val2)
            
            # X coordinate shrinks as it folds (accordion effect)
            px1 = x * CELL_SIZE * py5.cos(theta1)
            py1 = y * CELL_SIZE
            # Z alternates based on checkerboard pattern
            z_dir1 = 1 if (x + y) % 2 == 0 else -1
            pz1 = CELL_SIZE * py5.sin(theta1) * z_dir1
            
            px2 = x * CELL_SIZE * py5.cos(theta2)
            py2 = (y + 1) * CELL_SIZE
            z_dir2 = 1 if (x + y + 1) % 2 == 0 else -1
            pz2 = CELL_SIZE * py5.sin(theta2) * z_dir2
            
            # Dynamic coloring based on Z height (like iridescent paper)
            hue1 = (py5.remap(pz1, -CELL_SIZE, CELL_SIZE, 180, 300) + t * 20) % 360
            py5.fill(hue1, 70, 90)
            py5.vertex(px1, py1, pz1)
            
            hue2 = (py5.remap(pz2, -CELL_SIZE, CELL_SIZE, 180, 300) + t * 20) % 360
            py5.fill(hue2, 70, 90)
            py5.vertex(px2, py2, pz2)
            
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

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

# City Grid Parameters
GRID_SIZE = 35
CELL_SIZE = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.015
    
    # Orthographic projection for pure isometric feel
    py5.ortho(-py5.width/2, py5.width/2, -py5.height/2, py5.height/2, -2000, 2000)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Isometric rotations
    py5.rotate_x(-py5.asin(1 / py5.sqrt(3)))
    py5.rotate_y(py5.PI / 4 + t * 0.2)
    
    # Lighting setup
    py5.ambient_light(50, 50, 20)
    py5.directional_light(200, 80, 100, -1, 1, -1)
    py5.directional_light(320, 80, 80, 1, 0, 1)
    
    py5.stroke(0, 0, 0, 80)
    py5.stroke_weight(1.5)
    
    offset = (GRID_SIZE * CELL_SIZE) / 2.0
    py5.translate(-offset, 0, -offset)
    
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            # Calculate height based on Perlin noise moving across the grid
            noise_val = py5.noise(x * 0.1, z * 0.1, t * 0.5)
            
            # Create extreme spikes and deep valleys to look like skyscrapers
            noise_val = noise_val ** 3 
            
            h = noise_val * 1000 + 10
            
            # Determine building style based on grid position
            is_neon = (x % 5 == 0 and z % 5 == 0)
            
            py5.push_matrix()
            py5.translate(x * CELL_SIZE + CELL_SIZE/2, -h/2, z * CELL_SIZE + CELL_SIZE/2)
            
            if is_neon:
                py5.emissive(180, 80, 100)
                py5.fill(180, 80, 100)
                py5.no_stroke()
                py5.box(CELL_SIZE * 0.8, h * 1.5, CELL_SIZE * 0.8)
                py5.emissive(0, 0, 0)
                py5.stroke(0, 0, 0, 80)
            else:
                hue = (x * 2 + z * 2 + t * 30) % 360
                py5.fill(hue, 30, 80)
                py5.box(CELL_SIZE * 0.9, h, CELL_SIZE * 0.9)
                
            py5.pop_matrix()

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

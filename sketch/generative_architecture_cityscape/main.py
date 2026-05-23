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

GRID_SIZE = 20
BLOCK_SIZE = 80
STREET_WIDTH = 20

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5) # Dark night sky
    
    t = py5.frame_count * 0.01
    
    # Setup camera moving forward through the city
    camera_z = py5.frame_count * 15.0
    py5.camera(0, -400, camera_z, 
               0, 0, camera_z + 1000, 
               0, 1, 0)
    
    # We use ambient light and directional light for the city
    py5.ambient_light(200, 50, 20)
    py5.directional_light(280, 80, 80, -1, 1, 1)
    py5.directional_light(180, 80, 50, 1, 0, -1)
    
    # We draw buildings ahead of the camera and remove them as we pass
    start_z_idx = int(camera_z / (BLOCK_SIZE + STREET_WIDTH))
    end_z_idx = start_z_idx + 25
    
    start_x_idx = -10
    end_x_idx = 10
    
    for z in range(start_z_idx, end_z_idx):
        for x in range(start_x_idx, end_x_idx):
            # Leave a main avenue in the middle
            if abs(x) <= 1:
                continue
                
            world_x = x * (BLOCK_SIZE + STREET_WIDTH)
            world_z = z * (BLOCK_SIZE + STREET_WIDTH)
            
            # Use perlin noise to determine building height
            # Downtown (closer to x=0) has taller buildings
            downtown_factor = max(0, 1.0 - abs(x) / 10.0)
            noise_val = py5.noise(x * 0.2, z * 0.2)
            height = 100 + noise_val * 800 * downtown_factor
            
            # Map building color to its position
            hue = (abs(x) * 15 + z * 5 + t * 50) % 360
            py5.fill(hue, 70, 40)
            
            # Outline the buildings with neon
            py5.stroke(hue, 100, 100)
            py5.stroke_weight(2)
            
            py5.push_matrix()
            py5.translate(world_x, -height / 2, world_z)
            py5.box(BLOCK_SIZE, height, BLOCK_SIZE)
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

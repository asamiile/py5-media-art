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

# 15x15x15 grid = 3375 voxels
GRID_SIZE = 15
CELL_SIZE = 30

# Initialize colors with 3D Perlin-like noise but heavily shuffled
# We want them to eventually sort into a perfect 3D RGB cube
hues = np.random.uniform(0, 360, (GRID_SIZE, GRID_SIZE, GRID_SIZE)).astype(np.float32)
saturations = np.random.uniform(50, 100, (GRID_SIZE, GRID_SIZE, GRID_SIZE)).astype(np.float32)
brightnesses = np.random.uniform(50, 100, (GRID_SIZE, GRID_SIZE, GRID_SIZE)).astype(np.float32)

# Pack into a single structured array or just sort by a target value
# We will sort by hue along X, saturation along Y, brightness along Z
# Wait, sorting a 3D grid independently on axes can get stuck.
# We will do 1D bubble sort along each axis sequentially.

def bubble_sort_pass_x():
    global hues
    for z in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 1):
                if hues[x, y, z] > hues[x + 1, y, z]:
                    # Swap ALL color channels to keep the "voxel" intact
                    hues[x, y, z], hues[x+1, y, z] = hues[x+1, y, z], hues[x, y, z]
                    saturations[x, y, z], saturations[x+1, y, z] = saturations[x+1, y, z], saturations[x, y, z]
                    brightnesses[x, y, z], brightnesses[x+1, y, z] = brightnesses[x+1, y, z], brightnesses[x, y, z]

def bubble_sort_pass_y():
    global saturations
    for z in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 1):
                if saturations[x, y, z] > saturations[x, y + 1, z]:
                    hues[x, y, z], hues[x, y+1, z] = hues[x, y+1, z], hues[x, y, z]
                    saturations[x, y, z], saturations[x, y+1, z] = saturations[x, y+1, z], saturations[x, y, z]
                    brightnesses[x, y, z], brightnesses[x, y+1, z] = brightnesses[x, y+1, z], brightnesses[x, y, z]

def bubble_sort_pass_z():
    global brightnesses
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            for z in range(GRID_SIZE - 1):
                if brightnesses[x, y, z] > brightnesses[x, y, z + 1]:
                    hues[x, y, z], hues[x, y, z+1] = hues[x, y, z+1], hues[x, y, z]
                    saturations[x, y, z], saturations[x, y, z+1] = saturations[x, y, z+1], saturations[x, y, z]
                    brightnesses[x, y, z], brightnesses[x, y, z+1] = brightnesses[x, y, z+1], brightnesses[x, y, z]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.01
    
    # Run sorting passes over time to animate the self-organization
    if py5.frame_count < TOTAL_FRAMES * 0.8:
        # Do a few passes per frame to speed up the sort
        for _ in range(2):
            axis = py5.frame_count % 3
            if axis == 0:
                bubble_sort_pass_x()
            elif axis == 1:
                bubble_sort_pass_y()
            else:
                bubble_sort_pass_z()
    
    # Setup 3D camera / Isometric projection
    py5.translate(py5.width / 2, py5.height / 2, -500)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(py5.PI / 4 + t * 0.5)
    
    py5.ambient_light(40, 40, 40)
    py5.directional_light(200, 10, 100, 1, 1, -1)
    py5.directional_light(340, 10, 100, -1, -1, 1)
    
    offset = -(GRID_SIZE * CELL_SIZE) / 2.0
    
    # To draw properly with depth testing, drawing order matters slightly, 
    # but P3D depth buffer usually handles it if opacity is 100%.
    # We will shrink the boxes slightly so we can see through the grid.
    box_scale = CELL_SIZE * 0.7
    
    py5.no_stroke()
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                h = hues[x, y, z]
                s = saturations[x, y, z]
                b = brightnesses[x, y, z]
                
                # Make the blocks "breathe" based on their color
                # Once sorted, this will create a wave across the cube
                breathe = py5.sin(t * 5.0 + h * 0.05) * (CELL_SIZE * 0.15)
                current_size = box_scale + breathe
                
                py5.push_matrix()
                py5.translate(offset + x * CELL_SIZE + CELL_SIZE/2,
                              offset + y * CELL_SIZE + CELL_SIZE/2,
                              offset + z * CELL_SIZE + CELL_SIZE/2)
                
                py5.fill(h, s, b)
                py5.box(current_size)
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

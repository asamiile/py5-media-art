from pathlib import Path
import shutil
import subprocess
import sys
import random
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SIZE = 28
CELL_SIZE = 45

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100)
    
    global grid, ages
    grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=bool)
    ages = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=int)
    
    # Initial seeds
    for _ in range(5):
        grid[random.randint(5, GRID_SIZE-5), random.randint(5, GRID_SIZE-5), 0] = True

def draw():
    py5.background(230, 80, 10) # very dark blue background
    py5.lights()
    py5.directional_light(0, 0, 100, 0.5, 0.8, -1)
    py5.directional_light(300, 50, 100, -1, -0.5, -0.5)
    
    global grid, ages
    
    # Cellular automaton growth step every 4 frames
    if py5.frame_count % 4 == 0:
        new_grid = grid.copy()
        for x in range(1, GRID_SIZE-1):
            for y in range(1, GRID_SIZE-1):
                for z in range(0, GRID_SIZE-1):
                    if not grid[x, y, z]:
                        neighbors = (grid[x-1, y, z] + grid[x+1, y, z] + 
                                     grid[x, y-1, z] + grid[x, y+1, z] + 
                                     (grid[x, y, z-1] if z > 0 else 0) +
                                     (grid[x, y, z+1]))
                        
                        # Grow outward with bias towards Z axis
                        if (neighbors == 1 and random.random() < 0.25) or (neighbors == 2 and random.random() < 0.15):
                            new_grid[x, y, z] = True
        grid = new_grid
    
    ages[grid] += 1
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2 + 300, 0)
    
    py5.rotate_x(-py5.PI / 4)
    py5.rotate_y(py5.PI / 4 + py5.frame_count * 0.006)
    
    offset = (GRID_SIZE * CELL_SIZE) / 2
    py5.translate(-offset, -offset, -offset)
    
    py5.no_stroke()
    
    indices = np.argwhere(grid)
    for x, y, z in indices:
        py5.push_matrix()
        py5.translate(x * CELL_SIZE, y * CELL_SIZE, z * CELL_SIZE)
        
        age = ages[x, y, z]
        # Colors evolve from base blue/cyan to bright magenta as they age/grow higher
        hue = (190 + z * 4 + age * 0.2) % 360
        saturation = min(100, 60 + z * 2)
        brightness = min(100, 50 + age)
        
        py5.fill(hue, saturation, brightness)
        s = CELL_SIZE * 0.85 + np.sin(py5.frame_count * 0.05 + x + y + z) * CELL_SIZE * 0.15
        py5.box(s)
        py5.pop_matrix()
        
    py5.pop_matrix()

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

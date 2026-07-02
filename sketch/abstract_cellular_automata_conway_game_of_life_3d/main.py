from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

GRID_SIZE = 60
CELL_SIZE = 40

grid = np.random.choice([0, 1], size=(GRID_SIZE, GRID_SIZE), p=[0.8, 0.2])
anim_grid = np.copy(grid).astype(float)

def update_gol():
    global grid
    # Count neighbors
    neighbors = sum(np.roll(np.roll(grid, i, 0), j, 1)
                    for i in (-1, 0, 1) for j in (-1, 0, 1)
                    if (i != 0 or j != 0))
    # Apply rules
    new_grid = (neighbors == 3) | (grid & (neighbors == 2))
    grid = new_grid.astype(int)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global grid, anim_grid
    py5.background(10, 15, 20)
    
    t = py5.frame_count
    
    if t % 15 == 0:
        update_gol()
        
    # Animate cells
    anim_grid += (grid - anim_grid) * 0.2
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -500)
    
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.005)
    
    # Lighting
    py5.ambient_light(0, 0, 30)
    py5.directional_light(200, 40, 100, 0.5, 0.5, -1)
    py5.directional_light(320, 60, 80, -0.5, -0.5, -1)
    
    offset_x = -GRID_SIZE * CELL_SIZE / 2
    offset_y = -GRID_SIZE * CELL_SIZE / 2
    
    py5.translate(offset_x, offset_y, 0)
    
    py5.no_stroke()
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            val = anim_grid[i, j]
            if val > 0.01:
                x = i * CELL_SIZE
                y = j * CELL_SIZE
                
                h = val * CELL_SIZE * 4
                
                # Colors based on position and height
                hue = (200 + i * 2 + j * 2 + val * 60) % 360
                
                py5.push_matrix()
                py5.translate(x, y, h / 2)
                py5.fill(hue, 80, 90)
                
                # Scale box based on val
                s = val * CELL_SIZE * 0.9
                py5.box(s, s, h)
                py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()

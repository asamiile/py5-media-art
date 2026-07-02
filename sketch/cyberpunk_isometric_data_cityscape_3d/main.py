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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Pre-generate city grid
    global grid, cols, rows, cell_size
    cell_size = 40
    cols = py5.width // cell_size + 10
    rows = py5.height // cell_size + 10
    grid = np.zeros((cols, rows))
    
    # Randomly assign "buildings" and "streets"
    for i in range(cols):
        for j in range(rows):
            if py5.noise(i * 0.1, j * 0.1) > 0.4:
                grid[i][j] = py5.random(50, 300) # Base height
            else:
                grid[i][j] = 0

def draw():
    py5.background(10, 5, 20)
    
    # Lighting
    py5.ambient_light(30, 30, 40)
    py5.directional_light(300, 80, 100, 1, 1, -1) # Pink light
    py5.directional_light(180, 100, 100, -1, 1, -0.5) # Cyan light
    
    time_t = py5.frame_count * 0.02
    
    # Isometric view setup
    py5.translate(py5.width / 2, py5.height / 2 + 300, -500)
    py5.rotate_x(py5.QUARTER_PI)
    py5.rotate_z(py5.QUARTER_PI + time_t * 0.1) # Slowly rotating city
    
    # Offset to center the grid
    offset_x = -cols * cell_size / 2
    offset_y = -rows * cell_size / 2
    
    py5.no_stroke()
    
    for i in range(cols):
        for j in range(rows):
            base_h = grid[i][j]
            if base_h > 0:
                # Oscillating height
                oscillation = np.sin(time_t * 2 + i * 0.5 + j * 0.5) * 50
                h = base_h + oscillation
                
                # Neon color mapping
                hue = (180 if (i+j)%3 == 0 else 300) + py5.noise(i, j, time_t * 0.1) * 60
                hue %= 360
                
                py5.fill(hue, 80, 90)
                
                py5.push_matrix()
                py5.translate(offset_x + i * cell_size, offset_y + j * cell_size, h / 2)
                py5.box(cell_size * 0.8, cell_size * 0.8, h)
                
                # Glowing top "data node"
                py5.translate(0, 0, h / 2 + 2)
                py5.fill(hue, 20, 100, 200)
                py5.box(cell_size * 0.4, cell_size * 0.4, 4)
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

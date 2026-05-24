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

COLS = 100
ROWS = 100
CELL_SIZE = 15

# Use a 2D array to store the CA history
ca_grid = np.zeros((ROWS, COLS), dtype=np.int32)
# Initialize first row with a single active cell in the middle
ca_grid[0, COLS // 2] = 1

def generate_next_row(current_row):
    # Rule 30: 000 -> 0, 001 -> 1, 010 -> 1, 011 -> 1, 100 -> 1, 101 -> 0, 110 -> 0, 111 -> 0
    # Rule 30 binary string: 00011110 = 30
    rule = 30
    next_row = np.zeros_like(current_row)
    
    # Pad array to handle edges
    padded = np.pad(current_row, (1, 1), mode='wrap')
    
    for i in range(len(current_row)):
        left = padded[i]
        center = padded[i+1]
        right = padded[i+2]
        
        # Calculate binary state (0-7)
        state = (left << 2) | (center << 1) | right
        
        # Extract bit from rule
        bit = (rule >> state) & 1
        next_row[i] = bit
        
    return next_row

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global ca_grid
    
    py5.background(10, 20, 10)
    
    # Generate new CA row every few frames to animate it scrolling
    if py5.frame_count % 3 == 0:
        # Shift rows up
        ca_grid[1:] = ca_grid[:-1]
        # Generate new row at the top (which falls down)
        ca_grid[0] = generate_next_row(ca_grid[1])
        
        # Occasionally perturb the CA to keep it chaotic
        if py5.frame_count % 120 == 0:
            idx = np.random.randint(0, COLS)
            ca_grid[0, idx] = 1
            
    t = py5.frame_count * 0.05
    
    # Setup isometric projection
    py5.translate(py5.width / 2, py5.height / 2 + 100, -500)
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(py5.PI / 4 + t * 0.1) # Slowly rotate the entire tapestry
    
    py5.ambient_light(0, 0, 100)
    py5.directional_light(40, 60, 100, 1, 1, -1)
    py5.directional_light(200, 60, 100, -1, -1, 1)
    
    offset_x = -COLS * CELL_SIZE / 2
    offset_y = -ROWS * CELL_SIZE / 2
    
    py5.no_stroke()
    
    for r in range(ROWS):
        for c in range(COLS):
            val = ca_grid[r, c]
            
            py5.push_matrix()
            py5.translate(offset_x + c * CELL_SIZE, offset_y + r * CELL_SIZE, 0)
            
            # Animate the blocks based on their age (row index) and state
            dist_to_center = py5.dist(c, r, COLS/2, ROWS/2)
            z_offset = py5.sin(t + dist_to_center * 0.1) * 20
            
            if val == 1:
                # Active cell
                py5.translate(0, 0, z_offset + 10)
                py5.fill(45, 80, 100) # Gold
                py5.emissive(45, 80, 50)
                py5.box(CELL_SIZE * 0.9, CELL_SIZE * 0.9, CELL_SIZE * 2)
            else:
                # Inactive cell
                py5.translate(0, 0, z_offset - 10)
                py5.fill(220, 60, 20) # Dark blue/black
                py5.emissive(0, 0, 0)
                py5.box(CELL_SIZE * 0.9, CELL_SIZE * 0.9, CELL_SIZE * 0.5)
                
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

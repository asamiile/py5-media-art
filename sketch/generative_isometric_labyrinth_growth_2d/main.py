from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 15, 20)
    
    global grid_size, grid, current_cell, stack, scale, tile_size
    grid_size = 60
    grid = np.zeros((grid_size, grid_size), dtype=int)
    current_cell = (grid_size // 2, grid_size // 2)
    grid[current_cell] = 1 # visited
    stack = [current_cell]
    scale = 30
    tile_size = 28

def iso_project(x, y, z):
    # Standard isometric projection
    ix = (x - y) * np.cos(np.pi / 6)
    iy = (x + y) * np.sin(np.pi / 6) - z
    return ix, iy

def draw():
    global current_cell, stack, grid, grid_size
    
    # Do multiple steps per frame to speed up generation
    steps_per_frame = 3
    for _ in range(steps_per_frame):
        if len(stack) > 0:
            cx, cy = current_cell
            
            # Find unvisited neighbors
            neighbors = []
            if cx > 0 and grid[cx-1, cy] == 0: neighbors.append((cx-1, cy))
            if cx < grid_size-1 and grid[cx+1, cy] == 0: neighbors.append((cx+1, cy))
            if cy > 0 and grid[cx, cy-1] == 0: neighbors.append((cx, cy-1))
            if cy < grid_size-1 and grid[cx, cy+1] == 0: neighbors.append((cx, cy+1))
            
            if len(neighbors) > 0:
                nx, ny = random.choice(neighbors)
                stack.append(current_cell)
                grid[nx, ny] = 1
                
                # Draw the path immediately
                py5.push_matrix()
                py5.translate(py5.width/2, py5.height/2 + 400)
                
                # Draw line from current to neighbor
                py5.stroke(0, 255, 200, 150)
                py5.stroke_weight(2)
                
                ix1, iy1 = iso_project((cx - grid_size/2) * scale, (cy - grid_size/2) * scale, 0)
                ix2, iy2 = iso_project((nx - grid_size/2) * scale, (ny - grid_size/2) * scale, 0)
                
                py5.line(ix1, iy1, ix2, iy2)
                
                # Draw glowing node at new cell
                h = random.randint(10, 50)
                py5.fill(0, 200, 255, 200)
                py5.no_stroke()
                
                py5.begin_shape()
                for dx, dy in [(0,0), (1,0), (1,1), (0,1)]:
                    vx, vy = iso_project((nx - grid_size/2 + dx*0.2) * scale, (ny - grid_size/2 + dy*0.2) * scale, h)
                    py5.vertex(vx, vy)
                py5.end_shape(py5.CLOSE)
                
                py5.pop_matrix()
                
                current_cell = (nx, ny)
            else:
                current_cell = stack.pop()
    
    # Slight overlay to create trails for the moving head
    py5.fill(10, 15, 20, 5)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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

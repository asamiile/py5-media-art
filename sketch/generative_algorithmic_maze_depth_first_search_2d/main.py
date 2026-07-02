from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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

CELL_SIZE = 40
COLS = SIZE[0] // CELL_SIZE
ROWS = SIZE[1] // CELL_SIZE

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited = False
        # Top, Right, Bottom, Left
        self.walls = [True, True, True, True]

grid = [[Cell(x, y) for y in range(ROWS)] for x in range(COLS)]
stack = []
current = grid[COLS//2][ROWS//2]
current.visited = True
stack.append(current)

def get_unvisited_neighbors(cell):
    neighbors = []
    x, y = cell.x, cell.y
    if y > 0 and not grid[x][y-1].visited:
        neighbors.append((grid[x][y-1], 0))
    if x < COLS - 1 and not grid[x+1][y].visited:
        neighbors.append((grid[x+1][y], 1))
    if y < ROWS - 1 and not grid[x][y+1].visited:
        neighbors.append((grid[x][y+1], 2))
    if x > 0 and not grid[x-1][y].visited:
        neighbors.append((grid[x-1][y], 3))
    return neighbors

def remove_walls(a, b, dir_a_to_b):
    a.walls[dir_a_to_b] = False
    b.walls[(dir_a_to_b + 2) % 4] = False

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global current
    
    # Run a few steps per frame
    steps = 10
    
    for _ in range(steps):
        if len(stack) > 0:
            neighbors = get_unvisited_neighbors(current)
            if len(neighbors) > 0:
                next_cell, direction = random.choice(neighbors)
                next_cell.visited = True
                stack.append(current)
                remove_walls(current, next_cell, direction)
                current = next_cell
            else:
                current = stack.pop()
    
    py5.background(0, 0, 5, 40) # slight fade for motion blur
    
    py5.stroke(200, 50, 100)
    py5.stroke_weight(2)
    py5.stroke_cap(py5.SQUARE)
    
    # Draw walls
    for x in range(COLS):
        for y in range(ROWS):
            cell = grid[x][y]
            cx = x * CELL_SIZE
            cy = y * CELL_SIZE
            
            if cell.visited:
                py5.stroke(200, 50, 50)
                if cell.walls[0]: py5.line(cx, cy, cx + CELL_SIZE, cy)
                if cell.walls[1]: py5.line(cx + CELL_SIZE, cy, cx + CELL_SIZE, cy + CELL_SIZE)
                if cell.walls[2]: py5.line(cx + CELL_SIZE, cy + CELL_SIZE, cx, cy + CELL_SIZE)
                if cell.walls[3]: py5.line(cx, cy + CELL_SIZE, cx, cy)
                
    # Draw stack
    py5.no_stroke()
    for i, c in enumerate(stack):
        hue = (py5.frame_count * 2 + i * 5) % 360
        py5.fill(hue, 80, 100, 150)
        py5.rect(c.x * CELL_SIZE, c.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        
    # Draw current
    py5.fill(0, 0, 100)
    py5.rect(current.x * CELL_SIZE, current.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

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

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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid logic
GRID_SIZE = 80
NUM_PACKETS = 2000

# Packets structure: x, y, dx, dy, color_idx, tail_length
packets = np.zeros((NUM_PACKETS, 6), dtype=np.float32)

colors = [
    (0, 255, 255),   # Neon Cyan
    (255, 0, 255),   # Hot Magenta
    (255, 102, 0),   # Electric Orange
    (0, 200, 255)    # Light Blue
]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize packets
    for i in range(NUM_PACKETS):
        # Start on random grid intersections
        gx = np.random.randint(0, SIZE[0] // GRID_SIZE + 1) * GRID_SIZE
        gy = np.random.randint(0, SIZE[1] // GRID_SIZE + 1) * GRID_SIZE
        
        # Pick random orth direction
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        d = dirs[np.random.randint(0, 4)]
        
        c_idx = np.random.randint(0, len(colors))
        tail = np.random.uniform(20, 100)
        
        packets[i] = [gx, gy, d[0], d[1], c_idx, tail]
        
    py5.background(5, 5, 16) # Deep Navy/Black
    
def draw():
    # Draw faint trails and clear
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 16, 30) # slight trail effect
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw the static grid points faintly
    py5.stroke(21, 32, 48, 80) # Slate Blue
    py5.stroke_weight(2)
    # py5.shape or manual points. Since it's heavy, we'll just draw a few big rects in the background to simulate buildings
    py5.fill(10, 15, 25, 40)
    py5.no_stroke()
    py5.rect(200, 200, 400, 400)
    py5.rect(1200, 800, 600, 300)
    py5.rect(800, 1500, 300, 500)
    
    py5.blend_mode(py5.ADD)
    
    speed = 15.0
    
    for i in range(NUM_PACKETS):
        x, y, dx, dy, c_idx, tail = packets[i]
        
        # Move
        nx = x + dx * speed
        ny = y + dy * speed
        
        crossed = False
        snap_x = x
        snap_y = y
        
        if dx > 0:
            next_grid = (np.floor(x / GRID_SIZE) + 1) * GRID_SIZE
            if nx >= next_grid and x < next_grid:
                crossed = True
                snap_x = next_grid
                snap_y = ny
        elif dx < 0:
            # Need to handle exact float precision issues so we subtract a tiny amount before ceil or just use math
            # A safe way to find the previous grid point is:
            # next_grid = floor((x - 0.001) / GRID_SIZE) * GRID_SIZE
            next_grid = np.floor((x - 0.001) / GRID_SIZE) * GRID_SIZE
            if nx <= next_grid and x > next_grid:
                crossed = True
                snap_x = next_grid
                snap_y = ny
        elif dy > 0:
            next_grid = (np.floor(y / GRID_SIZE) + 1) * GRID_SIZE
            if ny >= next_grid and y < next_grid:
                crossed = True
                snap_x = nx
                snap_y = next_grid
        elif dy < 0:
            next_grid = np.floor((y - 0.001) / GRID_SIZE) * GRID_SIZE
            if ny <= next_grid and y > next_grid:
                crossed = True
                snap_x = nx
                snap_y = next_grid
                
        if crossed:
            if np.random.rand() < 0.4:
                # 90 deg turn
                if dx != 0: # moving horizontally
                    dx = 0
                    dy = np.random.choice([-1, 1])
                else: # moving vertically
                    dy = 0
                    dx = np.random.choice([-1, 1])
            
            nx, ny = snap_x, snap_y

            
        # Wrap around
        if nx > py5.width + 100: nx = -100
        if nx < -100: nx = py5.width + 100
        if ny > py5.height + 100: ny = -100
        if ny < -100: ny = py5.height + 100
        
        packets[i, 0] = nx
        packets[i, 1] = ny
        packets[i, 2] = dx
        packets[i, 3] = dy
        
        # Draw the tail
        tx = nx - dx * tail
        ty = ny - dy * tail
        
        py5.stroke_weight(4)
        r, g, b = colors[int(c_idx)]
        py5.stroke(r, g, b, 200)
        py5.line(nx, ny, tx, ty)

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            
        import os
        os._exit(0)

py5.run_sketch()

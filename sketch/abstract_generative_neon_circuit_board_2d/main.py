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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0, 0, 5)
    py5.stroke_weight(4)
    py5.stroke_cap(py5.SQUARE)
    
    global grid_size, cols, rows, paths, grid
    grid_size = 40
    cols = py5.width // grid_size + 1
    rows = py5.height // grid_size + 1
    grid = np.zeros((cols, rows), dtype=int)
    
    paths = []
    for _ in range(50): # 50 starting points
        cx = py5.random_int(cols - 1)
        cy = py5.random_int(rows - 1)
        grid[cx, cy] = 1
        hue = py5.random(100, 200) # Cyberpunk cyan to blue
        if py5.random(1) < 0.2:
            hue = py5.random(280, 340) # occasional magenta
        paths.append({
            "x": cx, "y": cy, 
            "dir": py5.random_int(3), # 0: N, 1: E, 2: S, 3: W
            "hue": hue, "active": True
        })

def get_next_pos(x, y, d):
    if d == 0: return x, y - 1
    if d == 1: return x + 1, y
    if d == 2: return x, y + 1
    if d == 3: return x - 1, y
    return x, y

def draw():
    # Motion blur / fading
    py5.no_stroke()
    py5.fill(0, 0, 5, 2)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.stroke_weight(4)
    
    for p in paths:
        if not p["active"]: continue
        
        # Chance to turn
        if py5.random(1) < 0.1:
            p["dir"] = (p["dir"] + py5.random_choice([-1, 1])) % 4
            
        nx, ny = get_next_pos(p["x"], p["y"], p["dir"])
        
        # Bounds check
        if nx < 0 or nx >= cols or ny < 0 or ny >= rows:
            p["active"] = False
            continue
            
        # Collision check
        if grid[nx, ny] == 1:
            # Draw a node (via)
            py5.no_stroke()
            py5.fill(0, 0, 100, 100)
            py5.circle(nx * grid_size, ny * grid_size, 12)
            p["active"] = False
            
            # Spawn a new path elsewhere occasionally to keep it going
            if py5.random(1) < 0.3:
                sx = py5.random_int(cols - 1)
                sy = py5.random_int(rows - 1)
                grid[sx, sy] = 1
                paths.append({
                    "x": sx, "y": sy,
                    "dir": py5.random_int(3),
                    "hue": py5.random(100, 200) if py5.random(1) > 0.2 else py5.random(280, 340),
                    "active": True
                })
            continue
            
        # Draw segment
        py5.stroke(p["hue"], 90, 100, 80)
        py5.line(p["x"] * grid_size, p["y"] * grid_size, nx * grid_size, ny * grid_size)
        
        grid[nx, ny] = 1
        p["x"] = nx
        p["y"] = ny
        
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
            
        import os
        os._exit(0)

py5.run_sketch()

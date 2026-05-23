from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# 3D Grid for crystal growth
GRID_SIZE = 30
SPACING = 20
grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=int)
active_nodes = []

# Directions for 3D Von Neumann neighborhood
DIRECTIONS = [
    (1,0,0), (-1,0,0),
    (0,1,0), (0,-1,0),
    (0,0,1), (0,0,-1)
]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed the crystal in the center
    cx, cy, cz = GRID_SIZE//2, GRID_SIZE//2, GRID_SIZE//2
    grid[cx, cy, cz] = 1 # Generation 1
    active_nodes.append((cx, cy, cz, 1))
    
def draw():
    py5.background(15)
    
    # Growth phase: grow multiple crystals per frame to speed up the process
    if len(active_nodes) > 0 and len(active_nodes) < 15000:
        for _ in range(50):
            if not active_nodes:
                break
                
            # Pick a random active node (biased towards newer nodes for branching structure)
            idx = int(random.betavariate(2, 1) * len(active_nodes))
            if idx >= len(active_nodes):
                idx = len(active_nodes) - 1
                
            x, y, z, gen = active_nodes[idx]
            
            # Try to grow in a random direction
            dx, dy, dz = random.choice(DIRECTIONS)
            nx, ny, nz = x + dx, y + dy, z + dz
            
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 0 <= nz < GRID_SIZE:
                if grid[nx, ny, nz] == 0:
                    grid[nx, ny, nz] = gen + 1
                    active_nodes.append((nx, ny, nz, gen + 1))
                    
                    # Occasionally deactivate old nodes so they don't grow forever (makes it branching)
                    if random.random() < 0.2:
                        active_nodes.pop(idx)

    # Rendering phase
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    t = py5.frame_count * 0.01
    py5.rotate_y(t)
    py5.rotate_x(py5.sin(t * 0.5) * 0.5)
    
    # Center the grid
    py5.translate(-GRID_SIZE * SPACING / 2, -GRID_SIZE * SPACING / 2, -GRID_SIZE * SPACING / 2)
    
    py5.ambient_light(100, 50, 50)
    py5.directional_light(0, 0, 100, -1, 1, -1)
    py5.directional_light(200, 100, 80, 1, -1, 1)
    
    # Draw crystals using instance-like rendering logic
    for z in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                gen = grid[x, y, z]
                if gen > 0:
                    py5.push_matrix()
                    py5.translate(x * SPACING, y * SPACING, z * SPACING)
                    
                    # Colors based on generation (age) to create bismuth-like rainbow layers
                    hue = (gen * 5 + t * 200) % 360
                    py5.fill(hue, 90, 90)
                    py5.stroke(hue, 100, 100)
                    py5.stroke_weight(1)
                    
                    # Crystals scale up slightly as they age (lower gen)
                    size = min(SPACING * 0.8, SPACING * 0.3 + gen * 0.1)
                    py5.box(size)
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

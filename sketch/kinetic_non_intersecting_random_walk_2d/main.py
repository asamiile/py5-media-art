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

CELL_SIZE = 12
GRID_W = SIZE[0] // CELL_SIZE
GRID_H = SIZE[1] // CELL_SIZE

# True if cell has been visited
grid = np.zeros((GRID_H, GRID_W), dtype=bool)

# Agents: list of [x, y, hue]
agents = []
for _ in range(500):
    agents.append([random.randint(1, GRID_W - 2), random.randint(1, GRID_H - 2), random.choice([190, 320, 50, 0])])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(240, 90, 10) # very dark blue
    py5.stroke_weight(CELL_SIZE * 0.8)
    py5.stroke_cap(py5.ROUND)

def draw():
    global agents
    
    # We do a few steps per frame to make it fast
    for _ in range(3):
        new_agents = []
        for a in agents:
            x, y, hue = a
            grid[y, x] = True
            
            # Find available neighbors
            neighbors = []
            if x > 0 and not grid[y, x - 1]: neighbors.append((x - 1, y))
            if x < GRID_W - 1 and not grid[y, x + 1]: neighbors.append((x + 1, y))
            if y > 0 and not grid[y - 1, x]: neighbors.append((x, y - 1))
            if y < GRID_H - 1 and not grid[y + 1, x]: neighbors.append((x, y + 1))
            
            if neighbors:
                nx, ny = random.choice(neighbors)
                
                # Draw step
                py5.stroke(hue, 90, 100)
                py5.line(x * CELL_SIZE, y * CELL_SIZE, nx * CELL_SIZE, ny * CELL_SIZE)
                
                # Update agent
                a[0] = nx
                a[1] = ny
                grid[ny, nx] = True
                new_agents.append(a)
                
                # Random chance to spawn a new agent if not too crowded
                if random.random() < 0.05 and len(new_agents) < 3000:
                    other_neighbors = [n for n in neighbors if n != (nx, ny)]
                    if other_neighbors:
                        nnx, nny = random.choice(other_neighbors)
                        new_agents.append([nnx, nny, hue])
                        
        agents = new_agents
        
        # If all agents die, spawn some new ones in unvisited areas
        if len(agents) < 100:
            unvisited_y, unvisited_x = np.where(~grid)
            if len(unvisited_x) > 0:
                for _ in range(50):
                    idx = random.randint(0, len(unvisited_x) - 1)
                    ux, uy = unvisited_x[idx], unvisited_y[idx]
                    agents.append([ux, uy, random.choice([190, 320, 50, 0])])
                    grid[uy, ux] = True

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
        import os
        os._exit(0)

py5.run_sketch()

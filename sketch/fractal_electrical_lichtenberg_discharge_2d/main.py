import math
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid for fast collision detection
CELL_SIZE = 5
grid_w, grid_h = 0, 0
occupancy = None

class Branch:
    def __init__(self, x, y, angle, generation):
        self.x = x
        self.y = y
        self.angle = angle
        self.generation = generation
        self.active = True
        self.length = random.uniform(8, 25)
        self.age = 0

branches = []
new_branches = []

def add_branch(x, y, angle, gen):
    global occupancy, grid_w, grid_h
    gx = int(x / CELL_SIZE)
    gy = int(y / CELL_SIZE)
    if gx >= 0 and gx < grid_w and gy >= 0 and gy < grid_h:
        if occupancy[gy, gx]:
            return None
        occupancy[gy, gx] = True
        b = Branch(x, y, angle, gen)
        new_branches.append(b)
        return b
    return None

def setup():
    global occupancy, grid_w, grid_h, branches, new_branches
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(8, 6, 8)
    
    grid_w = SIZE[0] // CELL_SIZE + 1
    grid_h = SIZE[1] // CELL_SIZE + 1
    occupancy = np.zeros((grid_h, grid_w), dtype=bool)
    
    # Start from center
    add_branch(SIZE[0]/2, SIZE[1]/2, random.uniform(0, 2*math.pi), 0)
    branches = new_branches[:]
    new_branches = []

def draw():
    global branches, new_branches
    
    # Fade background slightly for glowing trails to die down
    py5.fill(8, 6, 8, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    current_active = [b for b in branches if b.active]
    
    # Process a chunk of growth per frame
    growth_cycles = 3
    for _ in range(growth_cycles):
        next_active = []
        for b in current_active:
            if not b.active:
                continue
            
            # Draw current branch growth step
            growth_speed = 3.0
            nx = b.x + math.cos(b.angle) * growth_speed
            ny = b.y + math.sin(b.angle) * growth_speed
            
            # Distance checking
            gx, gy = int(nx / CELL_SIZE), int(ny / CELL_SIZE)
            hit = False
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                if occupancy[gy, gx]:
                    hit = True
                else:
                    occupancy[gy, gx] = True
            else:
                hit = True
                
            if hit or b.age * growth_speed > b.length:
                b.active = False
                # Branch out!
                if not hit and b.generation < 500:
                    num_splits = random.choices([1, 2, 3], weights=[0.4, 0.5, 0.1])[0]
                    for _ in range(num_splits):
                        angle_offset = random.gauss(0, 0.5)
                        add_branch(nx, ny, b.angle + angle_offset, b.generation + 1)
            else:
                # Draw the segment
                # Color based on generation and age
                alpha = 255
                if b.generation < 10:
                    py5.stroke(255, 255, 255, alpha) # White flashes for main branches
                    py5.stroke_weight(4)
                elif b.generation < 50:
                    py5.stroke(180, 50, 255, alpha) # Neon violet
                    py5.stroke_weight(2)
                else:
                    py5.stroke(200, 100, 20, alpha) # Burnt amber
                    py5.stroke_weight(1)
                
                py5.line(b.x, b.y, nx, ny)
                b.x, b.y = nx, ny
                b.age += 1
                next_active.append(b)
                
        current_active = next_active + new_branches
        branches.extend(new_branches)
        new_branches = []
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Branches: {len(branches)}")

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

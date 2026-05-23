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

# Cellular Automata parameters
GRID_W = 120
GRID_H = 150
cells = np.zeros((GRID_H, GRID_W), dtype=int)
# Initialize first row with a single dot in the middle (classic start for rule 30)
cells[0, GRID_W // 2] = 1

# Rule 30
# 111 110 101 100 011 010 001 000
#  0   0   0   1   1   1   1   0
rule = [0, 1, 1, 1, 1, 0, 0, 0]

for y in range(1, GRID_H):
    for x in range(GRID_W):
        left = cells[y-1, (x-1) % GRID_W]
        center = cells[y-1, x]
        right = cells[y-1, (x+1) % GRID_W]
        idx = (left << 2) | (center << 1) | right
        cells[y, x] = rule[7 - idx]

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # We will map the 1D CA history (y-axis) onto a 3D cylinder
    # and make the cylinder slowly bend and wave like fabric.
    
    py5.rotate_x(py5.PI / 4 + py5.sin(t * 0.3) * 0.2)
    py5.rotate_z(t * 0.5)
    
    radius = 300
    y_step = 6
    
    py5.no_stroke()
    
    # Draw as a continuous mesh for the cylinder
    py5.begin_shape(py5.QUADS)
    for y in range(GRID_H - 1):
        for x in range(GRID_W):
            val1 = cells[y, x]
            val2 = cells[y+1, x]
            val3 = cells[y+1, (x+1) % GRID_W]
            val4 = cells[y, (x+1) % GRID_W]
            
            # Map x to angle, y to cylinder height
            angle1 = x * py5.TWO_PI / GRID_W
            angle2 = (x+1) * py5.TWO_PI / GRID_W
            
            # Add some perlin noise to deform the cylinder into a wavy cloth
            noise1 = py5.noise(x * 0.1, y * 0.1, t) * 100
            noise2 = py5.noise((x+1) * 0.1, y * 0.1, t) * 100
            noise3 = py5.noise((x+1) * 0.1, (y+1) * 0.1, t) * 100
            noise4 = py5.noise(x * 0.1, (y+1) * 0.1, t) * 100
            
            r1 = radius + noise1
            r2 = radius + noise2
            r3 = radius + noise3
            r4 = radius + noise4
            
            cy1 = (y - GRID_H/2) * y_step
            cy2 = (y + 1 - GRID_H/2) * y_step
            
            # Color logic based on CA cell value
            if val1 == 1:
                hue = (y * 2 + t * 40) % 360
                py5.fill(hue, 80, 90, 90)
            else:
                py5.fill(0, 0, 20, 40) # Dark fabric background
                
            px1 = r1 * py5.cos(angle1)
            pz1 = r1 * py5.sin(angle1)
            
            px2 = r4 * py5.cos(angle1)
            pz2 = r4 * py5.sin(angle1)
            
            px3 = r3 * py5.cos(angle2)
            pz3 = r3 * py5.sin(angle2)
            
            px4 = r2 * py5.cos(angle2)
            pz4 = r2 * py5.sin(angle2)
            
            py5.vertex(px1, pz1, cy1)
            py5.vertex(px4, pz4, cy1)
            py5.vertex(px3, pz3, cy2)
            py5.vertex(px2, pz2, cy2)
            
    py5.end_shape()

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

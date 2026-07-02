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

# Downscale grid for performance of CA update
GRID_W, GRID_H = 320, 180
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

STATES = 16
grid = np.random.randint(0, STATES, (GRID_H, GRID_W), dtype=np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, STATES, 100, 100, 100)
    py5.background(0)

def update_ca():
    global grid
    # Cyclic Cellular Automaton
    # A cell takes the state of a neighbor if neighbor == (cell + 1) % STATES
    
    # Pad grid to handle wrapping
    padded = np.pad(grid, 1, mode='wrap')
    
    # Shift arrays for neighbors
    n = padded[:-2, 1:-1]
    s = padded[2:, 1:-1]
    e = padded[1:-1, 2:]
    w = padded[1:-1, :-2]
    ne = padded[:-2, 2:]
    nw = padded[:-2, :-2]
    se = padded[2:, 2:]
    sw = padded[2:, :-2]
    
    next_state = (grid + 1) % STATES
    
    # Mask where any neighbor is the next state
    mask = (n == next_state) | (s == next_state) | (e == next_state) | (w == next_state) | \
           (ne == next_state) | (nw == next_state) | (se == next_state) | (sw == next_state)
           
    grid = np.where(mask, next_state, grid)

def draw():
    update_ca()
    
    # Render grid to screen via a fast pixels approach or rects
    # Py5 has set_np_pixels but we are drawing a low res grid scaled up
    # We will draw it manually using no_stroke and rects, or create a py5 image
    
    img = py5.create_image(GRID_W, GRID_H, py5.RGB)
    img.load_np_pixels()
    
    # Map CA states to HSB colors, convert to RGB for np_pixels
    # Hue shift over time
    hue_offset = (py5.frame_count * 0.2) % STATES
    
    hues = (grid + hue_offset) % STATES
    
    # We construct RGB arrays manually (py5 np_pixels expects BGRA or ARGB depending on os)
    # Just draw rects, it's safer and fast enough for 320x180 = 57k rects? 
    # Actually, 57k rects in python might be too slow. Let's try Py5 shape or image
    # We can use py5.points if we scale properly
    pass

    # Alternative: Draw scaled rects manually but optimized
    cell_w = py5.width / GRID_W
    cell_h = py5.height / GRID_H
    
    py5.no_stroke()
    # To optimize, we group rects by state
    for s in range(STATES):
        hue = (s + (py5.frame_count * 0.2)) % STATES
        py5.fill(hue, 90, 90)
        
        y_idx, x_idx = np.where(grid == s)
        if len(y_idx) > 0:
            py5.begin_shape(py5.QUADS)
            for i in range(len(y_idx)):
                x = x_idx[i] * cell_w
                y = y_idx[i] * cell_h
                py5.vertex(x, y)
                py5.vertex(x + cell_w, y)
                py5.vertex(x + cell_w, y + cell_h)
                py5.vertex(x, y + cell_h)
            py5.end_shape()

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

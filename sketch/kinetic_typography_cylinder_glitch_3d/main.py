from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import random
import string

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

RADIUS = 400
ROWS = 60
COLS = 80
CHARS = list("0123456789ABCDEF")
font = None
data_grid = []

def setup():
    global font, data_grid
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize character grid
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append(random.choice(CHARS))
        data_grid.append(row)
        
    font = py5.create_font("Courier New", 24)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)

def draw():
    global data_grid
    py5.background(10, 15, 10) # Very dark green-black void
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Slowly tilt the cylinder to see more of its 3D volume
    py5.rotate_x(py5.sin(py5.frame_count * 0.01) * 0.2 - 0.1)
    py5.rotate_y(py5.frame_count * 0.005)
    
    t = py5.frame_count * 0.05
    
    row_height = py5.height * 1.5 / ROWS
    angle_step = py5.TWO_PI / COLS
    
    # Randomly glitch some characters each frame
    if py5.frame_count % 3 == 0:
        for _ in range(50):
            r = random.randint(0, ROWS - 1)
            c = random.randint(0, COLS - 1)
            data_grid[r][c] = random.choice(CHARS)
            
    # Glitch wave parameter
    glitch_t = py5.frame_count * 0.1
    
    for r in range(ROWS):
        y = (r - ROWS / 2) * row_height
        for c in range(COLS):
            angle = c * angle_step
            char = data_grid[r][c]
            
            # Base position
            x = RADIUS * py5.cos(angle)
            z = RADIUS * py5.sin(angle)
            
            # Compute a 3D noise for glitches
            # Use os_noise with wrap-around coordinates for seamless cylinder noise
            nx = py5.cos(angle) * 1.5
            ny = r * 0.1
            nz = py5.sin(angle) * 1.5
            noise_val = py5.os_noise(nx, ny - glitch_t, nz)
            
            displacement = 0
            is_glitch = False
            
            # If noise is high, push character outward and make it stark white
            if noise_val > 0.7:
                displacement = (noise_val - 0.7) * 400
                is_glitch = True
            elif noise_val < -0.7:
                # inward pinch
                displacement = (noise_val + 0.7) * 200
                
            final_x = (RADIUS + displacement) * py5.cos(angle)
            final_z = (RADIUS + displacement) * py5.sin(angle)
            
            py5.push_matrix()
            py5.translate(final_x, y, final_z)
            
            # Rotate text so it faces outwards from the center of the cylinder
            # and tilts slightly along the glitch
            py5.rotate_y(-angle + py5.HALF_PI)
            
            if is_glitch:
                py5.fill(255, 255, 255, 220) # Stark white glitch
                if py5.frame_count % 2 == 0:
                    py5.rotate_z(random.uniform(-0.1, 0.1))
            else:
                # Color gradient from top to bottom
                hue_val = py5.remap(r, 0, ROWS, 100, 160) # Green to Cyan range roughly
                py5.color_mode(py5.HSB, 360, 100, 100, 255)
                # Flickering opacity
                op = 200 + py5.sin(r + c * 2 + t) * 55
                # Add depth dimming
                depth = py5.remap(final_z, -RADIUS, RADIUS, 50, 100)
                py5.fill(hue_val, 100, depth, op)
                py5.color_mode(py5.RGB, 255) # Revert
                
            py5.text(char, 0, 0)
            py5.pop_matrix()
            
    py5.pop_matrix()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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

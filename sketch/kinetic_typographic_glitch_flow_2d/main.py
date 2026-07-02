from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
from lib.safety import apply_anti_flicker_filter

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

font = None
chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
cols = 80
rows = 45
cell_w = 0
cell_h = 0

grid = []

def setup():
    global font, cell_w, cell_h
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    font = py5.create_font("Courier", 48)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)
    
    cell_w = py5.width / cols
    cell_h = py5.height / rows
    
    for y in range(rows):
        row = []
        for x in range(cols):
            row.append(random.choice(chars))
        grid.append(row)

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.05
    
    # Update some characters
    for _ in range(100):
        grid[random.randint(0, rows-1)][random.randint(0, cols-1)] = random.choice(chars)
    
    # Draw characters with chromatic aberration and glitch
    py5.blend_mode(py5.ADD)
    
    for y in range(rows):
        # Determine glitch offset for this row
        glitch_offset = 0
        if random.random() < 0.05:
            glitch_offset = random.uniform(-100, 100)
            
        py_y = y * cell_h + cell_h / 2
        
        for x in range(cols):
            c = grid[y][x]
            
            # Flow effect
            flow = py5.os_noise(x * 0.1, y * 0.1, t)
            if flow > 0.6:
                continue # Skip some characters to create gaps
                
            py_x = x * cell_w + cell_w / 2 + glitch_offset
            
            # Base brightness
            bright = int(py5.remap(flow, 0, 0.6, 255, 50))
            
            # Chromatic aberration offsets
            off_r = 4 * py5.sin(t * 2 + y)
            off_b = -4 * py5.cos(t * 2 + x)
            
            py5.fill(bright, 0, 0)
            py5.text(c, py_x + off_r, py_y)
            
            py5.fill(0, bright, 0)
            py5.text(c, py_x, py_y)
            
            py5.fill(0, 0, bright)
            py5.text(c, py_x + off_b, py_y)

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    apply_anti_flicker_filter(0.5)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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

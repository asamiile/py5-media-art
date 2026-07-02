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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Cream / Off-White background
    py5.background(245, 245, 240)
    
    t = py5.frame_count / 60.0
    progress = py5.frame_count / TOTAL_FRAMES
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    py5.blend_mode(py5.MULTIPLY)
    
    # Layer 1: Huge rotating Mustard Yellow grid
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.rotate(t * 0.2)
    py5.stroke(221, 170, 34, 180) # Warm Mustard Yellow
    py5.stroke_weight(8)
    grid_spacing = 150
    grid_size = int(max(SIZE) * 1.5)
    for i in range(-grid_size, grid_size, grid_spacing):
        py5.line(i, -grid_size, i, grid_size)
        py5.line(-grid_size, i, grid_size, i)
    py5.pop_matrix()
    
    # Layer 2: Deep Red pulsing concentric circles
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.stroke(170, 17, 34, 200) # Deep Red
    py5.no_fill()
    num_circles = 12
    for i in range(num_circles):
        offset = (i / num_circles) * np.pi * 2
        radius = 200 + i * 80 + np.sin(t * 1.5 + offset) * 100
        thickness = 10 + np.cos(t * 2.0 + offset) * 8
        py5.stroke_weight(thickness)
        py5.circle(0, 0, radius * 2)
    py5.pop_matrix()
    
    # Layer 3: Charcoal Black precise sweeping arcs and clock hands
    py5.push_matrix()
    py5.translate(cx, cy)
    py5.stroke(17, 17, 17, 240) # Charcoal Black
    py5.no_fill()
    py5.stroke_cap(py5.SQUARE)
    
    # Main outer ring
    py5.stroke_weight(20)
    py5.circle(0, 0, 1800)
    
    # Inner moving arcs
    for i in range(3):
        py5.stroke_weight(40 + i * 20)
        start_angle = t * (0.5 + i * 0.3)
        end_angle = start_angle + np.pi / (1.5 + i * 0.5)
        py5.arc(0, 0, 800 + i * 250, 800 + i * 250, start_angle, end_angle)
    
    # Clock hands / lines
    py5.stroke_weight(15)
    for i in range(4):
        py5.push_matrix()
        py5.rotate(-t * 0.8 + i * np.pi / 2)
        py5.line(0, 0, 0, 1200)
        # Crossbars
        for j in range(1, 4):
            y_pos = j * 300
            bar_width = 150 - j * 20
            py5.line(-bar_width, y_pos, bar_width, y_pos)
        py5.pop_matrix()
    py5.pop_matrix()

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

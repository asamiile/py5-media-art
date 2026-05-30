from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_fractal(depth, max_depth, size, t):
    if depth == 0:
        return
        
    py5.push_matrix()
    
    # Quantum superposition wobble
    wobble_x = np.sin(t * depth + depth) * (size * 0.1)
    wobble_y = np.cos(t * depth + depth) * (size * 0.1)
    py5.translate(wobble_x, wobble_y, 0)
    
    py5.rotate_x(t * 0.2 + depth * 0.1)
    py5.rotate_y(t * 0.3 + depth * 0.1)
    py5.rotate_z(t * 0.1 + depth * 0.1)
    
    # Additive color based on depth
    # Magenta (300) to Amber (40)
    h = py5.remap(depth, 1, max_depth, 300, 40)
    # Brightness increases as depth increases (closer to core)
    b = py5.remap(depth, 1, max_depth, 40, 100)
    py5.stroke(h, 80, b, 50)
    py5.stroke_weight(max_depth - depth + 1)
    
    if depth % 2 == 0:
        py5.fill(h, 90, b, 10)
    else:
        py5.no_fill()
        
    py5.box(size)
    
    new_size = size * 0.5 * (1.0 + 0.3 * np.sin(t))
    offset = size * 0.5
    
    if depth > 1:
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                for dz in [-1, 1]:
                    py5.push_matrix()
                    py5.translate(dx * offset, dy * offset, dz * offset)
                    draw_fractal(depth - 1, max_depth, new_size, t)
                    py5.pop_matrix()
                    
    py5.pop_matrix()

def draw():
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width/2, py5.height/2, 0)
    
    t = py5.frame_count * 0.02
    
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.25)
    
    # Recursive 3D drawing, limit depth to 4 to avoid massive slowdown
    # 8 children per node, depth 4 = 1 + 8 + 64 + 512 = ~600 boxes
    draw_fractal(4, 4, 300, t)
    
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        os._exit(0)

py5.run_sketch()

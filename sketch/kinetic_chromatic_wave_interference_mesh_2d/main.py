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

rows = 150
cols = 250
spacing_x = SIZE[0] / (cols - 1)
spacing_y = SIZE[1] / (rows - 1)

waves = []
for _ in range(8):
    dir_x = random.uniform(-1, 1)
    dir_y = random.uniform(-1, 1)
    norm = np.hypot(dir_x, dir_y)
    freq = random.uniform(0.002, 0.015)
    amp = random.uniform(10, 80)
    phase_speed = random.uniform(0.01, 0.05)
    waves.append({
        'dir_x': dir_x / norm,
        'dir_y': dir_y / norm,
        'freq': freq,
        'amp': amp,
        'speed': phase_speed
    })

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5, 0, 15)
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 0, 15, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    t = py5.frame_count
    
    for r in range(rows):
        y_base = r * spacing_y
        
        c_r = int(py5.remap(r, 0, rows, 50, 255))
        c_g = int(py5.remap(r, 0, rows, 0, 50))
        c_b = int(py5.remap(r, 0, rows, 255, 100))
        
        py5.stroke(c_r, c_g, c_b, 150)
        py5.stroke_weight(py5.remap(r, 0, rows, 1, 4))
        
        py5.begin_shape()
        for c in range(cols):
            x = c * spacing_x
            y = y_base
            
            z = 0
            for w in waves:
                val = (x * w['dir_x'] + y * w['dir_y']) * w['freq'] + t * w['speed']
                z += np.sin(val) * w['amp']
                
            perspective = py5.remap(r, 0, rows, 0.2, 2.0)
            y_final = y - z * perspective
            
            py5.vertex(x, y_final)
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

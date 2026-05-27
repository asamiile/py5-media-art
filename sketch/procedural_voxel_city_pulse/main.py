from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

cols = 0
rows = 0
scl = 60
w = 2000
h = 2000

def setup():
    global cols, rows
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    cols = w // scl
    rows = h // scl

def draw():
    py5.background(0)
    
    py5.directional_light(255, 0, 255, 0, 1, -1) # Magenta
    py5.directional_light(0, 255, 255, -1, 0, 0) # Cyan
    py5.directional_light(60, 255, 255, 1, -1, -1) # Yellow
    
    py5.translate(py5.width / 2, py5.height / 2 + 200, -500)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.005)
    
    time = py5.frame_count * 0.05
    
    py5.translate(-w/2, -h/2)
    
    py5.no_stroke()
    
    for y in range(rows):
        for x in range(cols):
            # Calculate height using noise and sine waves
            dist = np.sqrt((x - cols/2)**2 + (y - rows/2)**2)
            wave = np.sin(dist * 0.2 - time) * 100
            noise_val = py5.os_noise(x * 0.1, y * 0.1 + time * 0.2) * 400
            
            box_h = max(10, wave + noise_val + 100)
            
            # Color based on height
            hue = (box_h * 0.5 + time * 10) % 360
            py5.fill(hue, 90, 100)
            
            py5.push_matrix()
            py5.translate(x * scl, y * scl, box_h / 2)
            py5.box(scl * 0.8, scl * 0.8, box_h)
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

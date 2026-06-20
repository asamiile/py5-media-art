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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*+?"

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    font = py5.create_font("Courier", 32)
    py5.text_font(font)
    py5.text_align(py5.CENTER, py5.CENTER)

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.05
    
    grid_size = 40
    cols = py5.width // grid_size + 2
    rows = py5.height // grid_size + 2
    
    cx1 = py5.width/2 + py5.cos(t * 0.3) * 300
    cy1 = py5.height/2 + py5.sin(t * 0.5) * 300
    
    cx2 = py5.width/2 + py5.sin(t * 0.2) * 400
    cy2 = py5.height/2 + py5.cos(t * 0.4) * 200
    
    for j in range(rows):
        for i in range(cols):
            x = i * grid_size
            y = j * grid_size
            
            d1 = py5.dist(x, y, cx1, cy1)
            d2 = py5.dist(x, y, cx2, cy2)
            
            # Interference wave
            wave1 = py5.sin(d1 * 0.05 - t * 2)
            wave2 = py5.sin(d2 * 0.03 - t * 1.5)
            
            val = (wave1 + wave2) * 0.5
            
            noise_val = py5.os_noise(i * 0.1, j * 0.1, t * 0.2)
            
            if val > 0:
                char_idx = int(py5.remap(noise_val, 0, 1, 0, len(charset) * 2)) % len(charset)
                char = charset[char_idx]
                
                scale = py5.remap(val, 0, 1, 0.5, 2.5)
                hue = py5.remap(wave1 - wave2, -2, 2, 0, 360) % 360
                
                py5.push_matrix()
                py5.translate(x, y)
                py5.rotate(val * py5.TWO_PI)
                py5.scale(scale)
                
                py5.fill(hue, 80, 100, 80)
                py5.text(char, 0, 0)
                
                py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

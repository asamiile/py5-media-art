from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    global chars, f, grid_w, grid_h, cols, rows
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Try to load a monospaced font
    try:
        f = py5.create_font("Courier", 32)
        py5.text_font(f)
    except:
        pass # use default
    
    chars = [chr(i) for i in range(33, 127)]
    grid_w = 40
    grid_h = 40
    cols = SIZE[0] // grid_w + 2
    rows = SIZE[1] // grid_h + 2

def draw():
    py5.background(5)
    
    t = py5.frame_count / FPS
    
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.no_stroke()
    
    for i in range(cols):
        # Column cascade speed
        col_speed = py5.os_noise(i * 0.1, 0.0) * 400
        
        for j in range(rows):
            x = i * grid_w
            y = j * grid_h
            
            y_offset = (y + t * col_speed) % (SIZE[1] + grid_h * 2) - grid_h
            
            n = py5.os_noise(i * 0.2, j * 0.2, t * 0.8)
            
            char_idx = int(py5.os_noise(i * 0.5, j * 0.5, t) * len(chars))
            c = chars[char_idx % len(chars)]
            
            if n > 0.75:
                # Glitch block - bright pink or cyan background
                if py5.os_noise(i, j, t*2) > 0.5:
                    py5.fill(255, 0, 150) # Pink
                else:
                    py5.fill(0, 255, 255) # Cyan
                
                # Displacement
                x_displace = (py5.os_noise(i, t * 15) - 0.5) * 120
                py5.rect(x + x_displace - grid_w/2, y_offset - grid_h/2, grid_w, grid_h)
                
                py5.fill(0)
                py5.text(c, x + x_displace, y_offset)
            else:
                # Normal text - acid green
                brightness = py5.os_noise(i * 0.1, y_offset * 0.01) * 255
                if brightness > 80:
                    py5.fill(50, 255, 50, brightness)
                    py5.text(c, x, y_offset)
                    
                    # Occasional chromatic aberration
                    if py5.os_noise(i, j, t*4) > 0.85:
                        py5.fill(255, 0, 0, 200)
                        py5.text(c, x - 4, y_offset)
                        py5.fill(0, 0, 255, 200)
                        py5.text(c, x + 4, y_offset)

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
        import os
        os._exit(0)

py5.run_sketch()

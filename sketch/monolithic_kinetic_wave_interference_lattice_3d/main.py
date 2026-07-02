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

cols = 60
rows = 60
box_size = 40
grid_width = cols * box_size
grid_height = rows * box_size

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 2, 0) # very dark brown/black
    
    # Lighting for warm metallic look
    py5.ambient_light(40, 30, 20)
    py5.directional_light(255, 220, 180, -1, 1, -1)
    py5.directional_light(150, 100, 50, 1, -0.5, 0)
    
    py5.translate(py5.width / 2, py5.height / 2 + 300, -800)
    py5.rotate_x(1.0) # Look down slightly
    py5.rotate_z(py5.frame_count * 0.002) # slow rotation
    
    t = py5.frame_count * 0.05
    
    # Centers of the interference waves
    cx1 = np.cos(t * 0.5) * cols / 2
    cy1 = np.sin(t * 0.4) * rows / 2
    cx2 = np.sin(t * 0.3) * cols / 2
    cy2 = np.cos(t * 0.6) * rows / 2
    
    py5.no_stroke()
    
    for i in range(cols):
        for j in range(rows):
            x = (i - cols/2.0) * box_size
            y = (j - rows/2.0) * box_size
            
            d1 = np.sqrt((i - cols/2.0 - cx1)**2 + (j - rows/2.0 - cy1)**2)
            d2 = np.sqrt((i - cols/2.0 - cx2)**2 + (j - rows/2.0 - cy2)**2)
            
            # Interference wave
            wave = np.sin(d1 * 0.3 - t) + np.sin(d2 * 0.4 - t * 1.5)
            
            # Combine with OpenSimplex noise
            noise_val = py5.os_noise(i * 0.05, j * 0.05, t * 0.2)
            
            h = 200 + wave * 150 + noise_val * 200
            
            py5.push_matrix()
            py5.translate(x, y, h / 2.0)
            
            # Warm bronze/gold color mapping
            c_val = py5.remap(wave + noise_val, -2, 2, 0, 1)
            r = py5.lerp(100, 255, c_val)
            g = py5.lerp(60, 200, c_val)
            b = py5.lerp(20, 100, c_val)
            py5.fill(r, g, b)
            
            py5.box(box_size * 0.9, box_size * 0.9, h)
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

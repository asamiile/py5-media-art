from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
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
DURATION_SEC = random.randint(15, 30)  # Random duration up to 30s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid config
STEP = 15
COLS = SIZE[0] // STEP
ROWS = SIZE[1] // STEP
x_coords, y_coords = np.meshgrid(np.arange(COLS) * STEP + STEP/2, np.arange(ROWS) * STEP + STEP/2)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Subtle fading for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.02
    
    py5.blend_mode(py5.ADD)
    
    # Calculate wave fields
    w1 = np.sin((x_coords * 0.005) + (y_coords * 0.01) - t)
    w2 = np.sin((x_coords * -0.008) + (y_coords * 0.005) + t * 1.5)
    w3 = np.cos((x_coords * 0.01) + (y_coords * -0.007) + t * 0.8)
    w4 = np.sin(np.sqrt((x_coords - SIZE[0]/2)**2 + (y_coords - SIZE[1]/2)**2) * 0.01 - t * 2)
    
    total_field = w1 + w2 + w3 + w4
    
    angles = total_field * py5.PI
    magnitudes = (np.abs(total_field) / 4.0)
    
    # Colors mapped from magnitude
    r_field = np.clip(100 + np.sin(magnitudes * 10) * 155, 0, 255)
    g_field = np.clip(100 + np.sin(magnitudes * 10 + 2) * 155, 0, 255)
    b_field = np.clip(100 + np.sin(magnitudes * 10 + 4) * 155, 0, 255)
    
    line_len = STEP * 1.2
    
    x1 = x_coords - np.cos(angles) * line_len * 0.5
    y1 = y_coords - np.sin(angles) * line_len * 0.5
    x2 = x_coords + np.cos(angles) * line_len * 0.5
    y2 = y_coords + np.sin(angles) * line_len * 0.5
    
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(ROWS):
        for j in range(COLS):
            py5.stroke(r_field[i, j], g_field[i, j], b_field[i, j], 150)
            py5.vertex(x1[i, j], y1[i, j])
            py5.vertex(x2[i, j], y2[i, j])
    py5.end_shape()

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

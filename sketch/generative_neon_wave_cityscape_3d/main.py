from pathlib import Path
import shutil
import subprocess
import sys
import math
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

GRID_SIZE = 30
TILE_W = 40
TILE_H = 20

def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(17, 0, 17)
    
def draw():
    py5.background(17, 0, 17)
    
    t = py5.frame_count * 0.015
    
    cx = py5.width / 2
    cy = py5.height / 2 + 300
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            # Isometric projection
            x = (i - j) * (TILE_W / 2)
            y = (i + j) * (TILE_H / 2)
            
            x += cx
            y += cy - (GRID_SIZE * TILE_H / 2)
            
            noise_val = py5.os_noise(i * 0.08, j * 0.08, t * 0.5)
            h = py5.remap(noise_val, 0, 1, 10, 800)
            if noise_val > 0.8:
                h *= 1.5
                
            py5.color_mode(py5.HSB, 360, 100, 100)
            hue_val = (noise_val * 360 + t * 50) % 360
            
            py5.stroke(hue_val, 80, 100)
            py5.stroke_weight(2)
            py5.fill(hue_val, 80, 10)
            
            # Draw the box using 2D shapes
            # Top face
            py5.begin_shape()
            py5.vertex(x, y - h)
            py5.vertex(x + TILE_W/2, y - TILE_H/2 - h)
            py5.vertex(x, y - TILE_H - h)
            py5.vertex(x - TILE_W/2, y - TILE_H/2 - h)
            py5.end_shape(py5.CLOSE)
            
            # Left face
            py5.begin_shape()
            py5.vertex(x - TILE_W/2, y - TILE_H/2)
            py5.vertex(x, y)
            py5.vertex(x, y - h)
            py5.vertex(x - TILE_W/2, y - TILE_H/2 - h)
            py5.end_shape(py5.CLOSE)
            
            # Right face
            py5.begin_shape()
            py5.vertex(x, y)
            py5.vertex(x + TILE_W/2, y - TILE_H/2)
            py5.vertex(x + TILE_W/2, y - TILE_H/2 - h)
            py5.vertex(x, y - h)
            py5.end_shape(py5.CLOSE)
            
    py5.color_mode(py5.RGB, 255)
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

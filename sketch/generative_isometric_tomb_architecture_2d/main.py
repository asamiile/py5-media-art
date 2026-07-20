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

GRID_W = 30
GRID_H = 30
BLOCK_SIZE = 40

def get_iso(x, y, z):
    ang = 0.52359877559
    sx = (x - y) * np.cos(ang)
    sy = (x + y) * np.sin(ang) - z
    return sx, sy

def draw_block(base_color):
    py5.fill(base_color[0] + 30, base_color[1] + 30, base_color[2] + 30)
    py5.begin_shape()
    py5.vertex(*get_iso(0, 0, BLOCK_SIZE))
    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    py5.vertex(*get_iso(0, BLOCK_SIZE, BLOCK_SIZE))
    py5.end_shape(py5.CLOSE)

    py5.fill(base_color[0] - 20, base_color[1] - 20, base_color[2] - 20)
    py5.begin_shape()
    py5.vertex(*get_iso(0, 0, 0))
    py5.vertex(*get_iso(BLOCK_SIZE, 0, 0))
    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
    py5.vertex(*get_iso(0, 0, BLOCK_SIZE))
    py5.end_shape(py5.CLOSE)

    py5.fill(base_color[0] - 50, base_color[1] - 50, base_color[2] - 50)
    py5.begin_shape()
    py5.vertex(*get_iso(BLOCK_SIZE, 0, 0))
    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, 0))
    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
    py5.end_shape(py5.CLOSE)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(20, 15, 10)
    
    curr_frame = py5.frame_count
    
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 400)
    
    py5.no_stroke()
    
    for x in range(GRID_W):
        for y in range(GRID_H):
            n = py5.os_noise(x * 0.1, y * 0.1, curr_frame * 0.005)
            h_blocks = int(n * 12)
            
            for z in range(h_blocks):
                is_glow = False
                if z == h_blocks - 1 and py5.os_noise(x * 0.2, y * 0.2, curr_frame * 0.02) > 0.7:
                    is_glow = True
                
                py5.push_matrix()
                cx, cy = get_iso(x * BLOCK_SIZE, y * BLOCK_SIZE, z * BLOCK_SIZE)
                py5.translate(cx, cy)
                
                if is_glow:
                    py5.fill(100, 200, 255)
                    py5.begin_shape()
                    py5.vertex(*get_iso(0, 0, BLOCK_SIZE))
                    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
                    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    py5.vertex(*get_iso(0, BLOCK_SIZE, BLOCK_SIZE))
                    py5.end_shape(py5.CLOSE)
                    py5.fill(50, 150, 255, 150)
                    py5.begin_shape()
                    py5.vertex(*get_iso(0, 0, 0))
                    py5.vertex(*get_iso(BLOCK_SIZE, 0, 0))
                    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
                    py5.vertex(*get_iso(0, 0, BLOCK_SIZE))
                    py5.end_shape(py5.CLOSE)
                    py5.begin_shape()
                    py5.vertex(*get_iso(BLOCK_SIZE, 0, 0))
                    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, 0))
                    py5.vertex(*get_iso(BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    py5.vertex(*get_iso(BLOCK_SIZE, 0, BLOCK_SIZE))
                    py5.end_shape(py5.CLOSE)
                else:
                    base_r = 160 + py5.os_noise(x, y, 0) * 40 - 20
                    base_g = 130 + py5.os_noise(x, y, 10) * 30 - 15
                    base_b = 90 + py5.os_noise(x, y, 20) * 30 - 15
                    draw_block((base_r, base_g, base_b))
                
                py5.pop_matrix()
                
    py5.pop_matrix()

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

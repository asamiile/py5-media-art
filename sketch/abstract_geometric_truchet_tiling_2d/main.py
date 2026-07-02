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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

tile_size = 120
cols = SIZE[0] // tile_size + 2
rows = SIZE[1] // tile_size + 2

grid_types = np.random.randint(0, 2, (cols, rows))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10)

def draw_tile(tile_type, s):
    if tile_type == 0:
        py5.arc(-s/2, -s/2, s, s, 0, py5.HALF_PI)
        py5.arc(s/2, s/2, s, s, py5.PI, py5.PI + py5.HALF_PI)
    else:
        py5.arc(s/2, -s/2, s, s, py5.HALF_PI, py5.PI)
        py5.arc(-s/2, s/2, s, s, py5.PI + py5.HALF_PI, py5.TWO_PI)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 15) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    py5.no_fill()
    py5.stroke_weight(8)
    py5.stroke_cap(py5.ROUND)
    
    for i in range(cols):
        for j in range(rows):
            x = i * tile_size
            y = j * tile_size
            
            nx = i * 0.1
            ny = j * 0.1
            n_val = py5.os_noise(nx, ny, t * 0.5)
            
            rot = n_val * py5.TWO_PI * 2.0
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(rot)
            
            hue = (i * 10 + j * 10 + t * 50) % 360
            py5.stroke(hue, 80, 100, 80)
            
            draw_tile(grid_types[i, j], tile_size)
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

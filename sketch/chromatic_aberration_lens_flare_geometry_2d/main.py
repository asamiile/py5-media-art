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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(5, 5, 8)

def draw():
    py5.background(5, 5, 8)
    
    t = py5.frame_count / 60.0
    w, h = py5.width, py5.height
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    step = 50
    
    lenses = []
    for i in range(4):
        lx = w/2 + np.sin(t * 0.4 + i*2.1) * w * 0.4
        ly = h/2 + np.cos(t * 0.5 + i*1.7) * h * 0.4
        lr = 400 + np.sin(t * 0.8 + i) * 200
        lenses.append((lx, ly, lr))
        
    def draw_grid(color, scale, intensity):
        py5.stroke(*color)
        
        # Verticals
        for x in range(0, w + step, step):
            py5.begin_shape()
            for y in range(0, h + step, step):
                dx, dy = 0, 0
                for lx, ly, lr in lenses:
                    dist = np.hypot(x - lx, y - ly)
                    if dist < lr:
                        force = (lr - dist) / lr
                        # Lens refraction distorts outward
                        dx += (x - lx) * force * 0.8 * scale
                        dy += (y - ly) * force * 0.8 * scale
                
                py5.vertex(x + dx, y + dy)
            py5.end_shape()

        # Horizontals
        for y in range(0, h + step, step):
            py5.begin_shape()
            for x in range(0, w + step, step):
                dx, dy = 0, 0
                for lx, ly, lr in lenses:
                    dist = np.hypot(x - lx, y - ly)
                    if dist < lr:
                        force = (lr - dist) / lr
                        dx += (x - lx) * force * 0.8 * scale
                        dy += (y - ly) * force * 0.8 * scale
                py5.vertex(x + dx, y + dy)
            py5.end_shape()

    draw_grid((255, 0, 80, 80), 1.05, 1.0)
    draw_grid((0, 255, 100, 80), 1.00, 1.0)
    draw_grid((0, 100, 255, 80), 0.95, 1.0)
    
    py5.blend_mode(py5.BLEND)

    # Save frame
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

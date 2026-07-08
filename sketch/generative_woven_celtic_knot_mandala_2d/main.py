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
    
def draw_woven_arc(x, y, r, start_a, end_a, col, thickness):
    py5.no_fill()
    py5.stroke_cap(py5.SQUARE)
    
    # Shadow
    py5.stroke_weight(thickness + 15)
    py5.stroke(0, 0, 0, 80)
    py5.arc(x, y, r, r, start_a, end_a)
    
    # Core
    py5.stroke_weight(thickness)
    py5.stroke(*col)
    py5.arc(x, y, r, r, start_a, end_a)
    
def draw():
    py5.background(20, 15, 10) # Dark rich background
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.01
    
    rings = 14
    nodes = 12
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # We draw inner to outer to layer correctly
    for ring in range(1, rings + 1):
        radius = ring * 100
        thickness = 50 - ring * 1.5
        
        hue = (ring * 25 + py5.frame_count * 0.5) % 360
        c = (hue, 85, 90, 95)
        
        for n in range(nodes):
            angle_offset = (py5.TWO_PI / nodes) * n
            
            wave = py5.sin(t * 2 + ring * 0.5 + n) * 40
            
            speed = 0.5 if ring % 2 == 0 else -0.5
            start_a = angle_offset + t * speed
            end_a = start_a + py5.PI / 4 + py5.sin(t * 3 + ring) * 0.2
            
            draw_woven_arc(0, 0, radius + wave, start_a, end_a, c, thickness)

    py5.color_mode(py5.RGB, 255)
    
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

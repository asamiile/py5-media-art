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

# Grid settings
SPACING = 50
COLS = int(3840 / SPACING) + 20
ROWS = int(4000 / SPACING)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
def draw():
    py5.background(280, 80, 10) 
    
    py5.push_matrix()
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Draw retro sun first in background
    py5.no_stroke()
    # Sun gradient
    for r in range(800, 0, -10):
        alpha_sun = py5.remap(r, 0, 800, 100, 0)
        py5.fill(330, 90, 100, alpha_sun)
        py5.circle(0, -300, r)
        
    t = py5.frame_count * 0.1
    
    py5.stroke_weight(3)
    
    FOV = 1200
    
    # Draw grid from back to front (rows to 0)
    for y in range(ROWS - 1, 0, -1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            x_idx = x - COLS / 2
            
            # Z is depth moving away
            z1 = y * SPACING + 10
            z2 = (y - 1) * SPACING + 10
            
            n1 = py5.os_noise(x * 0.1, y * 0.1 - t, t * 0.05)
            n2 = py5.os_noise(x * 0.1, (y - 1) * 0.1 - t, t * 0.05)
            
            h1 = py5.remap(n1, 0, 1, -500, 500)
            h2 = py5.remap(n2, 0, 1, -500, 500)
            
            road_dist = abs(x_idx)
            if road_dist < 6:
                road_factor = py5.remap(road_dist, 0, 6, 0, 1)
                h1 *= (road_factor ** 2)
                h2 *= (road_factor ** 2)
                
            scale1 = FOV / (FOV + z1)
            px1 = x_idx * SPACING * scale1
            py_coord1 = (z1 * 0.3 - h1) * scale1 + 200
            
            scale2 = FOV / (FOV + z2)
            px2 = x_idx * SPACING * scale2
            py_coord2 = (z2 * 0.3 - h2) * scale2 + 200
            
            hue1 = (300 + py5.remap(h1, -500, 500, -60, 60)) % 360
            hue2 = (300 + py5.remap(h2, -500, 500, -60, 60)) % 360
            
            # Distance fade (y=ROWS is back, y=0 is front)
            alpha1 = py5.remap(y, ROWS, 0, 0, 100)
            alpha2 = py5.remap(y - 1, ROWS, 0, 0, 100)
            
            # Base color for the triangles
            py5.fill(280, 80, 5, alpha1)
            py5.stroke(hue1, 90, 100, alpha1)
            py5.vertex(px1, py_coord1)
            
            py5.fill(280, 80, 5, alpha2)
            py5.stroke(hue2, 90, 100, alpha2)
            py5.vertex(px2, py_coord2)
            
        py5.end_shape()

    py5.pop_matrix()

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

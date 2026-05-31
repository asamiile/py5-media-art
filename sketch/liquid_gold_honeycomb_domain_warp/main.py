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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global hex_radius, cols, rows
    hex_radius = 45
    x_offset = np.sqrt(3) * hex_radius
    y_offset = 1.5 * hex_radius
    cols = int(SIZE[0] / x_offset) + 3
    rows = int(SIZE[1] / y_offset) + 3

def hexagon(x, y, r):
    py5.begin_shape()
    for i in range(6):
        angle = py5.PI / 3 * i - py5.PI / 6
        py5.vertex(x + r * np.cos(angle), y + r * np.sin(angle))
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(10, 80, 10) # Dark rich amber/brown
    py5.no_stroke()
    
    t = py5.frame_count * 0.015
    
    x_offset = np.sqrt(3) * hex_radius
    y_offset = 1.5 * hex_radius
    
    for row in range(rows):
        for col in range(cols):
            x = col * x_offset + (x_offset / 2 if row % 2 else 0)
            y = row * y_offset
            
            # Domain Warping using multiple noise passes
            dx = py5.os_noise(x * 0.002, y * 0.002, t) * 400
            dy = py5.os_noise(y * 0.002, x * 0.002, t + 100) * 400
            
            # Second pass
            n = py5.os_noise((x + dx) * 0.005, (y + dy) * 0.005, t * 0.5)
            
            # Map noise to visual properties
            mapped_r = py5.remap(n, 0, 1, hex_radius * 0.1, hex_radius * 1.5)
            hue = (35 + 40 * n) % 360 # Gold to amber
            
            if n > 0.6:
                py5.fill(hue, 80, 100, 90) # bright gold
            else:
                py5.fill(hue, 90, 40, 70)  # deep amber shadow
                
            with py5.push_matrix():
                py5.translate(x, y)
                py5.rotate(n * py5.PI)
                hexagon(0, 0, mapped_r)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

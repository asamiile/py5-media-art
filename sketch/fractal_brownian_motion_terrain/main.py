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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS = 60
ROWS = 60
SCALE = 40.0
W = COLS * SCALE
H = ROWS * SCALE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(0)
    
    # Setup camera for a dramatic flyover
    py5.translate(py5.width / 2, py5.height / 2 + 200, -300)
    py5.rotate_x(py5.PI / 2.5)
    
    # We want to fly over the terrain, so we offset the Y axis by time
    flying_speed = 0.05
    y_offset_base = py5.frame_count * flying_speed
    
    py5.translate(-W / 2, -H / 2)
    
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Generate and draw terrain strips
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Compute Z height using 2D Perlin noise
            # Multiply x and y by a small factor to make noise smoother
            noise_x = x * 0.1
            
            # Row 1
            noise_y1 = (y * 0.1) - y_offset_base
            z1 = py5.noise(noise_x, noise_y1) * 400.0 - 150.0
            
            # Row 2 (the next row for the triangle strip)
            noise_y2 = ((y + 1) * 0.1) - y_offset_base
            z2 = py5.noise(noise_x, noise_y2) * 400.0 - 150.0
            
            # Distance from center for fading
            dist_x = abs(x - COLS/2.0) / (COLS/2.0)
            dist_y = abs(y - ROWS/2.0) / (ROWS/2.0)
            fade = 1.0 - max(dist_x, dist_y)
            fade = max(0, fade)
            
            # Color mapping based on height
            hue = (py5.frame_count * 0.5 + z1 * 0.5) % 360
            py5.stroke(hue, 80, 100, 255 * fade)
            
            # Draw two vertices to form the triangle strip
            py5.vertex(x * SCALE, y * SCALE, z1)
            py5.vertex(x * SCALE, (y + 1) * SCALE, z2)
            
        py5.end_shape()
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

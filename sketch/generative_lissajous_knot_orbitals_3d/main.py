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
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    # Motion blur trail effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 40)
    py5.push_matrix()
    py5.translate(0, 0, -500) # Draw background plane far back
    py5.rect(-py5.width*2, -py5.height*2, py5.width*4, py5.height*4)
    py5.pop_matrix()
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    time_t = py5.frame_count * 0.015
    
    py5.rotate_x(time_t * 0.3)
    py5.rotate_y(time_t * 0.5)
    py5.rotate_z(time_t * 0.2)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    num_knots = 5
    resolution = 500
    base_radius = min(py5.width, py5.height) * 0.35
    
    for k in range(num_knots):
        py5.stroke_weight(3 + k)
        
        # Evolving parametric constants
        A = 3.0 + np.sin(time_t * 0.5 + k)
        B = 2.0 + np.cos(time_t * 0.4 - k)
        C = 4.0 + np.sin(time_t * 0.3 + k * 0.5)
        
        phase_x = time_t + k * py5.TWO_PI / num_knots
        phase_y = time_t * 1.2
        phase_z = time_t * 0.8
        
        py5.begin_shape()
        for i in range(resolution + 1): # +1 to close loop
            t = i * py5.TWO_PI / resolution
            
            x = base_radius * np.sin(A * t + phase_x)
            y = base_radius * np.sin(B * t + phase_y)
            z = base_radius * np.sin(C * t + phase_z)
            
            hue = (i / resolution * 360 + time_t * 50 + k * 60) % 360
            py5.stroke(hue, 90, 100, 150)
            
            py5.vertex(x, y, z)
            
        py5.end_shape()

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

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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Data for grid
COLS = 80
ROWS = 80
SPACING = 25
W = (COLS - 1) * SPACING
H = (ROWS - 1) * SPACING

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    # Subtle blur instead of pure ADD
    py5.push_matrix()
    py5.reset_matrix()
    py5.no_lights()
    py5.fill(0, 0, 0, 15)  # semi-transparent black for motion blur
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()

    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    # Rotate scene slowly
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.005)

    py5.translate(-W / 2, -H / 2)

    # Glitch factor
    time = py5.frame_count * 0.015
    glitch_intensity = py5.noise(time * 5)
    is_glitching = glitch_intensity > 0.7

    py5.no_fill()
    
    # Render with chromatic aberration simulation (drawing twice with slight offsets if glitching)
    passes = 2 if is_glitching else 1
    
    for p in range(passes):
        if p == 0:
            py5.stroke(200, 80, 80, 80) # Cyan base
            offsetX = 0
            offsetY = 0
        else:
            py5.stroke(320, 80, 80, 80) # Magenta glitch offset
            offsetX = py5.random(-20, 20) * ((glitch_intensity-0.7)/0.3)
            offsetY = py5.random(-20, 20) * ((glitch_intensity-0.7)/0.3)

        py5.push_matrix()
        py5.translate(offsetX, offsetY)
        
        for y in range(ROWS - 1):
            py5.begin_shape(py5.TRIANGLE_STRIP)
            for x in range(COLS):
                for dy in (0, 1):
                    px = x * SPACING
                    py = (y + dy) * SPACING
                    
                    # Noise height
                    nz = py5.noise(x * 0.05, (y + dy) * 0.05, time) * 400
                    
                    # Add intense sharp spikes on glitch
                    if is_glitching and py5.random(1) < 0.05:
                        nz += py5.random(-200, 200)

                    py5.vertex(px, py, nz)
            py5.end_shape()
            
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
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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

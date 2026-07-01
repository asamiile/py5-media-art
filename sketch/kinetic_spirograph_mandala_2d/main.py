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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Pre-calculate an array of parameter values for the spirographs
NUM_RINGS = 60
ring_offsets = np.linspace(0, py5.TWO_PI, NUM_RINGS)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global theta
    # 5000 points per ring to make it super smooth
    theta = np.linspace(0, py5.TWO_PI * 10, 5000)

def draw():
    # Subtle motion blur
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    cx, cy = py5.width / 2, py5.height / 2
    
    # Base radiuses
    R = py5.height * 0.3
    r = py5.height * 0.08
    d = py5.height * 0.15
    
    # We will draw `NUM_RINGS` spirographs
    for i in range(NUM_RINGS):
        offset = ring_offsets[i]
        
        # Animate the inner gear radius and pen distance over time
        # This causes the spirographs to warp and morph
        dyn_r = r + np.sin(t * py5.TWO_PI + offset) * (py5.height * 0.05)
        dyn_d = d + np.cos(t * py5.TWO_PI * 2.0 + offset * 2.0) * (py5.height * 0.05)
        
        # Hypotrochoid equations
        # x(theta) = (R - r)*cos(theta) + d*cos((R-r)/r * theta)
        # y(theta) = (R - r)*sin(theta) - d*sin((R-r)/r * theta)
        
        x = cx + (R - dyn_r) * np.cos(theta + offset + t * py5.TWO_PI) + dyn_d * np.cos((R - dyn_r) / dyn_r * theta)
        y = cy + (R - dyn_r) * np.sin(theta + offset + t * py5.TWO_PI) - dyn_d * np.sin((R - dyn_r) / dyn_r * theta)
        
        points = np.column_stack((x, y))
        
        py5.stroke_weight(2)
        
        # Interpolate color based on ring index
        r_col = py5.remap(i, 0, NUM_RINGS, 50, 255)
        g_col = py5.remap(i, 0, NUM_RINGS, 200, 50)
        b_col = py5.remap(np.sin(offset + t * py5.TWO_PI), -1, 1, 50, 255)
        
        py5.stroke(r_col, g_col, b_col, 50)
        py5.no_fill()
        
        py5.begin_shape()
        py5.vertices(points)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

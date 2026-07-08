from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import math
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

MAX_DEPTH = 13
lines_by_depth = [[] for _ in range(MAX_DEPTH + 1)]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 12, 15)
    FRAMES_DIR.mkdir(exist_ok=True)

def compute_tree(x, y, angle, length, depth, t):
    if depth == 0:
        return
    
    ex = x + math.cos(angle) * length
    ey = y + math.sin(angle) * length
    
    lines_by_depth[depth].extend([x, y, ex, ey])
    
    # Noise for wind
    nx = ex * 0.0005
    ny = ey * 0.0005
    
    # Wind flows across the screen
    # t moves the noise field
    wind_x = t * 0.5
    wind_y = t * 0.2
    
    n1 = py5.os_noise(nx + wind_x, ny + wind_y, t * 0.5)
    n2 = py5.os_noise(nx + wind_x + 10, ny + wind_y + 10, t * 0.5)
    
    # Sway
    sway1 = (n1 - 0.5) * 1.2
    sway2 = (n2 - 0.5) * 1.2
    
    angle1 = angle - 0.4 + sway1
    angle2 = angle + 0.4 + sway2
    
    # Depth affects branch length decay
    new_len = length * 0.78
    
    compute_tree(ex, ey, angle1, new_len, depth - 1, t)
    compute_tree(ex, ey, angle2, new_len, depth - 1, t)

def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 12, 15, 60)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.015
    
    # Clear lines
    for i in range(MAX_DEPTH + 1):
        lines_by_depth[i].clear()
        
    # Start tree at bottom center
    # Add a slight slow sway to the root
    root_angle = -math.pi / 2.0 + math.sin(t * 0.5) * 0.1
    compute_tree(SIZE[0] / 2, SIZE[1], root_angle, SIZE[1] * 0.22, MAX_DEPTH, t)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    # Render from bottom (MAX_DEPTH) to tips (1)
    for depth in range(MAX_DEPTH, 0, -1):
        lines = lines_by_depth[depth]
        if not lines:
            continue
            
        ratio = depth / float(MAX_DEPTH)
        
        # Deep crimson/brown to bright yellow/white
        r = py5.remap(ratio, 1, 0, 100, 255)
        g = py5.remap(ratio, 1, 0, 10, 255)
        b = py5.remap(ratio, 1, 0, 10, 200)
        
        sw = ratio * 15.0 + 1.0
        py5.stroke_weight(sw)
        
        # Less alpha for thicker branches to glow softly
        alpha = py5.remap(ratio, 1, 0, 100, 255)
        py5.stroke(r, g, b, alpha)
        
        py5.begin_shape(py5.LINES)
        for i in range(0, len(lines), 4):
            py5.vertex(lines[i], lines[i+1])
            py5.vertex(lines[i+2], lines[i+3])
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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

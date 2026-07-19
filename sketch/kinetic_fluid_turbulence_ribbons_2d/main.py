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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

n_ribbons = 800
tail_length = 30
ribbons_x = None
ribbons_y = None
colors = None

def get_curl(x, y, t):
    eps = 0.1
    n1 = py5.os_noise(x, y + eps, t)
    n2 = py5.os_noise(x, y - eps, t)
    n3 = py5.os_noise(x + eps, y, t)
    n4 = py5.os_noise(x - eps, y, t)
    
    a = (n1 - n2) / (2 * eps)
    b = (n3 - n4) / (2 * eps)
    return np.array([a, -b])

def setup():
    global ribbons_x, ribbons_y, colors
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    ribbons_x = np.zeros((n_ribbons, tail_length))
    ribbons_y = np.zeros((n_ribbons, tail_length))
    
    colors = []
    
    for i in range(n_ribbons):
        cx = random.uniform(0, SIZE[0])
        cy = random.uniform(0, SIZE[1])
        ribbons_x[i, :] = cx
        ribbons_y[i, :] = cy
        
        c_rand = random.random()
        if c_rand < 0.4:
            colors.append((0, 255, 255)) # Cyan
        elif c_rand < 0.8:
            colors.append((255, 0, 255)) # Magenta
        else:
            colors.append((100, 255, 100)) # Lime

def draw():
    global ribbons_x, ribbons_y
    
    py5.background(0, 0, 0, 40)
    py5.blend_mode(py5.ADD)
    
    curr_frame = py5.frame_count
    t = curr_frame * 0.005
    
    for i in range(n_ribbons):
        ribbons_x[i, 1:] = ribbons_x[i, :-1]
        ribbons_y[i, 1:] = ribbons_y[i, :-1]
        
        hx, hy = ribbons_x[i, 0], ribbons_y[i, 0]
        
        curl = get_curl(hx * 0.002, hy * 0.002, t)
        
        hx += curl[0] * 12
        hy += curl[1] * 12
        
        if hx < -100: hx = SIZE[0] + 100
        if hx > SIZE[0] + 100: hx = -100
        if hy < -100: hy = SIZE[1] + 100
        if hy > SIZE[1] + 100: hy = -100
        
        ribbons_x[i, 0] = hx
        ribbons_y[i, 0] = hy
        
        py5.no_fill()
        c = colors[i]
        py5.stroke_weight(2.0)
        
        py5.begin_shape()
        for j in range(tail_length):
            alpha = int(py5.remap(j, 0, tail_length, 255, 0))
            py5.stroke(c[0], c[1], c[2], alpha)
            py5.vertex(ribbons_x[i, j], ribbons_y[i, j])
        py5.end_shape()

    py5.blend_mode(py5.BLEND)

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

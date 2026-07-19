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

NUM_PARTICLES = 300000
particles = np.random.uniform(-3.0, 3.0, (NUM_PARTICLES, 2)).astype(np.float32)

a_target, b_target, c_target, d_target = 1.4, -2.3, 2.4, -2.1
a, b, c, d = a_target, b_target, c_target, d_target

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global particles, a, b, c, d, a_target, b_target, c_target, d_target
    
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.01
    
    if py5.frame_count % 300 == 0:
        a_target = random.uniform(-3.0, 3.0)
        b_target = random.uniform(-3.0, 3.0)
        c_target = random.uniform(-3.0, 3.0)
        d_target = random.uniform(-3.0, 3.0)
        
    a += (a_target - a) * 0.005
    b += (b_target - b) * 0.005
    c += (c_target - c) * 0.005
    d += (d_target - d) * 0.005
    
    x = particles[:, 0]
    y = particles[:, 1]
    
    nx = np.sin(a * y) - np.cos(b * x)
    ny = np.sin(c * x) - np.cos(d * y)
    
    particles[:, 0] = nx
    particles[:, 1] = ny
    
    screen_x = (nx + 2.5) * (SIZE[0] / 5.0)
    screen_y = (ny + 2.5) * (SIZE[1] / 5.0)
    
    screen_coords = np.column_stack((screen_x, screen_y))
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(1)
    py5.stroke(100, 200, 255, 30)
    
    py5.points(screen_coords)

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

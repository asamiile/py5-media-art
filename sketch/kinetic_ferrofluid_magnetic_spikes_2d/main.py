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

# Mesh parameters
NUM_POINTS = 500
BASE_RADIUS = 300

def get_vertex(angle, layer_scale, t):
    x_n = np.cos(angle)
    y_n = np.sin(angle)
    
    # 2D noise for spikes
    n1 = py5.os_noise(x_n * 2.0, y_n * 2.0, t * 0.5)
    n2 = py5.os_noise(x_n * 6.0 + 100, y_n * 6.0 + 100, t)
    
    spike = max(0, n2 - 0.6) * 4.0
    
    r = BASE_RADIUS * layer_scale + n1 * 300 * layer_scale + spike * 400 * layer_scale
    
    return x_n * r, y_n * r

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(20, 5, 5)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    t = py5.frame_count * 0.02
    
    # Draw several overlapping spiked circles for fake 3D depth
    num_layers = 20
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    for i in range(num_layers, 0, -1):
        layer_scale = py5.remap(i, 0, num_layers, 1.0, 0.1)
        
        c_r = int(py5.remap(i, 0, num_layers, 30, 255))
        c_g = int(py5.remap(i, 0, num_layers, 5, 100))
        c_b = int(py5.remap(i, 0, num_layers, 5, 50))
        alpha = int(py5.remap(i, 0, num_layers, 20, 200))
        
        py5.fill(c_r, c_g, c_b, alpha)
        
        py5.begin_shape()
        for j in range(NUM_POINTS):
            angle = py5.TWO_PI * j / NUM_POINTS
            # Adding slight rotation offset per layer for parallax
            angle_offset = angle + i * 0.05 * np.sin(t)
            vx, vy = get_vertex(angle_offset, layer_scale, t + i * 0.05)
            py5.vertex(vx, vy)
        py5.end_shape(py5.CLOSE)

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

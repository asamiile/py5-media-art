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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    t = py5.frame_count * 0.005
    
    num_strands = 200
    points_per_strand = 40
    
    for i in range(num_strands):
        base_x = py5.remap(i, 0, num_strands-1, -400, SIZE[0] + 400)
        
        r = int(py5.remap(np.sin(i * 0.1 + t), -1, 1, 50, 255))
        g = int(py5.remap(np.cos(i * 0.15 + t * 0.8), -1, 1, 50, 150))
        b = int(py5.remap(np.sin(i * 0.05 + t * 1.2), -1, 1, 150, 255))
        alpha = int(py5.remap(np.sin(i + t*3), -1, 1, 30, 90))
        
        py5.stroke(r, g, b, alpha)
        py5.stroke_weight(py5.remap(np.sin(i*0.5 + t*5), -1, 1, 1, 6))
        
        py5.begin_shape()
        for j in range(points_per_strand):
            py = py5.remap(j, 0, points_per_strand-1, -200, SIZE[1] + 200)
            
            noise_val = py5.os_noise(base_x * 0.001, py * 0.001 + t * 2.0, t)
            offset = py5.remap(noise_val, 0, 1, -400, 400)
            
            noise_val2 = py5.os_noise(base_x * 0.005, py * 0.005 - t, t * 1.5)
            offset += py5.remap(noise_val2, 0, 1, -100, 100)
            
            px = base_x + offset
            
            py5.curve_vertex(px, py)
        py5.end_shape()

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

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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_ring_set(x, y, max_r, num_rings, hue_col):
    py5.push_matrix()
    py5.translate(x, y)
    
    for i in range(num_rings):
        r = (i * max_r / num_rings)
        py5.stroke(hue_col[0], hue_col[1], hue_col[2], 180)
        py5.stroke_weight(4)
        py5.ellipse(0, 0, r * 2, r * 2)
        
    py5.pop_matrix()

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    time = py5.frame_count * 0.05
    
    # Layer 1: Center
    draw_ring_set(py5.width/2, py5.height/2, 2000, 100, (0, 255, 255))
    
    # Layer 2: Orbiting
    ox = py5.width/2 + np.cos(time * 0.5) * 200
    oy = py5.height/2 + np.sin(time * 0.7) * 200
    draw_ring_set(ox, oy, 2000, 100, (255, 0, 255))
    
    # Layer 3: Expanding
    scale_factor = 1.0 + np.sin(time) * 0.2
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.scale(scale_factor)
    py5.translate(-py5.width/2, -py5.height/2)
    draw_ring_set(py5.width/2, py5.height/2, 2000, 100, (255, 255, 255))
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

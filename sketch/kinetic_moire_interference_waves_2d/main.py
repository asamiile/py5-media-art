import os
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
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.no_fill()

def draw():
    py5.background(245, 245, 240)
    
    t = (py5.frame_count / TOTAL_FRAMES) * 2 * np.pi
    
    # Calculate the positions of the two focal points
    # They orbit the center slowly
    cx1 = py5.width/2 + np.cos(t) * 200
    cy1 = py5.height/2 + np.sin(t * 1.5) * 150
    
    cx2 = py5.width/2 + np.cos(t + np.pi) * 200
    cy2 = py5.height/2 + np.sin(t * 1.5 + np.pi) * 150

    max_radius = int(np.sqrt(py5.width**2 + py5.height**2)) + 500
    num_rings = 150
    
    py5.stroke(16, 0, 48, 180) # Deep Indigo
    py5.stroke_weight(4)
    
    # First set of rings
    for i in range(num_rings):
        r = i * 25 + (t * 50) % 25
        if r > 0:
            py5.stroke_weight(3 + 2 * np.sin(i * 0.1 - t))
            py5.circle(cx1, cy1, r * 2)
            
    # Second set of rings
    py5.stroke(208, 16, 32, 180) # Crimson Red
    for i in range(num_rings):
        r = i * 25 + (t * 50) % 25
        if r > 0:
            py5.stroke_weight(3 + 2 * np.cos(i * 0.1 - t))
            py5.circle(cx2, cy2, r * 2)

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
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()

from pathlib import Path
import shutil
import subprocess
import sys
import math
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
    
def draw_radial_lines(num_lines, outer_radius, inner_radius=0):
    for i in range(num_lines):
        a = (py5.TWO_PI / num_lines) * i
        x1 = math.cos(a) * inner_radius
        y1 = math.sin(a) * inner_radius
        x2 = math.cos(a) * outer_radius
        y2 = math.sin(a) * outer_radius
        py5.line(x1, y1, x2, y2)

def draw():
    py5.background(10)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.005
    
    py5.stroke(240)
    py5.stroke_weight(3)
    
    # Two offset rotating centers for deep moire
    py5.push_matrix()
    py5.translate(math.cos(t * 2) * 50, math.sin(t * 1.5) * 50)
    py5.rotate(t * 0.5)
    draw_radial_lines(360, 3000, 50)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.translate(math.cos(t * 1.8 + py5.PI) * 50, math.sin(t * 2.1 + py5.PI) * 50)
    py5.rotate(-t * 0.6)
    draw_radial_lines(360, 3000, 50)
    py5.pop_matrix()
    
    # Layer 3: Concentric circles that scale
    py5.no_fill()
    num_circles = 80
    base_r = (py5.frame_count * 2) % 40  # Infinite zooming outward effect
    
    for i in range(num_circles):
        r = base_r + i * 40
        sw = 3 + py5.sin(t * 10 - i * 0.2) * 2
        py5.stroke_weight(max(0.5, sw))
        
        # Occasional red highlight circle
        if (i + int(base_r/40)) % 15 == 0:
            py5.stroke(255, 30, 50)
        else:
            py5.stroke(255)
            
        py5.circle(0, 0, r * 2)

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

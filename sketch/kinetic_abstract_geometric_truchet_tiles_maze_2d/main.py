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

CELL_SIZE = 80
COLS = SIZE[0] // CELL_SIZE + 2
ROWS = SIZE[1] // CELL_SIZE + 2

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.rect_mode(py5.CENTER)
    
def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def draw():
    py5.background(15, 20, 25)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.stroke_weight(12)
    py5.stroke_cap(py5.SQUARE)
    
    cos_t = math.cos(loop_t)
    sin_t = math.sin(loop_t)
    
    for i in range(COLS):
        for j in range(ROWS):
            x = i * CELL_SIZE - CELL_SIZE / 2
            y = j * CELL_SIZE - CELL_SIZE / 2
            
            n_val = py5.noise(i * 0.08, j * 0.08, cos_t * 0.4 + 1.0)
            n_val2 = py5.noise(i * 0.08, j * 0.08, sin_t * 0.4 + 1.0)
            
            rot_target = (n_val + n_val2) * 2.0 
            
            base_quad = math.floor(rot_target)
            fract = rot_target - base_quad
            
            smooth_fract = ease_in_out_cubic(fract)
            
            rotation = (base_quad + smooth_fract) * py5.PI / 2
            
            dist = math.sqrt((x - SIZE[0]/2)**2 + (y - SIZE[1]/2)**2)
            hue = (dist * 0.1 + t * 360) % 360
            
            # Pulsing thickness
            thick = 8 + math.sin(dist * 0.01 - loop_t * 2) * 4
            py5.stroke_weight(thick)
            
            py5.stroke(hue, 80, 90)
            
            py5.push_matrix()
            py5.translate(x, y)
            py5.rotate(rotation)
            
            py5.no_fill()
            
            py5.arc(-CELL_SIZE/2, -CELL_SIZE/2, CELL_SIZE, CELL_SIZE, 0, py5.PI/2)
            py5.arc(CELL_SIZE/2, CELL_SIZE/2, CELL_SIZE, CELL_SIZE, py5.PI, py5.PI + py5.PI/2)
            
            py5.pop_matrix()

    py5.color_mode(py5.RGB, 255)

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

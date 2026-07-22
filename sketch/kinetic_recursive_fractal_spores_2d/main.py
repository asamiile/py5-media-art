from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_spore(depth, len_mult, t):
    if depth == 0:
        return
        
    py5.line(0, 0, 0, -len_mult)
    py5.translate(0, -len_mult)
    
    n_branches = 3
    for i in range(n_branches):
        py5.push_matrix()
        
        # rotation
        angle = py5.PI / 3.0 * (i - 1) + py5.noise(depth, i, t) * py5.PI / 2.0 - py5.PI / 4.0
        py5.rotate(angle)
        
        # Color based on depth
        if depth > 4:
            py5.stroke(255, 48, 32, 180) # Deep vermilion
        elif depth > 2:
            py5.stroke(255, 160, 64, 150) # Soft orange
        else:
            py5.stroke(255, 255, 255, 100) # Bright tips
            
        py5.stroke_weight(depth * 0.8)
        
        draw_spore(depth - 1, len_mult * 0.75, t)
        
        py5.pop_matrix()

def draw():
    py5.background(21, 16, 16) # Dark warm grey
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    py5.translate(SIZE[0] / 2, SIZE[1] * 0.8)
    
    # We will draw a few spore clusters from the center
    for i in range(5):
        py5.push_matrix()
        py5.rotate(py5.TWO_PI / 5 * i + t * 0.5)
        py5.translate(100, 0)
        
        draw_spore(7, 200, t + i*10)
        py5.pop_matrix()

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

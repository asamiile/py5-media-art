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
    py5.background(0)
    
def subdivide(x, y, w, h, depth, max_depth, t):
    # Calculate noise at the center of this rectangle
    nx = x + w / 2
    ny = y + h / 2
    
    n_val = py5.os_noise(nx * 0.002, ny * 0.002, t)
    
    # If we haven't reached max depth and the noise threshold allows, subdivide
    if depth < max_depth and n_val > (depth / max_depth) * 0.8:
        # Split vertically or horizontally based on aspect ratio and random noise
        split_vert = (w > h) if w != h else (py5.os_noise(nx * 0.01, ny * 0.01) > 0.5)
        
        # Add some variation to the split point
        split_ratio = 0.3 + 0.4 * py5.os_noise(nx * 0.005, ny * 0.005, t + 10)
        
        if split_vert:
            sw = w * split_ratio
            subdivide(x, y, sw, h, depth + 1, max_depth, t)
            subdivide(x + sw, y, w - sw, h, depth + 1, max_depth, t)
        else:
            sh = h * split_ratio
            subdivide(x, y, w, sh, depth + 1, max_depth, t)
            subdivide(x, y + sh, w, h - sh, depth + 1, max_depth, t)
    else:
        # Draw the rectangle
        # Map noise to color
        hue_val = py5.os_noise(nx * 0.003, ny * 0.003, t * 0.5)
        
        py5.color_mode(py5.HSB, 360, 100, 100, 100)
        
        if hue_val < 0.33:
            c = py5.color(186, 100, 100, 80) # Electric Blue
        elif hue_val < 0.66:
            c = py5.color(275, 80, 88, 80) # Purple
        else:
            c = py5.color(120, 75, 80, 80) # Lime Green
            
        py5.fill(c)
        py5.stroke(0, 0, 100, 90) # White borders like stained glass
        py5.stroke_weight(2)
        
        # Slight margin for tiles
        m = 2
        py5.rect(x + m, y + m, w - m*2, h - m*2)
        py5.color_mode(py5.RGB, 255)

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.01
    
    # Start subdivision
    subdivide(100, 100, py5.width - 200, py5.height - 200, 0, 7, t)
    
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

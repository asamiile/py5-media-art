from pathlib import Path
import shutil
import subprocess
import sys
import random
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

NUM_PARTICLES = 1_000_000
pts_x = np.random.uniform(-2, 2, NUM_PARTICLES).astype(np.float32)
pts_y = np.random.uniform(-2, 2, NUM_PARTICLES).astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5, 0, 5)

def draw():
    global pts_x, pts_y
    
    # Very slight clear for long trailing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 0, 5, 5) # Reduced fade for longer trails
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    # Clifford Attractor parameters drifting over time
    a = -1.4 + py5.noise(t, 0) * 2.8
    b = 1.6 + py5.noise(t, 10) * 1.0
    c = 1.0 + py5.noise(t, 20) * 1.5
    d = 0.7 + py5.noise(t, 30) * 1.5
    
    # Vectorized step
    x_new = np.sin(a * pts_y) + c * np.cos(a * pts_x)
    y_new = np.sin(b * pts_x) + d * np.cos(b * pts_y)
    
    pts_x[:] = x_new
    pts_y[:] = y_new
    
    # Map to screen coordinates
    scale = SIZE[1] / 5.5
    screen_x = SIZE[0]/2 + pts_x * scale
    screen_y = SIZE[1]/2 + pts_y * scale
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(4) # Very thick
    
    # Solid bright colors
    r = 255
    g = 180 + np.cos(t*4)*75
    b_col = 150 + np.sin(t*2)*100
    
    py5.stroke(r, g, b_col, 150) # High alpha
    py5.points(np.column_stack((screen_x, screen_y)))

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

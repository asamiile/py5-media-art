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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(10, 15)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Dense grid of points
GRID_SIZE = 150
xs = np.linspace(0, SIZE[0], GRID_SIZE)
ys = np.linspace(0, SIZE[1], GRID_SIZE)
X, Y = np.meshgrid(xs, ys)
X_flat = X.flatten()
Y_flat = Y.flatten()
NUM_POINTS = len(X_flat)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    py5.background(0)

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.02
    
    # Mathematical interference pattern
    z1 = np.sin(X_flat * 0.01 + t) * np.cos(Y_flat * 0.01 - t)
    z2 = np.sin(np.sqrt((X_flat - SIZE[0]/2)**2 + (Y_flat - SIZE[1]/2)**2) * 0.02 - t*2)
    
    z = z1 + z2
    
    # Calculate radius and hue based on interference
    radii = np.abs(z) * 10
    hues = (z * 60 + 200 + t * 50) % 360
    
    py5.begin_shape(py5.POINTS)
    py5.stroke_weight(4)
    for i in range(NUM_POINTS):
        # We only draw points where interference is strong to create contours
        if radii[i] > 5:
            py5.stroke(hues[i], 80, 100, 80)
            py5.vertex(X_flat[i], Y_flat[i])
    py5.end_shape()
    py5.no_stroke()

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

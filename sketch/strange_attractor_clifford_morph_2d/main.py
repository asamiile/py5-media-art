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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def get_clifford_params(t):
    # Slowly morphing parameters for the Clifford Attractor
    a = 1.5 + np.sin(t * 0.5) * 0.5
    b = -1.5 + np.cos(t * 0.4) * 0.6
    c = 1.0 + np.sin(t * 0.3) * 0.8
    d = 0.5 + np.cos(t * 0.6) * 1.0
    return a, b, c, d

def draw():
    py5.blend_mode(py5.BLEND)
    # Give a slight fade for motion blur
    py5.fill(10, 80, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    a, b, c, d = get_clifford_params(t)
    
    num_points = 500000
    iters = 1
    
    # Initialize random starting points
    x = np.random.uniform(-1, 1, num_points).astype(np.float32)
    y = np.random.uniform(-1, 1, num_points).astype(np.float32)
    
    # Iterate Clifford equations
    # x_{n+1} = sin(a y_n) + c cos(a x_n)
    # y_{n+1} = sin(b x_n) + d cos(b y_n)
    # Actually standard clifford is:
    # xn+1 = sin(a y) + c cos(a x)
    # yn+1 = sin(b x) + d cos(b y)
    
    for _ in range(iters):
        nx = np.sin(a * y) + c * np.cos(a * x)
        ny = np.sin(b * x) + d * np.cos(b * y)
        x, y = nx, ny
        
    # Scale and center
    scale = 400
    screen_x = x * scale + py5.width / 2
    screen_y = y * scale + py5.height / 2
    
    py5.stroke_weight(1)
    
    hue = (220 + t * 20) % 360
    py5.stroke(hue, 80, 100, 5)
    
    # Fast drawing with shape
    py5.begin_shape(py5.POINTS)
    for i in range(num_points):
        py5.vertex(screen_x[i], screen_y[i])
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

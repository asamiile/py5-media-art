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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 80000

px = np.random.uniform(-1, 1, NUM_PARTICLES)
py = np.random.uniform(-1, 1, NUM_PARTICLES)
p_hue = np.random.uniform(35, 55, NUM_PARTICLES) 

def chladni(x, y, n, m):
    return np.cos(n * np.pi * x) * np.cos(m * np.pi * y) - np.cos(m * np.pi * x) * np.cos(n * np.pi * y)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(220, 80, 5)
    
def draw():
    global px, py
    
    py5.no_stroke()
    py5.fill(220, 80, 5, 25)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    n = 3.0 + np.sin(t * 1.5) * 1.5
    m = 4.0 + np.cos(t * 1.2) * 2.0
    
    eps = 0.01
    lr = 0.003
    
    Z = chladni(px, py, n, m)
    Z2 = Z**2
    
    Z_dx = chladni(px + eps, py, n, m)**2
    Z_dy = chladni(px, py + eps, n, m)**2
    
    grad_x = (Z_dx - Z2) / eps
    grad_y = (Z_dy - Z2) / eps
    
    px -= lr * grad_x + np.random.normal(0, 0.005, NUM_PARTICLES)
    py -= lr * grad_y + np.random.normal(0, 0.005, NUM_PARTICLES)
    
    px = np.where(px > 1, -1, px)
    px = np.where(px < -1, 1, px)
    py = np.where(py > 1, -1, py)
    py = np.where(py < -1, 1, py)
    
    screen_x = (px + 1) * 0.5 * SIZE[0]
    screen_y = (py + 1) * 0.5 * SIZE[1]
    
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        z_abs = min(abs(Z[i]), 1.0)
        brightness = 100 - z_abs * 70
        alpha = 90 - z_abs * 80
        py5.stroke(p_hue[i], 80 - z_abs*60, brightness, alpha)
        py5.vertex(screen_x[i], screen_y[i])
    py5.end_shape()

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

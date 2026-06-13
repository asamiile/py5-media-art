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

density_map = None

def setup():
    global density_map
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    density_map = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def draw():
    global density_map
    
    t = py5.frame_count * 0.005
    
    a = 1.4 + 0.3 * np.sin(t * 1.1)
    b = -2.3 + 0.3 * np.cos(t * 1.3)
    c = 2.4 + 0.3 * np.sin(t * 0.9)
    d = -2.1 + 0.3 * np.cos(t * 1.5)
    
    N = 300000
    x = np.random.uniform(-2, 2, size=(N,)).astype(np.float32)
    y = np.random.uniform(-2, 2, size=(N,)).astype(np.float32)
    
    iters = 15
    
    scale = py5.height * 0.22
    cx, cy = py5.width / 2, py5.height / 2
    
    density_map *= 0.85
    
    for _ in range(iters):
        nx = np.sin(a * y) - np.cos(b * x)
        ny = np.sin(c * x) - np.cos(d * y)
        x, y = nx, ny
        
        px = (cx + x * scale).astype(np.int32)
        py_c = (cy + y * scale).astype(np.int32)
        
        valid = (px >= 0) & (px < py5.width) & (py_c >= 0) & (py_c < py5.height)
        px_v = px[valid]
        py_v = py_c[valid]
        
        np.add.at(density_map, (py_v, px_v), 1.0)
        
    py5.load_np_pixels()
    
    c_val = np.clip(density_map, 0, 100) / 100.0
    c_val = np.power(c_val, 0.7)
    
    r = (c_val * 150).astype(np.uint8)
    g = (c_val * c_val * 255).astype(np.uint8)
    b = (np.clip(c_val * 2.0, 0, 1) * 255).astype(np.uint8)
    alpha = np.full_like(r, 255)
    
    color_arr = np.dstack((alpha, r, g, b))
    
    rh, rw = py5.np_pixels.shape[:2]
    if rh != py5.height or rw != py5.width:
        import cv2
        resized = cv2.resize(color_arr, (rw, rh), interpolation=cv2.INTER_NEAREST)
        py5.np_pixels[:, :, :] = resized
    else:
        py5.np_pixels[:, :, :] = color_arr

    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
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
            
        import os
        os._exit(0)

py5.run_sketch()

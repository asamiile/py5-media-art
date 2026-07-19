from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

W, H = 512, 512
dA = 1.0
dB = 0.5
feed = 0.055
k = 0.062

A = np.ones((H, W), dtype=np.float32)
B = np.zeros((H, W), dtype=np.float32)

cx, cy = W // 2, H // 2
B[cy-10:cy+10, cx-10:cx+10] = 1.0

lapA = np.zeros_like(A)
lapB = np.zeros_like(B)

img = None

def laplacian(Z, out):
    out[:] = -Z
    
    out += np.roll(Z, 1, axis=0) * 0.2
    out += np.roll(Z, -1, axis=0) * 0.2
    out += np.roll(Z, 1, axis=1) * 0.2
    out += np.roll(Z, -1, axis=1) * 0.2
    
    out += np.roll(np.roll(Z, 1, axis=0), 1, axis=1) * 0.05
    out += np.roll(np.roll(Z, -1, axis=0), 1, axis=1) * 0.05
    out += np.roll(np.roll(Z, 1, axis=0), -1, axis=1) * 0.05
    out += np.roll(np.roll(Z, -1, axis=0), -1, axis=1) * 0.05
    
def step():
    global A, B
    laplacian(A, lapA)
    laplacian(B, lapB)
    
    abb = A * B * B
    
    t = py5.frame_count * 0.005
    f = feed + 0.001 * np.sin(t)
    k_var = k + 0.001 * np.cos(t * 0.8)
    
    A += (dA * lapA - abb + f * (1.0 - A)) * 1.0
    B += (dB * lapB + abb - (k_var + f) * B) * 1.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    global img
    img = py5.create_image(W, H, py5.RGB)
    
def draw():
    global A, B
    
    for _ in range(25):
        step()
        
    norm_B = np.clip(B * 2.5, 0, 1)
    
    r = (norm_B ** 2 * 255).astype(np.uint8)
    g = (norm_B * 200).astype(np.uint8)
    b = (norm_B * 0.5 * 255 + 40).astype(np.uint8)
    
    alpha = np.full_like(r, 255)
    
    pixels = np.dstack((alpha, r, g, b))
    
    img.set_np_pixels(pixels)
    
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

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

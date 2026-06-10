from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.ndimage import convolve
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

GRID_H, GRID_W = SIZE[1] // 4, SIZE[0] // 4

A = np.random.rand(GRID_H, GRID_W).astype(np.float32)
B = np.random.rand(GRID_H, GRID_W).astype(np.float32)
C = np.random.rand(GRID_H, GRID_W).astype(np.float32)

KERNEL = np.array([[0.05, 0.2, 0.05],
                   [0.2,  0.0, 0.2],
                   [0.05, 0.2, 0.05]], dtype=np.float32)

def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    
    i = i % 6
    
    r = np.choose(i.astype(np.int32), [v, q, p, p, t, v])
    g = np.choose(i.astype(np.int32), [t, v, v, q, p, p])
    b = np.choose(i.astype(np.int32), [p, p, t, v, v, q])
    
    return np.stack([r, g, b], axis=-1)

img = None

def setup():
    global img
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    img = py5.create_image(GRID_W, GRID_H, py5.ARGB)

def draw():
    global A, B, C
    
    for _ in range(2):
        c_a = convolve(A, KERNEL, mode='wrap')
        c_b = convolve(B, KERNEL, mode='wrap')
        c_c = convolve(C, KERNEL, mode='wrap')
        
        a_new = np.clip(A + A * (1.2 * B - C) - c_a * 0.1, 0, 1)
        b_new = np.clip(B + B * (1.2 * C - A) - c_b * 0.1, 0, 1)
        c_new = np.clip(C + C * (1.2 * A - B) - c_c * 0.1, 0, 1)
        
        A, B, C = a_new, b_new, c_new

    hue = (A * 1.5 + py5.frame_count * 0.002) % 1.0
    sat = 0.5 + 0.5 * B
    val = 0.2 + 0.8 * C
    
    rgb = hsv_to_rgb(hue, sat, val) * 255
    rgb = rgb.astype(np.uint32)
    
    A_chan = np.full((GRID_H, GRID_W), 255, dtype=np.uint32)
    R_chan = rgb[..., 0]
    G_chan = rgb[..., 1]
    B_chan = rgb[..., 2]
    
    img.load_np_pixels()
    
    if img.np_pixels.ndim == 3 and img.np_pixels.shape[2] == 4:
        # It's an array of shape (height, width, 4) containing ARGB channels
        img.np_pixels[..., 0] = 255  # Alpha
        img.np_pixels[..., 1] = R_chan
        img.np_pixels[..., 2] = G_chan
        img.np_pixels[..., 3] = B_chan
    elif img.np_pixels.ndim == 2:
        # It's an array of shape (height, width) containing packed int32 ARGB
        argb_pixels = (A_chan << 24) | (R_chan << 16) | (G_chan << 8) | B_chan
        img.np_pixels[:] = argb_pixels.astype(np.int32)
    elif img.np_pixels.ndim == 1:
        argb_pixels = (A_chan << 24) | (R_chan << 16) | (G_chan << 8) | B_chan
        img.np_pixels[:] = argb_pixels.flatten().astype(np.int32)
        
    img.update_np_pixels()
    
    py5.image(img, 0, 0, py5.width, py5.height)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

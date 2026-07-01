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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
# We simulate at a slightly lower resolution (1920x1080) for speed
# and upscale it when rendering to the canvas
W, H = SIZE[0] // 2, SIZE[1] // 2

# Gray-Scott parameters for "Mitosis" -> "Coral" transition
DA = 1.0
DB = 0.5

A = np.ones((H, W), dtype=np.float32)
B = np.zeros((H, W), dtype=np.float32)

def laplacian(Z):
    # 3x3 Laplacian using fast np.roll
    Z_up = np.roll(Z, 1, axis=0)
    Z_dn = np.roll(Z, -1, axis=0)
    Z_lt = np.roll(Z, 1, axis=1)
    Z_rt = np.roll(Z, -1, axis=1)
    
    Z_ul = np.roll(Z_up, 1, axis=1)
    Z_ur = np.roll(Z_up, -1, axis=1)
    Z_dl = np.roll(Z_dn, 1, axis=1)
    Z_dr = np.roll(Z_dn, -1, axis=1)
    
    return (0.2 * (Z_up + Z_dn + Z_lt + Z_rt) + 
            0.05 * (Z_ul + Z_ur + Z_dl + Z_dr) - 
            1.0 * Z)

def setup():
    global A, B
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.no_smooth()
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed the simulation in the center with noise
    r = 30
    cx, cy = W // 2, H // 2
    y, x = np.ogrid[-cy:H-cy, -cx:W-cx]
    mask = x*x + y*y <= r*r
    B[mask] = 1.0
    B += (np.random.random((H, W)) * 0.1).astype(np.float32)
    
    print("[Setup] Pre-simulating 500 steps...")
    f = 0.0367
    k = 0.0649
    for _ in range(500):
        lapA = laplacian(A)
        lapB = laplacian(B)
        ABB = A * B * B
        
        A += (DA * lapA - ABB + f * (1 - A))
        B += (DB * lapB + ABB - (k + f) * B)
        
        np.clip(A, 0, 1, out=A)
        np.clip(B, 0, 1, out=B)

def draw():
    global A, B
    
    t = py5.frame_count / TOTAL_FRAMES
    
    f = 0.0367 + (0.0545 - 0.0367) * t
    k = 0.0649 + (0.0620 - 0.0649) * t
    
    for _ in range(15):
        lapA = laplacian(A)
        lapB = laplacian(B)
        ABB = A * B * B
        
        A += (DA * lapA - ABB + f * (1 - A))
        B += (DB * lapB + ABB - (k + f) * B)
        
        np.clip(A, 0, 1, out=A)
        np.clip(B, 0, 1, out=B)
        
    # Render using the concentration of B
    # B ranges from 0 to ~0.5. We normalize it.
    B_norm = np.clip(B / 0.4, 0, 1)
    
    # Create an RGB image
    # We map B_norm to a color gradient: Dark Blue -> Magenta -> Glowing Gold
    R = (B_norm * 255).astype(np.uint8)
    G = ((B_norm**2) * 200).astype(np.uint8)
    # Give the background a dark blue tint
    B_channel = np.clip((B_norm * 100) + 15, 0, 255).astype(np.uint8)
    A_channel = np.full((H, W), 255, dtype=np.uint8)
    
    # Stack into an ARGB array
    pixels_1080 = np.dstack((A_channel, R, G, B_channel))
    
    # Create a py5 Image object from the numpy array
    img = py5.create_image_from_numpy(pixels_1080, 'ARGB')
    
    # Scale up to 4K
    py5.image(img, 0, 0, SIZE[0], SIZE[1])
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

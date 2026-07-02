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

# Internal resolution for simulation
SIM_W = 960
SIM_H = 540

A = None
B = None

# Diffusion rates
DA = 1.0
DB = 0.5
dt = 1.0

def setup():
    global A, B
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    A = np.ones((SIM_H, SIM_W), dtype=np.float32)
    B = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    
    # Seed B with some random spots
    for _ in range(50):
        x = np.random.randint(20, SIM_W - 20)
        y = np.random.randint(20, SIM_H - 20)
        w = np.random.randint(5, 15)
        h = np.random.randint(5, 15)
        B[y:y+h, x:x+w] = 1.0

def laplacian(Z):
    # 3x3 Laplacian using fast numpy rolls
    # Weight: center -1, neighbors 0.2, diagonals 0.05
    Ztop = np.roll(Z, 1, axis=0)
    Zbot = np.roll(Z, -1, axis=0)
    Zleft = np.roll(Z, 1, axis=1)
    Zright = np.roll(Z, -1, axis=1)
    
    Ztl = np.roll(Ztop, 1, axis=1)
    Ztr = np.roll(Ztop, -1, axis=1)
    Zbl = np.roll(Zbot, 1, axis=1)
    Zbr = np.roll(Zbot, -1, axis=1)
    
    return (
        Ztop * 0.2 + Zbot * 0.2 + Zleft * 0.2 + Zright * 0.2 +
        Ztl * 0.05 + Ztr * 0.05 + Zbl * 0.05 + Zbr * 0.05 -
        Z * 1.0
    )

def draw():
    global A, B
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Parametric drift for f and k using noise
    # We want f around 0.055 and k around 0.062 (classic coral growth)
    # We will gently sway these parameters to make the pattern evolve
    f = 0.0545 + 0.003 * py5.os_noise(t * 2.0, 0)
    k = 0.0620 + 0.002 * py5.os_noise(t * 2.0, 100)
    
    # Update simulation multiple times per frame
    for _ in range(12):
        lapA = laplacian(A)
        lapB = laplacian(B)
        
        ABB = A * B * B
        
        A += (DA * lapA - ABB + f * (1 - A)) * dt
        B += (DB * lapB + ABB - (k + f) * B) * dt
        
    # Clip values
    np.clip(A, 0, 1, out=A)
    np.clip(B, 0, 1, out=B)
    
    # Map B concentration to color
    # Background: (2, 0, 16)
    # Cyan: (0, 229, 255)
    # Purple: (179, 0, 255)
    # White: (255, 255, 255)
    
    # We want a smooth gradient
    c_b = np.zeros_like(B)
    c_g = np.zeros_like(B)
    c_r = np.zeros_like(B)
    
    # Map B from 0..0.4
    val = B / 0.4
    np.clip(val, 0, 1, out=val)
    
    # Multi-stop gradient
    t1, t2 = 0.4, 0.8
    m1 = val <= t1
    m2 = (val > t1) & (val <= t2)
    m3 = val > t2
    
    # 0 to t1: Dark Blue to Purple
    f1 = val[m1] / t1
    c_b[m1] = 16 + (255 - 16) * f1
    c_g[m1] = 0
    c_r[m1] = 2 + (179 - 2) * f1
    
    # t1 to t2: Purple to Cyan
    f2 = (val[m2] - t1) / (t2 - t1)
    c_b[m2] = 255
    c_g[m2] = 0 + (229 - 0) * f2
    c_r[m2] = 179 + (0 - 179) * f2
    
    # t2 to 1.0: Cyan to White
    f3 = (val[m3] - t2) / (1.0 - t2)
    c_b[m3] = 255
    c_g[m3] = 229 + (255 - 229) * f3
    c_r[m3] = 0 + (255 - 0) * f3
    
    pixels = np.zeros((SIM_H, SIM_W, 4), dtype=np.uint8)
    pixels[..., 0] = c_b.astype(np.uint8)
    pixels[..., 1] = c_g.astype(np.uint8)
    pixels[..., 2] = c_r.astype(np.uint8)
    pixels[..., 3] = 255
    
    # Create image and draw stretched
    img = py5.create_image_from_numpy(pixels, "ARGB")
    
    # Nearest neighbor or bilinear filtering depends on renderer, but Py5 default P2D scales smoothly
    py5.image(img, 0, 0, py5.width, py5.height)
    
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

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

# Run the simulation at 1080p for performance and thicker organic patterns
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

# Gray-Scott reaction-diffusion parameters (coral/mitosis-like growth)
dA = 1.0
dB = 0.5
feed = 0.0545
k = 0.062

A = np.ones((SIM_H, SIM_W), dtype=np.float32)
B = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Seed initial areas
for _ in range(40):
    rx = np.random.randint(50, SIM_W - 50)
    ry = np.random.randint(50, SIM_H - 50)
    A[ry-5:ry+5, rx-5:rx+5] = 0.5
    B[ry-5:ry+5, rx-5:rx+5] = 0.25
    
# To give it some dynamic flavor, feed rate varies slightly across the canvas
x_coords = np.linspace(-1, 1, SIM_W)
y_coords = np.linspace(-1, 1, SIM_H)
X, Y = np.meshgrid(x_coords, y_coords)
feed_map = feed + 0.002 * np.sin(X * 4) * np.cos(Y * 4)

def laplacian(Z):
    Z_up = np.roll(Z, 1, axis=0)
    Z_down = np.roll(Z, -1, axis=0)
    Z_left = np.roll(Z, 1, axis=1)
    Z_right = np.roll(Z, -1, axis=1)
    
    Z_ul = np.roll(Z_up, 1, axis=1)
    Z_ur = np.roll(Z_up, -1, axis=1)
    Z_dl = np.roll(Z_down, 1, axis=1)
    Z_dr = np.roll(Z_down, -1, axis=1)
    
    return (
        0.2 * (Z_up + Z_down + Z_left + Z_right) +
        0.05 * (Z_ul + Z_ur + Z_dl + Z_dr) -
        1.0 * Z
    )

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global A, B
    
    # 25 physics steps per frame for fast visual progression
    for _ in range(25):
        lapA = laplacian(A)
        lapB = laplacian(B)
        
        reaction = A * B * B
        
        A_new = A + (dA * lapA - reaction + feed_map * (1 - A))
        B_new = B + (dB * lapB + reaction - (k + feed_map) * B)
        
        A = np.clip(A_new, 0, 1)
        B = np.clip(B_new, 0, 1)
        
    # Mapping B to colors
    # Background: deep emerald green #0a2016
    # Dominant: coral pink #ff7f50
    # Secondary: bone white #ffffe0
    # Accent: dark crimson #8b0000
    
    # Normalize B for coloring (usually B max is around 0.3 to 0.5 in these settings)
    val = np.clip(B * 3.5, 0, 1)
    
    R = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    G = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    B_col = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    
    # Very low B -> emerald
    # Mid B -> crimson
    # High B -> coral pink -> bone white
    
    m1 = val < 0.2
    R[m1] = 10
    G[m1] = 32 + val[m1] * 50
    B_col[m1] = 22
    
    m2 = (val >= 0.2) & (val < 0.5)
    t2 = (val[m2] - 0.2) / 0.3
    R[m2] = 10 + t2 * (139 - 10)
    G[m2] = 42 - t2 * 42
    B_col[m2] = 22 - t2 * 22
    
    m3 = (val >= 0.5) & (val < 0.8)
    t3 = (val[m3] - 0.5) / 0.3
    R[m3] = 139 + t3 * (255 - 139)
    G[m3] = 0 + t3 * (127 - 0)
    B_col[m3] = 0 + t3 * (80 - 0)
    
    m4 = val >= 0.8
    t4 = np.clip((val[m4] - 0.8) / 0.2, 0, 1)
    R[m4] = 255
    G[m4] = 127 + t4 * (255 - 127)
    B_col[m4] = 80 + t4 * (224 - 80)
    
    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B_col = np.clip(B_col, 0, 255).astype(np.uint8)
    
    # Upscale 2x to 4K
    R_4k = np.repeat(np.repeat(R, 2, axis=0), 2, axis=1)
    G_4k = np.repeat(np.repeat(G, 2, axis=0), 2, axis=1)
    B_4k = np.repeat(np.repeat(B_col, 2, axis=0), 2, axis=1)
    
    alpha = np.full((SIZE[1], SIZE[0], 1), 255, dtype=np.uint8)
    rgb = np.stack((R_4k, G_4k, B_4k), axis=-1)
    argb = np.concatenate((alpha, rgb), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
    py5.update_np_pixels()
    
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

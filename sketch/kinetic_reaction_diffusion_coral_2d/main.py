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

# Use a smaller grid for the physics simulation to ensure 60fps performance,
# then scale up to the canvas size when rendering.
GRID_W = SIZE[0] // 3
GRID_H = SIZE[1] // 3

# Gray-Scott parameters for Coral/Brain-like patterns
F_base = 0.0545
k_base = 0.0620
Da = 1.0
Db = 0.5

A = np.ones((GRID_H, GRID_W), dtype=np.float32)
B = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Create a spatial map for the feed/kill rates to create varying patterns across the screen
fx = np.linspace(-1, 1, GRID_W)
fy = np.linspace(-1, 1, GRID_H)
FX, FY = np.meshgrid(fx, fy)
RAD = np.hypot(FX, FY)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed the simulation in a few random spots
    for _ in range(10):
        cx = np.random.randint(10, GRID_W - 10)
        cy = np.random.randint(10, GRID_H - 10)
        B[cy-5:cy+5, cx-5:cx+5] = 1.0

def laplacian(Z):
    # Fast 3x3 Laplacian using NumPy slicing
    Ztop = Z[0:-2, 1:-1]
    Zleft = Z[1:-1, 0:-2]
    Zbottom = Z[2:, 1:-1]
    Zright = Z[1:-1, 2:]
    Zcenter = Z[1:-1, 1:-1]
    
    Ztl = Z[0:-2, 0:-2]
    Ztr = Z[0:-2, 2:]
    Zbl = Z[2:, 0:-2]
    Zbr = Z[2:, 2:]
    
    L = np.zeros_like(Z)
    L[1:-1, 1:-1] = (
        Ztop * 0.2 + Zleft * 0.2 + Zbottom * 0.2 + Zright * 0.2 +
        Ztl * 0.05 + Ztr * 0.05 + Zbl * 0.05 + Zbr * 0.05 - 
        Zcenter * 1.0
    )
    return L

def draw():
    global A, B
    
    t = py5.frame_count * 0.01
    
    # Animate the F parameter slightly over time to make the coral "breathe" and morph
    F_mod = F_base + 0.002 * np.sin(t)
    F = F_mod + 0.002 * RAD # Spatially varying feed rate
    k = k_base + 0.001 * np.cos(t * 0.5)
    
    # Run simulation steps
    for _ in range(8):
        lapA = laplacian(A)
        lapB = laplacian(B)
        
        ABB = A * B * B
        
        # We need to compute the updates only where L has valid data to avoid boundary artifacts
        # We can just update the whole array since L is zero at boundaries
        A += (Da * lapA - ABB + F * (1 - A))
        B += (Db * lapB + ABB - (k + F) * B)
        
    A = np.clip(A, 0, 1)
    B = np.clip(B, 0, 1)
    
    # Render array to colors
    # Map B concentration to a toxic glowing green/yellow palette on dark violet background
    img_data = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
    
    # Background: dark violet (A is 1, B is 0)
    # Coral: bright green/yellow (B > 0.2)
    
    b_val = np.clip(B * 3.0, 0, 1) # Boost contrast
    
    # R channel: low at 0, high at 1 (goes to yellow)
    img_data[..., 0] = (20 + 200 * b_val).astype(np.uint8)
    
    # G channel: very high for B > 0
    img_data[..., 1] = (10 + 240 * b_val).astype(np.uint8)
    
    # B channel: high at 0 (violet bg), low at 1
    img_data[..., 2] = (50 - 50 * b_val).astype(np.uint8)
    
    # Alpha
    img_data[..., 3] = 255
    
    img = py5.create_image_from_numpy(img_data, 'RGBA')
    
    # Draw scaled image to canvas
    py5.blend_mode(py5.BLEND)
    py5.background(0)
    
    # We use nearest neighbor or smooth depending on the aesthetic
    # For organic coral, smooth is good
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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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

# Solver Grid
GRID_W = SIZE[0] // 2
GRID_H = SIZE[1] // 2

# Tyson-Fife Oregonator variables
u = np.random.rand(GRID_H, GRID_W).astype(np.float32) * 0.2
v = np.random.rand(GRID_H, GRID_W).astype(np.float32) * 0.2

# Parameters
epsilon = 0.03
q = 0.002
f = 1.4
Du = 0.15
Dv = 0.08
dt = 0.005

# Inject some initial seed spots for spirals
for _ in range(12):
    cx = random.randint(GRID_W // 4, 3 * GRID_W // 4)
    cy = random.randint(GRID_H // 4, 3 * GRID_H // 4)
    r = random.randint(10, 25)
    # Create phase differences for spirals
    Y, X = np.meshgrid(np.arange(GRID_H), np.arange(GRID_W), indexing='ij')
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    mask = dist < r
    u[mask] = 0.8
    v[mask] = 0.4 + 0.3 * np.arctan2(Y[mask] - cy, X[mask] - cx)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def laplacian(grid):
    # Wrapping boundary Laplacian using np.roll
    left = np.roll(grid, 1, axis=1)
    right = np.roll(grid, -1, axis=1)
    up = np.roll(grid, 1, axis=0)
    down = np.roll(grid, -1, axis=0)
    return left + right + up + down - 4.0 * grid

def update_oregonator():
    global u, v
    # Sub-stepping for stability
    for _ in range(4):
        lap_u = laplacian(u)
        lap_v = laplacian(v)
        
        # Oregonator Tyson-Fife kinetics
        # u_dot = (1/eps) * (u * (1 - u) - f * v * (u - q) / (u + q))
        # Add small value to denominator to avoid division by zero
        kin_u = (u * (1.0 - u) - f * v * (u - q) / (u + q + 1e-6)) / epsilon
        kin_v = u - v
        
        u += dt * (Du * lap_u + kin_u)
        v += dt * (Dv * lap_v + kin_v)
        
        # Keep variables bounded
        u = np.clip(u, 0.0, 1.0)
        v = np.clip(v, 0.0, 1.0)

def draw():
    update_oregonator()
    
    # Render state u and v to screen
    # Dominant (60%): Bioluminescent Emerald (Green)
    # Secondary (30%): Neon Amethyst (Purple/Violet)
    # Accent (10%): Coral Pink
    
    # We will map u -> Emerald Green, v -> Amethyst, and high intensity reaction front -> Coral Pink
    # Reaction front can be measured by high u and low v, or rate of change
    front = np.clip(u - v, 0.0, 1.0)
    
    r = (front * 0.9 + v * 0.5 + (1.0 - u) * 0.05) * 255
    g = (u * 0.8 + (1.0 - v) * 0.1) * 255
    b = (v * 0.8 + front * 0.3) * 255
    
    img_data = np.zeros((GRID_H, GRID_W, 4), dtype=np.uint8)
    img_data[:, :, 0] = 255  # Alpha
    img_data[:, :, 1] = np.clip(r, 0, 255).astype(np.uint8)
    img_data[:, :, 2] = np.clip(g, 0, 255).astype(np.uint8)
    img_data[:, :, 3] = np.clip(b, 0, 255).astype(np.uint8)
    
    img = py5.create_image(GRID_W, GRID_H, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:] = img_data
    img.update_pixels()
    
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Resolution (Full HD might be slow, so we simulate at half resolution and scale up)
SIM_W = SIZE[0] // 2
SIM_H = SIZE[1] // 2

# Gray-Scott Parameters (Coral growth)
# dA, dB, feed, kill
DA = 1.0
DB = 0.5
FEED = 0.054
KILL = 0.062

A = np.ones((SIM_H, SIM_W), dtype=np.float32)
B = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Laplacian convolution weights
W_CENTER = -1.0
W_ADJ = 0.2
W_DIAG = 0.05

def laplacian(M):
    """ Fast Laplacian using NumPy slicing instead of scipy.ndimage for zero dependencies """
    L = np.zeros_like(M)
    # Center
    L += M * W_CENTER
    # Adjacent
    L[:-1, :] += M[1:, :] * W_ADJ
    L[1:, :] += M[:-1, :] * W_ADJ
    L[:, :-1] += M[:, 1:] * W_ADJ
    L[:, 1:] += M[:, :-1] * W_ADJ
    # Diagonal
    L[:-1, :-1] += M[1:, 1:] * W_DIAG
    L[1:, 1:] += M[:-1, :-1] * W_DIAG
    L[:-1, 1:] += M[1:, :-1] * W_DIAG
    L[1:, :-1] += M[:-1, 1:] * W_DIAG
    return L

def setup():
    global A, B
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Seed the reaction
    r = 20
    for _ in range(10):
        cx = np.random.randint(r, SIM_W - r)
        cy = np.random.randint(r, SIM_H - r)
        B[cy-r:cy+r, cx-r:cx+r] = 1.0
        
def draw():
    global A, B
    
    # Evolve the simulation 8 times per frame
    for _ in range(8):
        lapA = laplacian(A)
        lapB = laplacian(B)
        
        reaction = A * B * B
        
        # We vary the feed and kill rates slightly across the screen to create diverse patterns
        t = py5.frame_count * 0.001
        
        # Adding a slight drift / wind effect to the diffusion
        A += (DA * lapA - reaction + FEED * (1 - A))
        B += (DB * lapB + reaction - (FEED + KILL) * B)
        
    # Clamp values safely
    np.clip(A, 0, 1, out=A)
    np.clip(B, 0, 1, out=B)

    # Render directly to screen using load_np_pixels
    py5.load_np_pixels()
    
    # We need to map the SIM_H x SIM_W array to the full SIZE screen
    # Since we used half resolution, we repeat the pixels
    B_expanded = np.repeat(np.repeat(B, 2, axis=0), 2, axis=1)
    
    # Map B concentration to colors (Neon biological look)
    # Background: Dark Violet, Slime: Bright Cyan/Green
    
    color_bg = np.array([255, 10, 5, 20])   # ARGB (Dark Violet)
    color_fg = np.array([255, 0, 255, 150]) # ARGB (Neon Cyan/Green)
    
    # Calculate color mixing based on B concentration
    # We use a non-linear curve to make the edges sharp
    intensity = np.power(B_expanded, 0.5)
    
    # Broadcasting to (H, W, 4)
    pixel_colors = color_bg * (1 - intensity[..., np.newaxis]) + color_fg * intensity[..., np.newaxis]
    
    py5.np_pixels[:] = pixel_colors.astype(np.uint8)
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

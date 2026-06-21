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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global X, Y
    x = np.linspace(0, py5.width, py5.width)
    y = np.linspace(0, py5.height, py5.height)
    X, Y = np.meshgrid(x, y)

def draw():
    t = py5.frame_count * 0.05
    
    # Interference sources
    c1x = py5.width/2 + np.sin(t * 0.5) * 400
    c1y = py5.height/2 + np.cos(t * 0.3) * 300
    
    c2x = py5.width/2 + np.cos(t * 0.4) * 500
    c2y = py5.height/2 + np.sin(t * 0.6) * 200
    
    c3x = py5.width/2 + np.sin(t * 0.7) * 300
    c3y = py5.height/2 + np.cos(t * 0.2) * 600
    
    # Calculate distances
    d1 = np.sqrt((X - c1x)**2 + (Y - c1y)**2)
    d2 = np.sqrt((X - c2x)**2 + (Y - c2y)**2)
    d3 = np.sqrt((X - c3x)**2 + (Y - c3y)**2)
    
    # Wave lengths
    w1, w2, w3 = 80.0, 60.0, 100.0
    
    # Interference pattern
    v = np.sin(d1/w1 - t*2) + np.sin(d2/w2 - t*3) + np.sin(d3/w3 - t*1.5)
    
    # Normalize to 0-1
    v = (v + 3) / 6.0
    
    # Map to colors (Iridescent effect: narrow bands of varying hue)
    # Using HSB
    # Hue wrapped multiple times based on the interference value
    hue = (v * 1000 + t * 50) % 360
    
    # Saturation high
    sat = np.full_like(hue, 80)
    
    # Brightness bands
    brt = np.sin(v * np.pi * 10) * 50 + 50
    
    # Alpha
    alpha = np.full_like(hue, 100)
    
    # Convert HSB to RGB via py5 functions on numpy arrays? Py5 np_pixels expects ARGB or ABGR depending on byte order
    # It's faster to let py5 do HSB conversion via drawing points, or we convert manually.
    # We can do an HSB -> RGB manual conversion here
    C = (brt / 100) * (sat / 100)
    X_val = C * (1 - np.abs((hue / 60) % 2 - 1))
    m = (brt / 100) - C
    
    R = np.zeros_like(hue)
    G = np.zeros_like(hue)
    B = np.zeros_like(hue)
    
    # Hue sectors
    mask0 = (0 <= hue) & (hue < 60)
    mask1 = (60 <= hue) & (hue < 120)
    mask2 = (120 <= hue) & (hue < 180)
    mask3 = (180 <= hue) & (hue < 240)
    mask4 = (240 <= hue) & (hue < 300)
    mask5 = (300 <= hue) & (hue < 360)
    
    R[mask0], G[mask0], B[mask0] = C[mask0], X_val[mask0], 0
    R[mask1], G[mask1], B[mask1] = X_val[mask1], C[mask1], 0
    R[mask2], G[mask2], B[mask2] = 0, C[mask2], X_val[mask2]
    R[mask3], G[mask3], B[mask3] = 0, X_val[mask3], C[mask3]
    R[mask4], G[mask4], B[mask4] = X_val[mask4], 0, C[mask4]
    R[mask5], G[mask5], B[mask5] = C[mask5], 0, X_val[mask5]
    
    R = ((R + m) * 255).astype(np.uint8)
    G = ((G + m) * 255).astype(np.uint8)
    B = ((B + m) * 255).astype(np.uint8)
    A = np.full_like(R, 255)
    
    py5.load_np_pixels()
    
    # ARGB format for np_pixels
    py5.np_pixels[:, :, 0] = A
    py5.np_pixels[:, :, 1] = R
    py5.np_pixels[:, :, 2] = G
    py5.np_pixels[:, :, 3] = B
    
    py5.update_np_pixels()

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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

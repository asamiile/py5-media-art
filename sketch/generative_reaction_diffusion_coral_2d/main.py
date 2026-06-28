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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation Grid Size (lower resolution for performance, scaled up for rendering)
SIM_W = 960
SIM_H = 540

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global U, V, laplacian
    U = np.ones((SIM_H, SIM_W), dtype=np.float32)
    V = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    
    # Initial seeds
    for _ in range(50):
        cx = np.random.randint(100, SIM_W - 100)
        cy = np.random.randint(100, SIM_H - 100)
        V[cy-10:cy+10, cx-10:cx+10] = 1.0
        
    laplacian = np.array([[0.05, 0.2, 0.05],
                          [0.2, -1.0, 0.2],
                          [0.05, 0.2, 0.05]], dtype=np.float32)

def draw():
    global U, V
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Parameters for Gray-Scott (Coral-like pattern)
    # Smoothly morphing parameters to make the coral "breathe" and change shape
    f = np.interp(np.sin(t * py5.TWO_PI), [-1, 1], [0.0545, 0.0620])
    k = np.interp(np.cos(t * py5.TWO_PI * 0.5), [-1, 1], [0.0620, 0.0630])
    
    Du = 1.0
    Dv = 0.5
    
    # Run multiple simulation steps per frame to speed up the growth visually
    for _ in range(8):
        # Calculate Laplacian
        lapU = convolve(U, laplacian, mode='wrap')
        lapV = convolve(V, laplacian, mode='wrap')
        
        # Reaction terms
        uvv = U * V * V
        
        # Update equations
        u_new = U + (Du * lapU - uvv + f * (1.0 - U))
        v_new = V + (Dv * lapV + uvv - (f + k) * V)
        
        U = np.clip(u_new, 0, 1)
        V = np.clip(v_new, 0, 1)
        
    # Map V to colors
    # V goes from 0 to ~1
    # We want a glowing neon coral colormap
    
    # Create an ARGB array
    # Format: shape (SIM_H, SIM_W, 4) for A, R, G, B or directly as int32
    
    # Normalize V for coloring
    v_norm = V / V.max() if V.max() > 0 else V
    
    # Map to colors: Black -> Deep Blue -> Neon Pink -> Bright White
    r = np.interp(v_norm, [0, 0.3, 0.7, 1.0], [5, 20, 255, 255])
    g = np.interp(v_norm, [0, 0.3, 0.7, 1.0], [5, 10, 50, 255])
    b = np.interp(v_norm, [0, 0.3, 0.7, 1.0], [15, 150, 150, 255])
    
    # Alpha is always 255
    a = np.full_like(r, 255)
    
    # Stack into an image array (H, W, 4) RGBA
    img_data = np.stack((r, g, b, a), axis=-1).astype(np.uint8)
    
    # Create py5 image
    img = py5.create_image_from_numpy(img_data, "RGBA")
    
    # Draw scaled up
    py5.image(img, 0, 0, py5.width, py5.height)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

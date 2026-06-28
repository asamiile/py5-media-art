from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.ndimage import convolve

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

# Internal resolution for fast 2D Convolution
W_INT = SIZE[0] // 2
H_INT = SIZE[1] // 2

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global U, V, kernel, pixel_array
    
    # Initialize U=1, V=0
    U = np.ones((H_INT, W_INT), dtype=np.float32)
    V = np.zeros((H_INT, W_INT), dtype=np.float32)
    
    # Drop some random seed boxes of V=1 in the center area
    cx, cy = W_INT // 2, H_INT // 2
    for _ in range(50):
        rx = np.random.randint(cx - 100, cx + 100)
        ry = np.random.randint(cy - 100, cy + 100)
        U[ry-5:ry+5, rx-5:rx+5] = 0.5
        V[ry-5:ry+5, rx-5:rx+5] = 0.25
        
    # Introduce some noise to break symmetry
    U += np.random.uniform(-0.01, 0.01, (H_INT, W_INT))
    V += np.random.uniform(-0.01, 0.01, (H_INT, W_INT))
    
    # 3x3 Laplacian Kernel for 2D diffusion
    kernel = np.array([
        [0.05, 0.2, 0.05],
        [0.2, -1.0, 0.2],
        [0.05, 0.2, 0.05]
    ], dtype=np.float32)
    
    # Pre-allocate RGBA buffer
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255

def draw():
    global U, V, pixel_array
    
    # Gray-Scott Parameters (Coral growth / Mitosis-like)
    Du = 1.0     # Diffusion rate of U
    Dv = 0.5     # Diffusion rate of V
    feed = 0.055 # Feed rate
    kill = 0.062 # Kill rate
    dt = 1.0     # Time step
    
    # To animate the parameters, we can subtly shift the feed/kill rates across the grid
    # This creates different patterns (spots vs stripes) in different areas
    
    STEPS = 25
    for _ in range(STEPS):
        # Calculate Laplacian using scipy's fast C convolution
        lap_U = convolve(U, kernel, mode='wrap')
        lap_V = convolve(V, kernel, mode='wrap')
        
        # Calculate interaction
        reaction = U * V**2
        
        # Update U and V
        dU = Du * lap_U - reaction + feed * (1.0 - U)
        dV = Dv * lap_V + reaction - (feed + kill) * V
        
        U += dU * dt
        V += dV * dt
        
    # Prevent numerical instability
    U = np.clip(U, 0, 1)
    V = np.clip(V, 0, 1)

    # Render mapping: Map the difference (U - V) to a beautiful alien color palette
    val = U - V
    val_norm = np.clip((val + 1.0) / 2.0, 0, 1) # Range 0 to 1
    
    # Color mapping: deep purple/black to glowing cyan/white
    r = (0.5 + 0.5 * np.cos(py5.PI * 2 * (val_norm * 1.5 + 0.5))) * 255
    g = (0.5 + 0.5 * np.cos(py5.PI * 2 * (val_norm * 1.5 + 0.8))) * 255
    b = (0.5 + 0.5 * np.cos(py5.PI * 2 * (val_norm * 1.5 + 0.9))) * 255
    
    pixel_array[:, :, 0] = r.astype(np.uint8)
    pixel_array[:, :, 1] = g.astype(np.uint8)
    pixel_array[:, :, 2] = b.astype(np.uint8)
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Scale up to 4K using nearest neighbor (because we called py5.no_smooth() early)
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

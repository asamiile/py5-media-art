from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.signal import convolve2d

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

# For reaction-diffusion, 4K is too slow for CPU. We simulate at lower resolution and scale up.
SIM_SIZE = (OUTPUT_SIZE[0] // 4, OUTPUT_SIZE[1] // 4)
SIZE = OUTPUT_SIZE

# Gray-Scott parameters
DA = 1.0
DB = 0.5
feed = 0.055
k = 0.062

kernel = np.array([[0.05, 0.2, 0.05],
                   [0.2, -1.0, 0.2],
                   [0.05, 0.2, 0.05]])

A = np.ones((SIM_SIZE[1], SIM_SIZE[0]), dtype=np.float32)
B = np.zeros((SIM_SIZE[1], SIM_SIZE[0]), dtype=np.float32)

# Seed initial spots
for _ in range(20):
    rx = random.randint(10, SIM_SIZE[0]-10)
    ry = random.randint(10, SIM_SIZE[1]-10)
    B[ry-5:ry+5, rx-5:rx+5] = 1.0

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def update_rd():
    global A, B
    for _ in range(10): # 10 simulation steps per frame for speed
        lapA = convolve2d(A, kernel, mode='same', boundary='wrap')
        lapB = convolve2d(B, kernel, mode='same', boundary='wrap')
        
        ABB = A * B * B
        
        # dynamic feed and k based on spatial location (creates varied patterns)
        # we'll keep it simple for now, but slightly vary feed over time
        f = feed + py5.sin(py5.frame_count * 0.01) * 0.002
        
        newA = A + (DA * lapA - ABB + f * (1 - A))
        newB = B + (DB * lapB + ABB - (k + f) * B)
        
        A = np.clip(newA, 0, 1)
        B = np.clip(newB, 0, 1)

def draw():
    update_rd()
    
    # Map B concentration to color
    # B ranges roughly 0 to 0.4
    normalized_B = np.clip(B * 2.5, 0, 1)
    
    py5.load_pixels()
    
    # We need to map the SIM_SIZE array to the py5 SIZE screen.
    # To do this efficiently, we create an image from the numpy array.
    
    diff = normalized_B - A
    
    # We will draw this as an image
    # HSB to RGB mapping for numpy is non-trivial, so we create an ARGB integer array
    # Hue: 180 to 280 (blue to purple)
    # Saturation: 80 to 100
    # Brightness: dependent on B
    
    hue = 180 + normalized_B * 100
    sat = 80 + normalized_B * 20
    bri = normalized_B * 255
    
    # Convert HSB to RGB (approximate fast path)
    # Just mapping to a color palette in RGB directly
    R = (np.sin(normalized_B * np.pi) * 255).astype(np.uint32)
    G = (normalized_B * 255).astype(np.uint32)
    B_col = (np.cos(normalized_B * np.pi * 0.5) * 255).astype(np.uint32)
    
    # Pack into ARGB
    A_col = np.full_like(R, 255)
    pixels_2d = (A_col << 24) | (R << 16) | (G << 8) | B_col
    
    img = py5.create_image(SIM_SIZE[0], SIM_SIZE[1], py5.ARGB)
    img.load_np_pixels()
    # img.np_pixels has shape (H, W, 4) in RGBA, wait, load_np_pixels gives shape (H, W, 4)
    # Actually create_image + load_np_pixels is easier:
    img.np_pixels[:, :, 0] = A_col.astype(np.uint8) # A
    img.np_pixels[:, :, 1] = R.astype(np.uint8)     # R
    img.np_pixels[:, :, 2] = G.astype(np.uint8)     # G
    img.np_pixels[:, :, 3] = B_col.astype(np.uint8) # B
    img.update_np_pixels()
    
    # Draw scaled image
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

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
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# BZ Reaction simulation parameters
# We use a 3-state continuous cellular automaton
GRID_SCALE = 3
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

a = np.random.rand(ROWS, COLS).astype(np.float32)
b = np.random.rand(ROWS, COLS).astype(np.float32)
c = np.random.rand(ROWS, COLS).astype(np.float32)

# Convolution kernel for 8-way Moore neighborhood sum
kernel = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1]
], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global a, b, c
    
    # We step the simulation multiple times per frame to speed it up
    for _ in range(2):
        # BZ Reaction rules:
        # new_a = a + a * (alpha * b - gamma * c)
        # However, a simpler discrete model produces spiral waves:
        # A cell's state increases based on neighbors in the next state.
        
        c_a = convolve2d(a, kernel, mode='same', boundary='wrap') / 8.0
        c_b = convolve2d(b, kernel, mode='same', boundary='wrap') / 8.0
        c_c = convolve2d(c, kernel, mode='same', boundary='wrap') / 8.0
        
        # Hyperparameters for spiral wave formation
        alpha = 1.0
        beta = 1.0
        gamma = 1.0
        
        new_a = a + a * (alpha * b - gamma * c)
        new_b = b + b * (beta * c - alpha * a)
        new_c = c + c * (gamma * a - beta * b)
        
        a = np.clip(new_a, 0, 1)
        b = np.clip(new_b, 0, 1)
        c = np.clip(new_c, 0, 1)
        
        # Apply slight diffusion
        a = a * 0.9 + c_a * 0.1
        b = b * 0.9 + c_b * 0.1
        c = c * 0.9 + c_c * 0.1
    
    # Render
    py5.background(0)
    
    # We can map the states a, b, c to RGB or HSV.
    # Let's map a to hue, b to saturation, c to brightness.
    # Or simply:
    # Hue: based on dominant state
    # Brightness: magnitude
    
    # For speed, we will draw rects or use load_pixels.
    # load_pixels is much faster at 4K.
    py5.load_np_pixels()
    
    # Calculate colors
    # We use RGB colors to directly set the pixels
    
    r = (a * 255).astype(np.uint8)
    g = (b * 255).astype(np.uint8)
    bl = (c * 255).astype(np.uint8)
    
    # We want a neon palette: Deep violet, electric cyan, soft pink
    # A -> cyan (0, 255, 255)
    # B -> pink (255, 100, 200)
    # C -> violet (100, 0, 255)
    
    r_out = a * 0 + b * 255 + c * 100
    g_out = a * 255 + b * 100 + c * 0
    b_out = a * 255 + b * 200 + c * 255
    
    r_out = np.clip(r_out, 0, 255).astype(np.uint8)
    g_out = np.clip(g_out, 0, 255).astype(np.uint8)
    b_out = np.clip(b_out, 0, 255).astype(np.uint8)
    
    # We need to scale up the grid to the screen
    # Use numpy kron to upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # The arrays might not exactly match the screen size if SIZE is not divisible by GRID_SCALE
    # We just crop to the screen size
    r_scaled = r_scaled[:py5.height, :py5.width]
    g_scaled = g_scaled[:py5.height, :py5.width]
    b_scaled = b_scaled[:py5.height, :py5.width]
    
    # In py5, np_pixels is shape (height, width, 4) in ARGB format on Mac
    py5.np_pixels[:, :, 0] = 255 # Alpha
    py5.np_pixels[:, :, 1] = r_scaled # Red
    py5.np_pixels[:, :, 2] = g_scaled # Green
    py5.np_pixels[:, :, 3] = b_scaled # Blue
    
    py5.update_np_pixels()

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
        import os
        os._exit(0)

py5.run_sketch()

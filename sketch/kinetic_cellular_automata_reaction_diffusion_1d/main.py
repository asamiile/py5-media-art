from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
from scipy.ndimage import convolve1d

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

GRID_SCALE = 2
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# 1D Gray-Scott Reaction-Diffusion parameters
Da = 1.0
Db = 0.5
dt = 1.0
steps_per_frame = 30

# Initialize 1D arrays for chemicals A and B
A = np.ones(COLS, dtype=np.float32)
B = np.zeros(COLS, dtype=np.float32)

# Spatially varying parameters
x = np.linspace(0, 1, COLS, dtype=np.float32)
# f goes from 0.010 to 0.080
# k goes from 0.045 to 0.065
f = np.interp(x, [0, 1], [0.01, 0.06])
k = np.interp(x, [0, 1], [0.04, 0.07])

# Seed some B randomly
seed_indices = np.random.choice(COLS, 20, replace=False)
B[seed_indices] = 1.0

# 2D history buffer
history_B = np.zeros((ROWS, COLS), dtype=np.float32)

# Laplacian 1D kernel
kernel = np.array([1.0, -2.0, 1.0], dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A, B, history_B
    
    for _ in range(steps_per_frame):
        # Calculate Laplacian
        lapA = convolve1d(A, kernel, mode='wrap')
        lapB = convolve1d(B, kernel, mode='wrap')
        
        # Reaction terms
        reaction = A * B**2
        
        # Update A and B
        A_new = A + (Da * lapA - reaction + f * (1.0 - A)) * dt
        B_new = B + (Db * lapB + reaction - (k + f) * B) * dt
        
        A = np.clip(A_new, 0, 1)
        B = np.clip(B_new, 0, 1)
        
    # Scroll history up
    history_B[:-1] = history_B[1:]
    history_B[-1] = B
    
    # Render
    py5.load_np_pixels()
    
    # Palette: Molten Gold to Obsidian (Fire gradient)
    # v is B concentration (typically 0.0 to 0.5 max in Gray-Scott, we normalize by 0.5)
    v = np.clip(history_B * 2.0, 0, 1)
    
    # Black -> Red -> Orange -> Yellow -> White
    # R: 0 -> 255 -> 255 -> 255
    r_out = np.interp(v, [0, 0.33, 0.66, 1.0], [0, 255, 255, 255])
    # G: 0 -> 0 -> 128 -> 255
    g_out = np.interp(v, [0, 0.33, 0.66, 1.0], [0, 0, 160, 255])
    # B: 0 -> 0 -> 0 -> 255
    b_out = np.interp(v, [0, 0.33, 0.66, 1.0], [10, 0, 0, 255])
    
    r_out = np.clip(r_out, 0, 255).astype(np.uint8)
    g_out = np.clip(g_out, 0, 255).astype(np.uint8)
    b_out = np.clip(b_out, 0, 255).astype(np.uint8)
    
    # Upscale
    r_scaled = np.kron(r_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    g_scaled = np.kron(g_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    b_scaled = np.kron(b_out, np.ones((GRID_SCALE, GRID_SCALE), dtype=np.uint8))
    
    # Crop to screen
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

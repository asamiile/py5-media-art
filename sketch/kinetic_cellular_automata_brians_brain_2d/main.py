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

# Brian's Brain simulation parameters
GRID_SCALE = 4
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# States
OFF = 0
ON = 1
DYING = 2

# Initialize state with noise in the center
A = np.zeros((ROWS, COLS), dtype=np.uint8)
cx, cy = COLS // 2, ROWS // 2
s = 100

noise = np.random.rand(2*s, 2*s)
A[cy-s:cy+s, cx-s:cx+s] = np.where(noise > 0.8, ON, np.where(noise > 0.7, DYING, OFF))

kernel = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1]
], dtype=np.uint8)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global A
    
    # We step the simulation multiple times per frame
    for _ in range(2):
        # Count ON neighbors
        on_cells = (A == ON).astype(np.uint8)
        neighbors = convolve2d(on_cells, kernel, mode='same', boundary='wrap')
        
        # Next state
        A_next = np.zeros_like(A)
        
        # OFF turns ON if exactly 2 ON neighbors
        A_next[(A == OFF) & (neighbors == 2)] = ON
        
        # ON turns DYING
        A_next[A == ON] = DYING
        
        # DYING turns OFF (implicit, as A_next is initialized to OFF)
        
        A = A_next
        
    # Render
    py5.load_np_pixels()
    
    # Palette: Cyberpunk circuitry
    # OFF: Black (0)
    # ON: Bright Cyan
    # DYING: Deep Indigo
    
    r_out = np.zeros_like(A, dtype=np.uint8)
    g_out = np.zeros_like(A, dtype=np.uint8)
    b_out = np.zeros_like(A, dtype=np.uint8)
    
    r_out[A == ON] = 0
    g_out[A == ON] = 255
    b_out[A == ON] = 255
    
    r_out[A == DYING] = 20
    g_out[A == DYING] = 0
    b_out[A == DYING] = 100
    
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

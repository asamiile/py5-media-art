from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
from scipy.ndimage import convolve1d

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

# Parameters
ROWS = 1080  # We will compute at half-resolution and scale up to 4K to make it chunky and fast
COLS = 1920

# We keep a 2D array of the screen state
grid = np.zeros((ROWS, COLS), dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize the first row with some noise
    grid[0, :] = np.random.uniform(0, 1, COLS)

def draw():
    py5.background(0)
    
    # The kernel for continuous 1D CA
    # We drift the kernel weights slightly using time (frame_count)
    t = py5.frame_count * 0.01
    
    # Kernel weights: left, center, right
    w_l = 1.0 + 0.5 * np.sin(t * 1.3)
    w_c = 1.2 + 0.5 * np.cos(t * 0.8)
    w_r = 1.0 + 0.5 * np.sin(t * 1.7 + 2.0)
    
    kernel = np.array([w_l, w_c, w_r]) / (w_l + w_c + w_r) * 1.99
    
    # Shift rows down by 2 to simulate falling faster
    # To keep it continuous, we actually only compute the top row based on the 2nd row?
    # No, usually in 1D CA time is the Y axis. So we compute row N based on row N-1.
    # Since we want a waterfall, the whole screen shifts down, and the top row is generated from the old top row.
    
    speed = 3 # shift down by 3 pixels per frame
    
    # Shift grid down
    grid[speed:, :] = grid[:-speed, :]
    
    # Generate new top rows
    # row 0 is based on what row 0 was before we shifted.
    # Actually, we can just convolve the old row 0 `speed` times to generate the missing rows.
    old_top = grid[speed, :]
    for i in range(speed - 1, -1, -1):
        # convolve
        new_row = convolve1d(old_top, kernel, mode='wrap')
        # Apply a non-linear activation (fractal folding)
        new_row = new_row - np.floor(new_row)
        grid[i, :] = new_row
        old_top = new_row

    # Map grid (0.0 to 1.0) to RGB
    # We will use an advanced numpy color mapping to make it look like a glowing neon tapestry
    # We create an RGB image array
    image_array = np.zeros((ROWS, COLS, 4), dtype=np.uint8)
    
    # Hue mapping: value * 360
    # Let's do a simple gradient: 0->Dark Blue, 0.5->Magenta, 1.0->Cyan
    # We can do this with sine waves for RGB channels
    val = grid * np.pi * 2
    r = (0.5 + 0.5 * np.sin(val + 0.0)) * 255
    g = (0.5 + 0.5 * np.sin(val + 2.0)) * 255
    b = (0.5 + 0.5 * np.sin(val + 4.0)) * 255
    
    image_array[:, :, 0] = r.astype(np.uint8)
    image_array[:, :, 1] = g.astype(np.uint8)
    image_array[:, :, 2] = b.astype(np.uint8)
    image_array[:, :, 3] = 255 # Alpha
    
    # Create Py5 image
    img = py5.create_image_from_numpy(image_array, 'RGBA')
    
    # Draw it scaled up
    py5.image_mode(py5.CORNER)
    py5.image(img, 0, 0, SIZE[0], SIZE[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

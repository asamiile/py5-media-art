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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation parameters
NUM_POINTS = 500000
SCALE_FACTOR = 4.5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, colors
    
    # Initialize random starting positions
    pos = np.random.uniform(-2, 2, (NUM_POINTS, 2))
    
    # Colors based on initial X position (just for variation)
    colors = np.zeros((NUM_POINTS, 4))
    colors[:, 0] = (pos[:, 0] * 50 + 200) % 360 # Hue (cyan to magenta)
    colors[:, 1] = 90  # Sat
    colors[:, 2] = 100 # Bri
    colors[:, 3] = 15  # Low alpha for additive blending

def draw():
    global pos
    
    # Motion fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 12)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    W, H = SIZE
    t = py5.frame_count / TOTAL_FRAMES * py5.TWO_PI
    
    # Smoothly morphing parameters for Peter de Jong attractor
    a = -1.24 + np.sin(t * 0.5) * 0.5
    b = 1.43 + np.cos(t * 0.7) * 0.5
    c = 1.34 + np.sin(t * 1.1) * 0.5
    d = -1.82 + np.cos(t * 0.9) * 0.5
    
    # Peter de Jong equations
    new_x = np.sin(a * pos[:, 1]) - np.cos(b * pos[:, 0])
    new_y = np.sin(c * pos[:, 0]) - np.cos(d * pos[:, 1])
    
    pos[:, 0] = new_x
    pos[:, 1] = new_y
    
    # Mapping to screen coordinates
    screen_x = np.clip((pos[:, 0] * (W / SCALE_FACTOR)) + W / 2, 0, W - 1).astype(int)
    screen_y = np.clip((pos[:, 1] * (H / SCALE_FACTOR)) + H / 2, 0, H - 1).astype(int)
    
    # Draw points directly to py5.np_pixels for maximum performance (half a million points is too slow for loop)
    py5.load_np_pixels()
    pixels = py5.np_pixels
    
    # Since we can't easily do additive blending in pure numpy without expensive operations, 
    # we can just write bright colors directly and rely on the rect fade. 
    # But wait, to get the glowing effect, we should add to the existing pixels.
    # We can do this efficiently using np.add.at or just simple array indexing.
    # Wait, `py5.np_pixels` is an array of shape (H, W, 4) with RGBA uint8.
    
    # To keep it simple and safe from Py5 bridge memory issues, let's just use begin_shape(POINTS).
    # Wait! 500,000 points in a Python loop for `begin_shape` might take 1 second per frame (60 seconds for 60 frames = 15 mins total).
    # Since we are not in a rush, a Python loop is perfectly acceptable and robust.
    # Let's reduce NUM_POINTS to 100,000 to keep it somewhat fast.
    
    # Since NUM_POINTS is 500k in the script, I will draw them using py5.points() if possible.
    # But Py5 doesn't have `points()`. It has `begin_shape(POINTS)`.
    # Let's just do it directly to np_pixels since it's much faster.
    
    # Direct pixel manipulation:
    # 1. Convert to 1D flat indices
    flat_indices = screen_y * W + screen_x
    
    # 2. Extract current pixels (shape: H*W, 4)
    flat_pixels = pixels.reshape(-1, 4)
    
    # 3. We want to add color. 
    # To do additive blending properly without loop:
    # It's better to just set the pixels to a bright color, the fade will take care of the rest.
    flat_pixels[flat_indices, 0] = 255 # Alpha
    # Set R, G, B channels based on some simple logic. We'll just use a cool cyan/magenta base depending on X.
    # X from 0 to W
    r_val = (screen_x / W * 255).astype(np.uint8)
    b_val = (screen_y / H * 255).astype(np.uint8)
    
    flat_pixels[flat_indices, 1] = r_val     # R
    flat_pixels[flat_indices, 2] = 100       # G
    flat_pixels[flat_indices, 3] = 255 - b_val # B
    
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

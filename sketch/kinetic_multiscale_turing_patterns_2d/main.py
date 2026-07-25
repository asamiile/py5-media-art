from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import gaussian_filter

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

# Multi-Scale Turing Pattern Parameters
# We simulate at a lower resolution and upscale for speed,
# as Gaussian blur is expensive at 4K.
SCALE = 3
SIZE = OUTPUT_SIZE
W = SIZE[0] // SCALE
H = SIZE[1] // SCALE

STEPS_PER_FRAME = 1
DT = 0.05

# 5 scales of Turing Patterns
SCALES = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A, colormap
    
    # Initialize with white noise [-1, 1]
    A = np.random.uniform(-1.0, 1.0, (H, W)).astype(np.float32)
    
    # Pre-generate an elegant biological/mineral colormap
    # Dark Emerald -> Gold -> White
    colormap = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        v = i / 255.0
        colormap[i, 0] = 255 # Alpha
        
        if v < 0.3:
            p = v / 0.3
            colormap[i, 1:] = [int(p * 20), int(p * 50), int(p * 30)] # Deep Green
        elif v < 0.7:
            p = (v - 0.3) / 0.4
            colormap[i, 1:] = [20 + int(p * 200), 50 + int(p * 150), 30 + int(p * 50)] # Emerald to Gold
        else:
            p = (v - 0.7) / 0.3
            colormap[i, 1:] = [220 + int(p * 35), 200 + int(p * 55), 80 + int(p * 175)] # Gold to White

def step_physics(t):
    global A
    
    # Calculate activations and inhibitions for each scale
    # Using scipy.ndimage.gaussian_filter with mode='wrap' for seamless tiling
    variations = []
    diffs = []
    
    for r in SCALES:
        # Modulate the radii slightly over time to make the patterns breathe
        r_mod = r * (1.0 + 0.2 * np.sin(t * 0.5 + r))
        
        act = gaussian_filter(A, sigma=r_mod, mode='wrap')
        inh = gaussian_filter(A, sigma=r_mod * 1.5, mode='wrap')
        
        diff = act - inh
        var = np.abs(diff)
        
        diffs.append(diff)
        variations.append(var)
        
    variations = np.array(variations) # Shape (num_scales, H, W)
    diffs = np.array(diffs)
    
    # Find the index of the minimum variation for each pixel
    min_var_idx = np.argmin(variations, axis=0)
    
    # Get the corresponding diff
    # Advanced indexing to pull out the correct diff for each pixel
    best_diff = np.take_along_axis(diffs, min_var_idx[np.newaxis, :, :], axis=0)[0]
    
    # Update State
    A += np.sign(best_diff) * DT
    
    # Normalize state back to [-1, 1]
    # To prevent it from clamping immediately to hard edges, we use a softer normalization
    A = np.clip(A, -1.0, 1.0)
    
    # Add a continuous rolling drift to make the pattern flow like a fluid
    drift_x = int(np.sin(t) * 2.0)
    drift_y = int(np.cos(t * 0.7) * 2.0)
    A = np.roll(A, drift_x, axis=1)
    A = np.roll(A, drift_y, axis=0)

def draw():
    global A
    
    t = py5.frame_count * 0.05
    for _ in range(STEPS_PER_FRAME):
        step_physics(t)
        
    py5.load_np_pixels()
    
    # Map State A [-1, 1] to colormap indices [0, 255]
    # We apply a slight sigmoid to soften the edges
    soft_A = 1.0 / (1.0 + np.exp(-4.0 * A))
    indices = (soft_A * 255).astype(np.uint8)
    
    colors = colormap[indices] # Shape (H, W, 4)
    
    # Upscale
    upscaled = np.repeat(np.repeat(colors, SCALE, axis=0), SCALE, axis=1)
    
    # Write to py5 pixels
    py5.np_pixels[:] = upscaled
    
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

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

# Reaction-Diffusion Simulation parameters
# We use a 2-state continuous cellular automaton
GRID_SCALE = 3
COLS = SIZE[0] // GRID_SCALE
ROWS = SIZE[1] // GRID_SCALE

# U is initially 1 everywhere, V is 0
u = np.ones((ROWS, COLS), dtype=np.float32)
v = np.zeros((ROWS, COLS), dtype=np.float32)

# Seed V in the center
cx, cy = COLS // 2, ROWS // 2
radius = 20
y, x = np.ogrid[-cy:ROWS-cy, -cx:COLS-cx]
mask = x**2 + y**2 <= radius**2
v[mask] = 1.0

# Also scatter a few random seeds to make it asymmetric
for _ in range(50):
    rx, ry = random.randint(0, COLS-1), random.randint(0, ROWS-1)
    v[ry-2:ry+3, rx-2:rx+3] = 1.0

# Laplacian kernel for diffusion
kernel = np.array([
    [0.05, 0.2, 0.05],
    [0.2, -1.0, 0.2],
    [0.05, 0.2, 0.05]
], dtype=np.float32)

# Gray-Scott parameters
DA = 1.0
DB = 0.5
feed0 = 0.055
k0 = 0.062

feed1 = 0.036
k1 = 0.053 # Mitosis / coral

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global u, v
    
    # Animate parameters
    t = py5.frame_count / TOTAL_FRAMES
    # Oscillate smoothly between feed0/k0 and feed1/k1
    s = (np.sin(t * np.pi * 2) + 1.0) / 2.0
    feed = feed0 * (1 - s) + feed1 * s
    k = k0 * (1 - s) + k1 * s
    
    # We step the simulation multiple times per frame to speed it up
    for _ in range(8):
        lap_u = convolve2d(u, kernel, mode='same', boundary='wrap')
        lap_v = convolve2d(v, kernel, mode='same', boundary='wrap')
        
        uvv = u * v * v
        
        new_u = u + (DA * lap_u - uvv + feed * (1 - u))
        new_v = v + (DB * lap_v + uvv - (feed + k) * v)
        
        u = np.clip(new_u, 0, 1)
        v = np.clip(new_v, 0, 1)
    
    # For speed, we will use load_pixels.
    py5.load_np_pixels()
    
    # Color palette: Hot pink, vivid orange, deep oceanic blue
    # We map V to colors
    # V is usually between 0 and 0.5
    v_norm = np.clip(v * 2.5, 0, 1)
    
    # Background: deep oceanic blue (10, 20, 50)
    # Mid: vivid orange (255, 100, 0)
    # High: hot pink (255, 0, 128)
    
    r_out = v_norm * 255 + (1 - v_norm) * 10
    g_out = v_norm * (1-v_norm)*4 * 255 + (1 - v_norm) * 20
    b_out = v_norm * 128 + (1 - v_norm) * 50
    
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

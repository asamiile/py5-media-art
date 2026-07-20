from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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

def setup():
    global state, new_state, scale, cols, rows
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    scale = 8
    cols = SIZE[0] // scale
    rows = SIZE[1] // scale
    
    # Continuous state [0, 1]
    state = np.random.rand(rows, cols) * 0.5
    new_state = np.zeros((rows, cols))

def draw():
    global state, new_state
    
    py5.background(0)
    
    # 8-neighbor sum using np.roll
    s = (
        np.roll(state, 1, axis=0) +
        np.roll(state, -1, axis=0) +
        np.roll(state, 1, axis=1) +
        np.roll(state, -1, axis=1) +
        np.roll(np.roll(state, 1, axis=0), 1, axis=1) +
        np.roll(np.roll(state, -1, axis=0), 1, axis=1) +
        np.roll(np.roll(state, 1, axis=0), -1, axis=1) +
        np.roll(np.roll(state, -1, axis=0), -1, axis=1)
    )
    
    avg = s / 8.0
    
    # Growth rule based on average neighbor value
    # Magic numbers for a nice continuous CA
    growth = np.exp(-((avg - 0.28) ** 2) / 0.015) * 2 - 1
    
    new_state = state + growth * 0.2
    new_state = np.clip(new_state, 0, 1)
    
    # Decay slightly
    new_state -= 0.005
    new_state = np.clip(new_state, 0, 1)
    
    # Inject noise/growth seeds
    if py5.frame_count % 15 == 0:
        cy = np.random.randint(0, rows)
        cx = np.random.randint(0, cols)
        radius = 15
        y, x = np.ogrid[-cy:rows-cy, -cx:cols-cx]
        mask = x*x + y*y <= radius*radius
        new_state[mask] = 1.0

    # Calculate difference for blood red effect
    diff = state - new_state # positive means it decayed
    
    state = new_state.copy()
    
    py5.load_np_pixels()
    
    # ARGB format: A=0, R=1, G=2, B=3
    # Decay turns red. Normal is grayscale.
    
    base_val = (state * 255).astype(np.uint8)
    decay_val = np.clip(diff * 10 * 255, 0, 255).astype(np.uint8)
    
    r_channel = np.clip(base_val + decay_val, 0, 255).astype(np.uint8)
    g_channel = base_val
    b_channel = base_val
    
    r_scaled = np.repeat(np.repeat(r_channel, scale, axis=0), scale, axis=1)
    g_scaled = np.repeat(np.repeat(g_channel, scale, axis=0), scale, axis=1)
    b_scaled = np.repeat(np.repeat(b_channel, scale, axis=0), scale, axis=1)
    
    # Trim to exact size in case of rounding
    r_scaled = r_scaled[:SIZE[1], :SIZE[0]]
    g_scaled = g_scaled[:SIZE[1], :SIZE[0]]
    b_scaled = b_scaled[:SIZE[1], :SIZE[0]]
    
    py5.np_pixels[:, :, 1] = r_scaled
    py5.np_pixels[:, :, 2] = g_scaled
    py5.np_pixels[:, :, 3] = b_scaled
    py5.np_pixels[:, :, 0] = 255 # Alpha
    
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import numpy as np
import py5

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # (3840, 2160)

# Grid setup (upscaled for performance)
GRID_SCALE = 6
cols = SIZE[0] // GRID_SCALE  # 640
rows = SIZE[1] // GRID_SCALE  # 360

paper = None
ink = None
wetness = None

# Palettes (desaturated HSL converted to RGB values)
c_bg = np.array([248.0, 244.0, 236.0], dtype=np.float32)      # Warm linen paper background
c_dom = np.array([28.0, 45.0, 66.0], dtype=np.float32)        # Prussian Blue (60% weight)
c_sec = np.array([42.0, 101.0, 112.0], dtype=np.float32)       # Indigo Teal (30% weight)
c_acc = np.array([184.0, 74.0, 92.0], dtype=np.float32)        # Warm Coral Crimson (10% weight)

# Path dynamics
t_offset = random.uniform(0, 1000)


def setup():
    global paper, ink, wetness
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize paper texture using py5 noise (run once)
    paper = np.zeros((rows, cols), dtype=np.float32)
    ns = random.uniform(0, 1000)
    for r in range(rows):
        for c in range(cols):
            fine = py5.noise(c * 0.11 + ns, r * 0.11 + ns)
            fiber = py5.noise(c * 0.025 + ns + 40, r * 0.04 + ns)
            paper[r, c] = 0.78 + fine * 0.12 + fiber * 0.18
    paper = np.clip(paper, 0.72, 1.08)
    
    # Ink: 3 channels (dominant, secondary, accent)
    ink = np.zeros((rows, cols, 3), dtype=np.float32)
    wetness = np.zeros((rows, cols), dtype=np.float32)
    
    # Initial wet paths and ink pools
    for i in range(3):
        x = int(cols * (0.3 + i * 0.2))
        y = int(rows * 0.5)
        add_drop(x, y, radius=random.randint(18, 28), channel=i)


def add_drop(cx: int, cy: int, radius: int, channel: int):
    global ink, wetness
    y_min, y_max = max(0, cy - radius * 2), min(rows, cy + radius * 2 + 1)
    x_min, x_max = max(0, cx - radius * 2), min(cols, cx + radius * 2 + 1)
    
    Y, X = np.ogrid[y_min:y_max, x_min:x_max]
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    
    mask = dist <= radius * 2
    if not np.any(mask):
        return
        
    amount = np.maximum(0.0, 1.0 - dist / (radius * 2))
    local_paper = paper[y_min:y_max, x_min:x_max]
    grain = 0.65 + local_paper * 0.45
    
    ink[y_min:y_max, x_min:x_max, channel] += amount * grain * mask * 0.095
    wetness[y_min:y_max, x_min:x_max] = np.minimum(1.0, wetness[y_min:y_max, x_min:x_max] + amount * 0.9 * mask)


def draw():
    global ink, wetness
    
    t = py5.frame_count * 0.8 + t_offset
    
    # Update agents (painting paths) and emit wetness + ink drops
    # Agent 0 (Dominant Prussian Blue) Lissajous path
    a0_x = int(cols / 2 + math.sin(t * 0.015) * cols * 0.38)
    a0_y = int(rows / 2 + math.cos(t * 0.009) * rows * 0.38)
    
    # Agent 1 (Secondary Indigo Teal) slow oval
    a1_x = int(cols / 2 + math.cos(t * 0.012) * cols * 0.32)
    a1_y = int(rows / 2 + math.sin(t * 0.019) * rows * 0.28)
    
    # Agent 2 (Accent Coral Crimson) noise wander
    a2_x = int(cols / 2 + (py5.noise(t * 0.007, 100) - 0.5) * cols * 0.8)
    a2_y = int(rows / 2 + (py5.noise(t * 0.007, 200) - 0.5) * rows * 0.8)
    
    # Continuously brush dynamic wetness along the paths
    for ax, ay in [(a0_x, a0_y), (a1_x, a1_y), (a2_x, a2_y)]:
        if 0 <= ax < cols and 0 <= ay < rows:
            # Add a small splash of wetness
            r_brush = 10
            y_min, y_max = max(0, ay - r_brush), min(rows, ay + r_brush + 1)
            x_min, x_max = max(0, ax - r_brush), min(cols, ax + r_brush + 1)
            Y, X = np.ogrid[y_min:y_max, x_min:x_max]
            dist = np.sqrt((X - ax)**2 + (Y - ay)**2)
            brush_mask = dist <= r_brush
            wetness[y_min:y_max, x_min:x_max] = np.minimum(1.0, wetness[y_min:y_max, x_min:x_max] + 0.18 * brush_mask)
            
    # Inject ink drops periodically
    if py5.frame_count % 35 == 0:
        add_drop(a0_x, a0_y, radius=random.randint(9, 15), channel=0)
    if py5.frame_count % 47 == 0:
        add_drop(a1_x, a1_y, radius=random.randint(7, 12), channel=1)
    if py5.frame_count % 73 == 0:
        add_drop(a2_x, a2_y, radius=random.randint(5, 10), channel=2)

    # Perform physical step diffusion
    for _ in range(3):
        # Ink diffusion
        diffusion = 0.14 + (paper - 0.72) * 0.2
        neighbors = (
            np.roll(ink, 1, axis=0) +
            np.roll(ink, -1, axis=0) +
            np.roll(ink, 1, axis=1) +
            np.roll(ink, -1, axis=1)
        ) * 0.25
        delta = (neighbors - ink) * diffusion[:, :, None] * wetness[:, :, None]
        ink = np.clip(ink + delta, 0, 4.0)
        
        # Wetness diffusion
        wetness_neighbors = (
            np.roll(wetness, 1, axis=0) +
            np.roll(wetness, -1, axis=0) +
            np.roll(wetness, 1, axis=1) +
            np.roll(wetness, -1, axis=1)
        ) * 0.25
        wetness_delta = (wetness_neighbors - wetness) * 0.14
        wetness = np.clip(wetness + wetness_delta, 0.0, 1.0)
        wetness *= 0.984  # drying rate

    # Compute wet edge (Laplacian of wetness)
    up = np.roll(wetness, 1, axis=0)
    down = np.roll(wetness, -1, axis=0)
    left = np.roll(wetness, 1, axis=1)
    right = np.roll(wetness, -1, axis=1)
    laplacian = np.abs(wetness * 4 - up - down - left - right)
    edge = np.clip(laplacian * 3.2, 0, 1.0)

    # Color mapping
    bg = c_bg[None, None, :] * paper[:, :, None]
    
    total_density = np.sum(ink, axis=2)
    # Blend coefficient
    blend_density = np.minimum(1.0, total_density * 0.85)
    
    epsilon = 1e-6
    w_dom = ink[:, :, 0] / (total_density + epsilon)
    w_sec = ink[:, :, 1] / (total_density + epsilon)
    w_acc = ink[:, :, 2] / (total_density + epsilon)
    
    pigment_color = (
        c_dom[None, None, :] * w_dom[:, :, None] +
        c_sec[None, None, :] * w_sec[:, :, None] +
        c_acc[None, None, :] * w_acc[:, :, None]
    )
    
    rgb = bg * (1.0 - blend_density[:, :, None]) + pigment_color * blend_density[:, :, None] * 0.96
    
    # Apply wet edge darkening (caustic edge effect)
    rgb = rgb * (1.0 - edge[:, :, None] * 0.45)
    
    rgb_uint8 = np.clip(rgb, 0, 255).astype(np.uint8)
    
    # High-quality bilinear upscaling to 4K resolution
    try:
        import cv2
        rgb_upscaled = cv2.resize(rgb_uint8, SIZE, interpolation=cv2.INTER_LINEAR)
    except ImportError:
        from PIL import Image
        img = Image.fromarray(rgb_uint8, 'RGB')
        img_upscaled = img.resize(SIZE, Image.BILINEAR)
        rgb_upscaled = np.array(img_upscaled)

    # Write to py5 frame buffer
    py5.load_np_pixels()
    # In py5 on macOS, the np_pixels channel layout is ARGB
    py5.np_pixels[:, :, 0] = 255  # Alpha
    py5.np_pixels[:, :, 1] = rgb_upscaled[:, :, 0]  # Red
    py5.np_pixels[:, :, 2] = rgb_upscaled[:, :, 1]  # Green
    py5.np_pixels[:, :, 3] = rgb_upscaled[:, :, 2]  # Blue
    py5.update_np_pixels()

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress logging
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Complete render
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot at the midpoint
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

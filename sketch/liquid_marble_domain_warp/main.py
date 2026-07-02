from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5
import cv2

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
W, H = SIZE

def generate_noise_map(w, h, scale):
    """Generate a simple low-frequency noise map using sine waves for displacement."""
    x = np.linspace(0, scale * np.pi * 2, w)
    y = np.linspace(0, scale * np.pi * 2, h)
    X, Y = np.meshgrid(x, y)
    
    # Complex interference pattern
    N1 = np.sin(X + np.cos(Y))
    N2 = np.cos(Y - np.sin(X))
    N3 = np.sin(X * 0.5 - Y * 1.5)
    
    noise = (N1 + N2 + N3) / 3.0
    return noise.astype(np.float32)

# Generate base maps
map_u = generate_noise_map(W, H, 3.0)
map_v = generate_noise_map(W, H, 2.5)

# Generate base color texture
tex_x = np.linspace(-1, 1, W)
tex_y = np.linspace(-1, 1, H)
TX, TY = np.meshgrid(tex_x, tex_y)
base_texture = np.zeros((H, W, 3), dtype=np.float32)

# Palette: Ocean depths and liquid gold
# Deep ocean: #001F3F (0, 31, 63)
# Cyan: #39CCCC (57, 204, 204)
# Gold: #FFDC00 (255, 220, 0)
dist = np.sqrt(TX**2 + TY**2)
angle = np.arctan2(TY, TX)

# Map colors to texture
# Base is ocean
base_texture[:, :, 0] = 63  # B
base_texture[:, :, 1] = 31  # G
base_texture[:, :, 2] = 0   # R (OpenCV uses BGR initially, we'll convert to RGB for py5)

# Add cyan bands
cyan_mask = np.sin(dist * 20 + angle * 4) > 0.5
base_texture[cyan_mask, 0] = 204
base_texture[cyan_mask, 1] = 204
base_texture[cyan_mask, 2] = 57

# Add gold bands
gold_mask = np.cos(dist * 15 - angle * 3) > 0.8
base_texture[gold_mask, 0] = 0
base_texture[gold_mask, 1] = 220
base_texture[gold_mask, 2] = 255

# Swap BGR to RGB since py5 expects ARGB
rgb_texture = base_texture[:, :, ::-1]

# Base identity maps for remap
grid_x, grid_y = np.meshgrid(np.arange(W), np.arange(H))
map_x_base = grid_x.astype(np.float32)
map_y_base = grid_y.astype(np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    t = py5.frame_count * 0.05
    
    # Animate displacement map over time
    # We mix the static noise maps with time-varying offsets
    disp_x = map_u * np.cos(t * 0.2) + map_v * np.sin(t * 0.3)
    disp_y = map_u * np.sin(t * 0.25) - map_v * np.cos(t * 0.35)
    
    # Amplify displacement
    strength = 150.0 + 50.0 * np.sin(t * 0.1)
    
    # Final remap coordinates
    map_x = (map_x_base + disp_x * strength).astype(np.float32)
    map_y = (map_y_base + disp_y * strength).astype(np.float32)
    
    # Apply domain warp
    warped = cv2.remap(rgb_texture, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    # Add second layer of warp for fractal "fBM" effect
    disp_x2 = cv2.remap(map_u, map_x, map_y, cv2.INTER_LINEAR)
    disp_y2 = cv2.remap(map_v, map_x, map_y, cv2.INTER_LINEAR)
    
    map_x2 = (map_x_base + disp_x2 * strength * 0.5).astype(np.float32)
    map_y2 = (map_y_base + disp_y2 * strength * 0.5).astype(np.float32)
    
    final_warped = cv2.remap(warped, map_x2, map_y2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    # Convert to ARGB for py5
    alpha = np.full((H, W, 1), 255, dtype=np.uint8)
    argb = np.concatenate((alpha, final_warped.astype(np.uint8)), axis=-1)
    
    py5.load_np_pixels()
    py5.np_pixels[:] = argb
    py5.update_np_pixels()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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

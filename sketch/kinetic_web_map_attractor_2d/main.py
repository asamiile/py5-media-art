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

# Simulation state
N = 1000000
# Initial points inside the web region
x = np.random.uniform(-10, 10, N).astype(np.float32)
y = np.random.uniform(-10, 10, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_web(alpha, K):
    global x, y
    u = x * np.cos(alpha) + y * np.sin(alpha)
    v = -x * np.sin(alpha) + y * np.cos(alpha)
    x_new = u
    y_new = v - K * np.sin(u)
    # Wrap to a large torus to prevent particles from diffusing out of view
    x[:] = np.mod(x_new + 20.0, 40.0) - 20.0
    y[:] = np.mod(y_new + 20.0, 40.0) - 20.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Modulate parameters continuously
    # The Zaslavsky Web Map parameter K controls chaotic layer thickness.
    # We use q=4 symmetry (alpha = 2*pi/4 = pi/2) and slowly breathe K.
    alpha = np.pi / 2.0
    K = 0.5 + 0.2 * np.sin(t)
    
    # Run steps
    for _ in range(4):
        step_web(alpha, K)
        
    # Apply a gentle rotation to the points before mapping to screen
    rot = np.sin(t * 0.5) * 0.1
    x_rot = x * np.cos(rot) - y * np.sin(rot)
    y_rot = x * np.sin(rot) + y * np.cos(rot)
    
    # Map to screen (Web map bounds depends on how far we want to see, [-10, 10] is a good web section)
    screen_x = (x_rot + 10.0) / 20.0 * SIZE[0]
    screen_y = (y_rot + 10.0) / 20.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Neon Magenta, Cyan, and Deep Velvet
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    # Deep Velvet base
    r_col = 30 * (density_norm ** 1.5)
    g_col = 0 * (density_norm ** 1.2)
    b_col = 60 * (density_norm ** 1.0)
    
    # Neon Magenta & Cyan midtones
    neon_mask = (density_norm > 0.3) & (density_norm < 0.7)
    r_col[neon_mask] = np.maximum(r_col[neon_mask], 60 + 195 * ((density_norm[neon_mask] - 0.3) / 0.4))
    g_col[neon_mask] = np.maximum(g_col[neon_mask], 0 + 50 * ((density_norm[neon_mask] - 0.3) / 0.4))
    b_col[neon_mask] = np.maximum(b_col[neon_mask], 100 + 155 * ((density_norm[neon_mask] - 0.3) / 0.4))
    
    # Cyan highlights
    cyan_mask = density_norm > 0.7
    r_col[cyan_mask] = np.maximum(r_col[cyan_mask], 255 - 150 * ((density_norm[cyan_mask] - 0.7) / 0.3))
    g_col[cyan_mask] = np.maximum(g_col[cyan_mask], 50 + 205 * ((density_norm[cyan_mask] - 0.7) / 0.3))
    b_col[cyan_mask] = 255
    
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_col.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g_col.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b_col.astype(np.uint8)
    
    py5.update_np_pixels()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.", flush=True)
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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

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
# Initial points spread around the origin
x = np.random.uniform(-2, 2, N).astype(np.float32)
y = np.random.uniform(-2, 2, N).astype(np.float32)
z = np.random.uniform(-2, 2, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_aizawa(a, b, c, d, e, f_val, dt=0.01):
    global x, y, z
    # Euler integration step for the Aizawa attractor
    dx = (z - b) * x - d * y
    dy = d * x + (z - b) * y
    dz = c + a * z - (z**3) / 3.0 - (x**2 + y**2) * (1.0 + e * z) + f_val * z * (x**3)
    
    x += dx * dt
    y += dy * dt
    z += dz * dt

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Aizawa attractor parameters with continuous modulation
    a = 0.95 + 0.1 * np.sin(t)
    b = 0.7
    c = 0.6
    d = 3.5 + 0.5 * np.cos(t * 1.5)
    e = 0.25
    f_val = 0.1
    
    # Run integration steps
    for _ in range(2):
        step_aizawa(a, b, c, d, e, f_val, dt=0.01)
        
    # Rotate 3D attractor gently over time
    theta = t * 0.5
    phi = np.sin(t) * 0.5
    
    # Rotate around Z
    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    z_rot1 = z
    
    # Rotate around X
    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z_rot1 * np.sin(phi)
    z_rot2 = y_rot1 * np.sin(phi) + z_rot1 * np.cos(phi)
    
    # Map to screen
    # Aizawa attractor typical size is roughly [-2.5, 2.5]
    screen_x = (x_rot2 + 3.0) / 6.0 * SIZE[0]
    screen_y = (y_rot2 + 3.0) / 6.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Ruby Red, Champagne Gold, and Deep Obsidian
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    # Deep Obsidian base
    r_col = 30 * (density_norm ** 1.5)
    g_col = 10 * (density_norm ** 1.2)
    b_col = 30 * (density_norm ** 1.0)
    
    # Ruby Red midtones
    ruby_mask = (density_norm > 0.3) & (density_norm < 0.7)
    r_col[ruby_mask] = np.maximum(r_col[ruby_mask], 30 + 195 * ((density_norm[ruby_mask] - 0.3) / 0.4))
    g_col[ruby_mask] = np.maximum(g_col[ruby_mask], 10 + 10 * ((density_norm[ruby_mask] - 0.3) / 0.4))
    b_col[ruby_mask] = np.maximum(b_col[ruby_mask], 30 + 30 * ((density_norm[ruby_mask] - 0.3) / 0.4))
    
    # Champagne Gold highlights
    gold_mask = density_norm > 0.7
    r_col[gold_mask] = np.maximum(r_col[gold_mask], 225 + 30 * ((density_norm[gold_mask] - 0.7) / 0.3))
    g_col[gold_mask] = np.maximum(g_col[gold_mask], 20 + 215 * ((density_norm[gold_mask] - 0.7) / 0.3))
    b_col[gold_mask] = np.maximum(b_col[gold_mask], 60 + 115 * ((density_norm[gold_mask] - 0.7) / 0.3))
    
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

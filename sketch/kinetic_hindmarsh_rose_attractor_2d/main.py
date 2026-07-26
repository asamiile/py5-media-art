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
x = np.random.uniform(-0.1, 0.1, N).astype(np.float32)
y = np.random.uniform(-0.1, 0.1, N).astype(np.float32)
z = np.random.uniform(-0.1, 0.1, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_hindmarsh_rose(I_val, dt=0.01):
    global x, y, z
    a = 1.0
    b = 3.0
    c = 1.0
    d = 5.0
    r = 0.006
    s = 4.0
    x_R = -1.6
    
    # Euler integration step for the Hindmarsh-Rose model
    dx = y - a * (x ** 3) + b * (x ** 2) - z + I_val
    dy = c - d * (x ** 2) - y
    dz = r * (s * (x - x_R) - z)
    
    x_new = x + dx * dt
    y_new = y + dy * dt
    z_new = z + dz * dt
    
    # Keep particles bounded
    mask = (np.abs(x_new) > 20) | (np.abs(y_new) > 20) | (np.abs(z_new) > 20) | np.isnan(x_new)
    x_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    y_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    z_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    
    x[:] = x_new
    y[:] = y_new
    z[:] = z_new

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Parameter with continuous modulation
    I_val = 3.0 + 0.5 * np.sin(t)
    
    # Run integration steps
    for _ in range(5):
        step_hindmarsh_rose(I_val, dt=0.01)
        
    # Rotate 3D attractor gently over time
    theta = t * 0.4
    phi = np.sin(t * 1.5) * 0.4
    
    # Rotate around Z
    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    z_rot1 = z
    
    # Rotate around X
    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z_rot1 * np.sin(phi)
    z_rot2 = y_rot1 * np.sin(phi) + z_rot1 * np.cos(phi)
    
    # Map to screen
    # Hindmarsh-Rose typical size: x in [-3,3], y in [-15,5], z in [0,5]
    # We will center and scale uniformly assuming range roughly [-10, 10]
    screen_x = (x_rot2 + 10.0) / 20.0 * SIZE[0]
    screen_y = (y_rot2 + 10.0) / 20.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Crimson, Electric Blue, and Silver
    density_norm = np.clip(density_buffer / 12.0, 0, 1)
    
    # Crimson base
    r_col = 75 * (density_norm ** 1.5)
    g_col = 5 * (density_norm ** 1.5)
    b_col = 25 * (density_norm ** 1.5)
    
    # Electric Blue midtones
    blue_mask = (density_norm > 0.3) & (density_norm < 0.7)
    r_col[blue_mask] = np.maximum(r_col[blue_mask], 75 - 75 * ((density_norm[blue_mask] - 0.3) / 0.4))
    g_col[blue_mask] = np.maximum(g_col[blue_mask], 5 + 185 * ((density_norm[blue_mask] - 0.3) / 0.4))
    b_col[blue_mask] = np.maximum(b_col[blue_mask], 25 + 230 * ((density_norm[blue_mask] - 0.3) / 0.4))
    
    # Silver highlights
    silver_mask = density_norm > 0.7
    r_col[silver_mask] = np.maximum(r_col[silver_mask], 0 + 230 * ((density_norm[silver_mask] - 0.7) / 0.3))
    g_col[silver_mask] = np.maximum(g_col[silver_mask], 190 + 50 * ((density_norm[silver_mask] - 0.7) / 0.3))
    b_col[silver_mask] = np.maximum(b_col[silver_mask], 255 - 15 * ((density_norm[silver_mask] - 0.7) / 0.3))
    
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

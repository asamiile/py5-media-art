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
w = np.random.uniform(-0.1, 0.1, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_hyperchaotic_lu(d, dt=0.002):
    global x, y, z, w
    
    a = 36.0
    b = 3.0
    c = 20.0
    
    # Euler integration step for the Hyperchaotic Lu Attractor
    dx = a * (y - x) + w
    dy = -x * z + c * y
    dz = x * y - b * z
    dw = x * z + d * w
    
    x_new = x + dx * dt
    y_new = y + dy * dt
    z_new = z + dz * dt
    w_new = w + dw * dt
    
    # Keep particles bounded
    mask = (np.abs(x_new) > 100) | (np.abs(y_new) > 100) | (np.abs(z_new) > 100) | (np.abs(w_new) > 100) | np.isnan(x_new)
    x_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    y_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    z_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    w_new[mask] = np.random.uniform(-0.1, 0.1, np.sum(mask)).astype(np.float32)
    
    x[:] = x_new
    y[:] = y_new
    z[:] = z_new
    w[:] = w_new

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Parameter with continuous modulation
    d = 1.3 + 0.3 * np.sin(t)
    
    # Run integration steps
    for _ in range(4):
        step_hyperchaotic_lu(d, dt=0.002)
        
    # Rotate 3D attractor gently over time
    theta = t * 0.4
    phi = np.sin(t * 1.5) * 0.4
    
    # Rotate around Z
    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    z_rot1 = (z - 30.0)
    
    # Rotate around X
    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z_rot1 * np.sin(phi)
    z_rot2 = y_rot1 * np.sin(phi) + z_rot1 * np.cos(phi)
    
    # Add a bit of W to Z just for fun depth
    z_rot2 += w * 0.2
    
    # Map to screen
    # Hyperchaotic Lu typical size: x,y in [-40, 40], z in [0, 60]
    screen_x = (x_rot2 + 40.0) / 80.0 * SIZE[0]
    screen_y = (y_rot2 + 40.0) / 80.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Violet, Gold, and Deep Blue
    density_norm = np.clip(density_buffer / 12.0, 0, 1)
    
    # Deep Blue base
    r_col = 15 * (density_norm ** 1.5)
    g_col = 10 * (density_norm ** 1.5)
    b_col = 50 * (density_norm ** 1.5)
    
    # Violet midtones
    violet_mask = (density_norm > 0.3) & (density_norm < 0.7)
    r_col[violet_mask] = np.maximum(r_col[violet_mask], 15 + 135 * ((density_norm[violet_mask] - 0.3) / 0.4))
    g_col[violet_mask] = np.maximum(g_col[violet_mask], 10 + 40 * ((density_norm[violet_mask] - 0.3) / 0.4))
    b_col[violet_mask] = np.maximum(b_col[violet_mask], 50 + 175 * ((density_norm[violet_mask] - 0.3) / 0.4))
    
    # Gold highlights
    gold_mask = density_norm > 0.7
    r_col[gold_mask] = np.maximum(r_col[gold_mask], 150 + 105 * ((density_norm[gold_mask] - 0.7) / 0.3))
    g_col[gold_mask] = np.maximum(g_col[gold_mask], 50 + 160 * ((density_norm[gold_mask] - 0.7) / 0.3))
    b_col[gold_mask] = np.maximum(b_col[gold_mask], 225 - 175 * ((density_norm[gold_mask] - 0.7) / 0.3))
    
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

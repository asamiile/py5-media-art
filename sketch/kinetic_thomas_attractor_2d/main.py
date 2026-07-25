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
# Initial points spread across the attractor space
x = np.random.uniform(-4, 4, N).astype(np.float32)
y = np.random.uniform(-4, 4, N).astype(np.float32)
z = np.random.uniform(-4, 4, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_thomas(b, dt=0.05):
    global x, y, z
    # Euler integration step for Thomas' cyclically symmetric attractor
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    
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
    
    # Modulate dissipation parameter
    # Lower b means a more complex, dense knot. Higher b simplifies the orbits.
    b = 0.18 + 0.02 * np.sin(t)
    
    # Run integration steps
    for _ in range(5):
        step_thomas(b, dt=0.05)
        
    # Rotate 3D attractor gently over time
    theta = t * 0.7
    phi = np.sin(t * 1.3) * 0.5
    
    # Rotate around Z
    x_rot1 = x * np.cos(theta) - y * np.sin(theta)
    y_rot1 = x * np.sin(theta) + y * np.cos(theta)
    z_rot1 = z
    
    # Rotate around X
    x_rot2 = x_rot1
    y_rot2 = y_rot1 * np.cos(phi) - z_rot1 * np.sin(phi)
    z_rot2 = y_rot1 * np.sin(phi) + z_rot1 * np.cos(phi)
    
    # Map to screen
    # Thomas attractor typical size is well bounded in roughly [-4, 4] for x,y,z
    screen_x = (x_rot2 + 5.0) / 10.0 * SIZE[0]
    screen_y = (y_rot2 + 5.0) / 10.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Neon Emerald, Azure, and Star White
    density_norm = np.clip(density_buffer / 15.0, 0, 1)
    
    # Azure base
    r_col = 0 * (density_norm ** 1.5)
    g_col = 80 * (density_norm ** 1.2)
    b_col = 180 * (density_norm ** 1.0)
    
    # Neon Emerald midtones
    emerald_mask = (density_norm > 0.3) & (density_norm < 0.8)
    r_col[emerald_mask] = np.maximum(r_col[emerald_mask], 0 + 30 * ((density_norm[emerald_mask] - 0.3) / 0.5))
    g_col[emerald_mask] = np.maximum(g_col[emerald_mask], 80 + 175 * ((density_norm[emerald_mask] - 0.3) / 0.5))
    b_col[emerald_mask] = np.maximum(b_col[emerald_mask], 180 - 100 * ((density_norm[emerald_mask] - 0.3) / 0.5))
    
    # Star White highlights
    white_mask = density_norm > 0.8
    r_col[white_mask] = np.maximum(r_col[white_mask], 30 + 225 * ((density_norm[white_mask] - 0.8) / 0.2))
    g_col[white_mask] = np.maximum(g_col[white_mask], 255)
    b_col[white_mask] = np.maximum(b_col[white_mask], 80 + 175 * ((density_norm[white_mask] - 0.8) / 0.2))
    
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

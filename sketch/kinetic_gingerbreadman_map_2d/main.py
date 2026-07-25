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
# Initial points (the Gingerbreadman map is typically constrained around [-10, 10])
x = np.random.uniform(-10, 10, N).astype(np.float32)
y = np.random.uniform(-10, 10, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_gingerbreadman(s):
    global x, y
    x_new = 1.0 - y + np.abs(x) * s
    y_new = x.copy()
    x[:] = x_new
    y[:] = y_new

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    global density_buffer
    
    t = py5.frame_count * 2 * np.pi / TOTAL_FRAMES
    
    # Modulate parameters continuously
    # A standard Gingerbreadman map has s=1.0. We breathe it gently to warp the crystals.
    s = 1.0 + 0.05 * np.sin(t)
    
    # Run steps
    for _ in range(5):
        step_gingerbreadman(s)
        
    # Apply a gentle rotation to the points before mapping to screen
    rot = np.sin(t) * 0.2
    x_rot = x * np.cos(rot) - y * np.sin(rot)
    y_rot = x * np.sin(rot) + y * np.cos(rot)
    
    # Map to screen (Gingerbreadman bounds typically roughly [-20, 20])
    screen_x = (x_rot + 20.0) / 40.0 * SIZE[0]
    screen_y = (y_rot + 20.0) / 40.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Ice Blue, Sapphire, and Frost White
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    # Ice Blue base
    b = 255 * (density_norm ** 0.8)
    g = 150 * (density_norm ** 1.2) + 50 * density_norm
    r = 50 * density_norm
    
    # Sapphire midtones
    sapphire_mask = (density_norm > 0.3) & (density_norm < 0.7)
    b[sapphire_mask] = 255
    g[sapphire_mask] = np.maximum(g[sapphire_mask], 100 * ((density_norm[sapphire_mask] - 0.3) / 0.4))
    r[sapphire_mask] = np.maximum(r[sapphire_mask], 50 * ((density_norm[sapphire_mask] - 0.3) / 0.4))
    
    # Frost White highlights
    white_mask = density_norm > 0.7
    r[white_mask] = np.maximum(r[white_mask], 200 + 55 * ((density_norm[white_mask] - 0.7) / 0.3))
    g[white_mask] = np.maximum(g[white_mask], 200 + 55 * ((density_norm[white_mask] - 0.7) / 0.3))
    b[white_mask] = 255
    
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b.astype(np.uint8)
    
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

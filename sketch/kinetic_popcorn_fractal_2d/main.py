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
# Initial points
x = np.random.uniform(-5, 5, N).astype(np.float32)
y = np.random.uniform(-5, 5, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_popcorn(h, c):
    global x, y
    x_new = x - h * np.sin(y + np.tan(c * y))
    y_new = y - h * np.sin(x + np.tan(c * x))
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
    # Standard Popcorn fractal has c=3.0. We breathe it gently to warp the structures.
    h = 0.05
    c = 3.0 + 0.5 * np.sin(t)
    
    # Run steps (particles drift slowly, so we run multiple steps)
    for _ in range(3):
        step_popcorn(h, c)
        
    # Apply a gentle rotation to the points before mapping to screen
    rot = np.sin(t * 0.5) * 0.1
    x_rot = x * np.cos(rot) - y * np.sin(rot)
    y_rot = x * np.sin(rot) + y * np.cos(rot)
    
    # Map to screen (Popcorn bounds are roughly the initialization [-5, 5])
    screen_x = (x_rot + 5.0) / 10.0 * SIZE[0]
    screen_y = (y_rot + 5.0) / 10.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Amethyst Purple, Rose Gold, and Pearl White
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    # Amethyst Purple base
    r = 120 * (density_norm ** 1.5)
    g = 30 * (density_norm ** 2.0)
    b_col = 200 * (density_norm ** 0.8)
    
    # Rose Gold midtones
    gold_mask = (density_norm > 0.4) & (density_norm < 0.8)
    r[gold_mask] = np.maximum(r[gold_mask], 200 + 55 * ((density_norm[gold_mask] - 0.4) / 0.4))
    g[gold_mask] = np.maximum(g[gold_mask], 100 + 80 * ((density_norm[gold_mask] - 0.4) / 0.4))
    b_col[gold_mask] = np.maximum(0, b_col[gold_mask] - 50 * ((density_norm[gold_mask] - 0.4) / 0.4))
    
    # Pearl White highlights
    pearl_mask = density_norm > 0.8
    r[pearl_mask] = 255
    g[pearl_mask] = np.maximum(g[pearl_mask], 230 + 25 * ((density_norm[pearl_mask] - 0.8) / 0.2))
    b_col[pearl_mask] = np.maximum(b_col[pearl_mask], 200 + 55 * ((density_norm[pearl_mask] - 0.8) / 0.2))
    
    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r.astype(np.uint8)
    py5.np_pixels[:, :, 2] = g.astype(np.uint8)
    py5.np_pixels[:, :, 3] = b_col.astype(np.uint8)
    
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

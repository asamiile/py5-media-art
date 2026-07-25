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
x = np.random.uniform(-3, 3, N).astype(np.float32)
y = np.random.uniform(-3, 3, N).astype(np.float32)

density_buffer = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)

def step_svensson(a, b, c, d):
    global x, y
    x_new = d * np.sin(a * x) - np.sin(b * y)
    y_new = c * np.cos(a * x) + np.cos(b * y)
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
    # A beautiful set of parameters to oscillate around:
    # a = 1.4, b = 1.56, c = 1.4, d = -6.56
    a = 1.4 + 0.05 * np.sin(t)
    b = 1.56 + 0.05 * np.cos(t * 1.5)
    c = 1.4 + 0.05 * np.sin(t * 2)
    d = -6.56 + 0.2 * np.cos(t)
    
    # Run steps
    for _ in range(5):
        step_svensson(a, b, c, d)
        
    # Map to screen (Svensson bounds are roughly [-abs(d)-1, abs(d)+1] -> [-8, 8])
    screen_x = (x + 8.0) / 16.0 * SIZE[0]
    screen_y = (y + 8.0) / 16.0 * SIZE[1]
    
    # Fast 2D histogram
    H, _, _ = np.histogram2d(screen_y, screen_x, bins=(SIZE[1], SIZE[0]), range=[[0, SIZE[1]], [0, SIZE[0]]])
    
    # Accumulate with decay (motion blur)
    density_buffer = density_buffer * 0.85 + H
    
    # Render
    py5.load_np_pixels()
    
    # Map density to colors
    # Palette: Luminous Pearl White, Violet, and Rose Gold
    density_norm = np.clip(density_buffer / 10.0, 0, 1)
    
    # Rose Gold base
    r = 255 * (density_norm ** 0.8)
    g = 150 * (density_norm ** 1.2) + 50 * density_norm
    b = 100 * (density_norm ** 1.5) + 50 * density_norm
    
    # Violet midtones
    violet_mask = (density_norm > 0.3) & (density_norm < 0.7)
    b[violet_mask] = np.maximum(b[violet_mask], 200 * ((density_norm[violet_mask] - 0.3) / 0.4))
    
    # Pearl White highlights
    pearl_mask = density_norm > 0.7
    g[pearl_mask] = np.maximum(g[pearl_mask], 200 + 55 * ((density_norm[pearl_mask] - 0.7) / 0.3))
    b[pearl_mask] = np.maximum(b[pearl_mask], 200 + 55 * ((density_norm[pearl_mask] - 0.7) / 0.3))
    
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

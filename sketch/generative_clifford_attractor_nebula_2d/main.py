from pathlib import Path
import shutil
import subprocess
import sys
import math
import numpy as np
import py5

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

# Number of walkers to iterate per frame
NUM_WALKERS = 2000000
# State of walkers
x = None
y = None
density_map = None

def setup():
    global x, y, density_map
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize walkers
    x = np.random.uniform(-2, 2, NUM_WALKERS)
    y = np.random.uniform(-2, 2, NUM_WALKERS)
    
    density_map = np.zeros((py5.height, py5.width), dtype=np.float32)

def generate_points(a, b, c, d):
    global x, y
    
    # We will step the walkers multiple times to gather points
    # Actually, a single step of 2M walkers is 2M points, which is a lot.
    # We will do 3 steps per frame to get 6M points.
    points_x = []
    points_y = []
    
    for _ in range(3):
        x_new = np.sin(a * y) + c * np.cos(a * x)
        y_new = np.sin(b * x) + d * np.cos(b * y)
        x = x_new
        y = y_new
        
        points_x.append(x)
        points_y.append(y)
        
    return np.concatenate(points_x), np.concatenate(points_y)

def draw():
    global x, y, density_map
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Decay the old density for a fading trail effect
    density_map *= 0.85
    
    # Smoothly vary parameters
    # The parameters typically range from -2 to 2 or -3 to 3
    a = 1.5 + 1.2 * py5.os_noise(t * 1.5, 0)
    b = -1.5 + 1.2 * py5.os_noise(t * 1.5, 10)
    c = 1.0 + 1.5 * py5.os_noise(t * 1.5, 20)
    d = 0.5 + 1.5 * py5.os_noise(t * 1.5, 30)
    
    px, py = generate_points(a, b, c, d)
    
    # Map points from approx [-3, 3] to screen coordinates
    # We will use a scale factor
    scale = min(py5.width, py5.height) / 6.5
    screen_x = (px * scale + py5.width / 2).astype(np.int32)
    screen_y = (py * scale + py5.height / 2).astype(np.int32)
    
    # Filter points within screen bounds
    valid = (screen_x >= 0) & (screen_x < py5.width) & (screen_y >= 0) & (screen_y < py5.height)
    screen_x = screen_x[valid]
    screen_y = screen_y[valid]
    
    # Fast 2D histogram using bincount
    coords = screen_x + screen_y * py5.width
    counts = np.bincount(coords, minlength=py5.width * py5.height)
    counts_2d = counts.reshape((py5.height, py5.width))
    
    # Add to density map
    density_map += counts_2d
    
    # Color mapping
    # Apply a non-linear scaling (logarithmic or square root) to make low densities visible
    norm_density = np.sqrt(density_map)
    max_d = np.max(norm_density)
    if max_d > 0:
        norm_density /= max_d
    else:
        max_d = 1.0
        
    # Magma-like colormap
    # 0 -> Black (0, 0, 0)
    # 0.3 -> Purple (80, 0, 120)
    # 0.6 -> Magenta/Red (200, 50, 100)
    # 0.8 -> Orange (255, 150, 0)
    # 1.0 -> Yellow/White (255, 255, 200)
    
    r = np.zeros_like(norm_density)
    g = np.zeros_like(norm_density)
    b_chan = np.zeros_like(norm_density)
    
    # Thresholds
    t1, t2, t3, t4 = 0.3, 0.6, 0.8, 1.0
    
    # Interpolation masks
    m1 = (norm_density <= t1)
    m2 = (norm_density > t1) & (norm_density <= t2)
    m3 = (norm_density > t2) & (norm_density <= t3)
    m4 = (norm_density > t3)
    
    # M1: 0 to t1 (Black to Purple)
    f1 = norm_density[m1] / t1
    r[m1] = 80 * f1
    g[m1] = 0
    b_chan[m1] = 120 * f1
    
    # M2: t1 to t2 (Purple to Magenta/Red)
    f2 = (norm_density[m2] - t1) / (t2 - t1)
    r[m2] = 80 + (200 - 80) * f2
    g[m2] = 50 * f2
    b_chan[m2] = 120 + (100 - 120) * f2
    
    # M3: t2 to t3 (Magenta/Red to Orange)
    f3 = (norm_density[m3] - t2) / (t3 - t2)
    r[m3] = 200 + (255 - 200) * f3
    g[m3] = 50 + (150 - 50) * f3
    b_chan[m3] = 100 + (0 - 100) * f3
    
    # M4: t3 to t4 (Orange to Yellow/White)
    f4 = (norm_density[m4] - t3) / (t4 - t3)
    r[m4] = 255
    g[m4] = 150 + (255 - 150) * f4
    b_chan[m4] = 200 * f4
    
    pixels = np.zeros((py5.height, py5.width, 4), dtype=np.uint8)
    pixels[..., 0] = b_chan.astype(np.uint8) # BGRA format for py5
    pixels[..., 1] = g.astype(np.uint8)
    pixels[..., 2] = r.astype(np.uint8)
    pixels[..., 3] = 255 # Alpha
    
    py5.set_np_pixels(pixels)
    
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

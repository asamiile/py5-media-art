from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from scipy.signal import convolve2d
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

# BZ Reaction / Hodgepodge machine parameters
W, H = SIZE[0] // 4, SIZE[1] // 4 # Low res grid for performance
STATES = 120
K1 = 2
K2 = 3
G_PARAM = 17

grid = np.random.randint(0, STATES, (W, H))

# Moore neighborhood kernel
kernel = np.array([
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 1]
])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    global grid
    
    # BZ Cellular Automata step
    # Count specific cell states
    ill = (grid == STATES - 1).astype(int)
    infected = ((grid > 0) & (grid < STATES - 1)).astype(int)
    
    sum_ill = convolve2d(ill, kernel, mode='same', boundary='wrap')
    sum_infected = convolve2d(infected, kernel, mode='same', boundary='wrap')
    sum_grid = convolve2d(grid, kernel, mode='same', boundary='wrap')
    
    # Calculate next state
    next_grid = np.copy(grid)
    
    # Healthy cells (state 0)
    mask_0 = grid == 0
    next_grid[mask_0] = np.floor(sum_infected[mask_0] / K1) + np.floor(sum_ill[mask_0] / K2)
    
    # Infected cells (0 < state < STATES-1)
    mask_inf = (grid > 0) & (grid < STATES - 1)
    s_inf = sum_grid[mask_inf]
    # To avoid divide by zero, count total active neighbors
    num_active = sum_infected[mask_inf] + sum_ill[mask_inf]
    num_active[num_active == 0] = 1 # Prevent Div0
    
    next_grid[mask_inf] = np.floor(s_inf / num_active) + G_PARAM
    
    # Ill cells (state STATES-1)
    mask_ill = grid == STATES - 1
    next_grid[mask_ill] = 0
    
    # Clamp
    grid = np.clip(next_grid, 0, STATES - 1)
    
    # Rendering
    # Map grid values to colors
    # We create a full screen image and load it
    
    py5.load_pixels()
    
    # Map to hue
    hue = (grid / (STATES - 1.0)) * 360.0
    sat = np.where(grid > 0, 80, 0)
    val = np.where(grid > 0, 90, 0)
    
    # In py5, we can't easily set numpy arrays back to HSB directly, we need ARGB integers
    # Let's draw it using py5.image after converting to ARGB in python, 
    # Or simply draw rectangles for scaling, which is fast enough for WxH
    
    py5.background(0)
    
    # To draw fast, let's use points or small rects, but py5 can do shape or points
    # Actually py5.image from numpy is fastest
    
    # Convert HSB to RGB manually
    # H: 0-360, S: 0-1, V: 0-1
    h = hue / 60.0
    i = np.floor(h)
    f = h - i
    p = val * (1.0 - sat/100.0)
    q = val * (1.0 - sat/100.0 * f)
    t = val * (1.0 - sat/100.0 * (1.0 - f))
    
    i = (i % 6).astype(int)
    
    r = np.zeros_like(hue)
    g = np.zeros_like(hue)
    b = np.zeros_like(hue)
    
    # Apply formulas based on i
    r[i==0] = val[i==0]; g[i==0] = t[i==0]; b[i==0] = p[i==0]
    r[i==1] = q[i==1]; g[i==1] = val[i==1]; b[i==1] = p[i==1]
    r[i==2] = p[i==2]; g[i==2] = val[i==2]; b[i==2] = t[i==2]
    r[i==3] = p[i==3]; g[i==3] = q[i==3]; b[i==3] = val[i==3]
    r[i==4] = t[i==4]; g[i==4] = p[i==4]; b[i==4] = val[i==4]
    r[i==5] = val[i==5]; g[i==5] = p[i==5]; b[i==5] = q[i==5]
    
    # Map to 0-255
    R = (r * 2.55).astype(np.uint32)
    G = (g * 2.55).astype(np.uint32)
    B = (b * 2.55).astype(np.uint32)
    A = np.full_like(R, 255)
    
    # ARGB
    pixels_argb = (A << 24) | (R << 16) | (G << 8) | B
    
    img = py5.create_image(W, H, py5.ARGB)
    img.load_pixels()
    img.pixels = pixels_argb.flatten()
    img.update_pixels()
    
    # Draw scaled
    py5.image(img, 0, 0, py5.width, py5.height)

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

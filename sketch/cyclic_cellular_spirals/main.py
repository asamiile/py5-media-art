from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import math
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10  # 10 seconds of animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties (480x270 matches 16:9 ratio, fast simulation, crisp scale-up)
GRID_W = 480
GRID_H = 270
N_STATES = 16

cells = np.zeros((GRID_H, GRID_W), dtype=np.int32)
colormap = np.zeros((N_STATES, 3), dtype=np.uint8)
vignette = np.ones((GRID_H, GRID_W, 1), dtype=np.float32)

# py5 Image reference for rendering the grid
pg_image = None

def hsb_to_rgb(h: float, s: float, b: float) -> tuple[int, int, int]:
    h = h / 360.0
    s = s / 100.0
    b = b / 100.0
    if s == 0.0:
        return int(b * 255), int(b * 255), int(b * 255)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = b * (1.0 - s)
    q = b * (1.0 - s * f)
    t = b * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        r, g, b_val = b, t, p
    elif i == 1:
        r, g, b_val = q, b, p
    elif i == 2:
        r, g, b_val = p, b, t
    elif i == 3:
        r, g, b_val = p, q, b
    elif i == 4:
        r, g, b_val = t, p, b
    else:
        r, g, b_val = b, p, q
    return int(r * 255), int(g * 255), int(b_val * 255)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global cells, colormap, vignette, pg_image
    
    # Initialize cyclic HSB colormap
    # Indigo -> Teal -> Gold -> Magenta
    stops = [
        (225, 80, 22),   # Deep Indigo/Navy
        (185, 90, 95),   # Bright Teal
        (45, 85, 98),    # Soft Gold
        (315, 90, 85),   # Radiant Magenta
    ]
    
    n_stops = len(stops)
    steps_per_stop = N_STATES // n_stops
    for i in range(N_STATES):
        stop_idx = i // steps_per_stop
        next_stop_idx = (stop_idx + 1) % n_stops
        t_val = (i % steps_per_stop) / float(steps_per_stop)
        
        h1, s1, b1 = stops[stop_idx]
        h2, s2, b2 = stops[next_stop_idx]
        
        # Shortest path hue interpolation
        dh = h2 - h1
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        h = (h1 + dh * t_val) % 360
        
        s = s1 + (s2 - s1) * t_val
        b = b1 + (b2 - b1) * t_val
        
        colormap[i] = hsb_to_rgb(h, s, b)
        
    # Pre-calculate vignette mask
    y_indices, x_indices = np.mgrid[0:GRID_H, 0:GRID_W]
    cy, cx = GRID_H / 2.0, GRID_W / 2.0
    dist_sq = (x_indices - cx) ** 2 + (y_indices - cy) ** 2
    max_dist_sq = cx ** 2 + cy ** 2
    vignette = 1.0 - (dist_sq / max_dist_sq) * 0.65  # Fades up to 65% at corners
    vignette = np.clip(vignette, 0.0, 1.0)[:, :, np.newaxis]
    
    # Seed cells with multiple localized spiral growth centers
    np.random.seed(987)  # Fix internal seed for reproducibility of centers
    cells = np.zeros((GRID_H, GRID_W), dtype=np.int32)
    
    # Place ~32 spiral seeding centers
    n_centers = 32
    for _ in range(n_centers):
        cx_val = np.random.randint(8, GRID_W - 8)
        cy_val = np.random.randint(8, GRID_H - 8)
        radius = np.random.randint(4, 10)
        
        y, x = np.ogrid[:GRID_H, :GRID_W]
        mask = (x - cx_val)**2 + (y - cy_val)**2 <= radius**2
        cells[mask] = np.random.randint(0, N_STATES, np.sum(mask))

    # Create py5 image for fast scaling and rendering
    pg_image = py5.create_image(GRID_W, GRID_H, py5.RGB)

def update_ca():
    global cells
    target = (cells + 1) % N_STATES
    
    # Sum neighbors in state (cells + 1) % 16 using 2D rolls
    neighbor_count = np.zeros_like(cells, dtype=np.int32)
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        ( 0, -1),          ( 0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]
    for dy, dx in directions:
        rolled = np.roll(np.roll(cells, dy, axis=0), dx, axis=1)
        neighbor_count += (rolled == target)
        
    # Standard threshold rule: if 2 or more neighbors are in target state, transition
    advance = neighbor_count >= 2
    cells = np.where(advance, target, cells)

def draw():
    # Execute 1 update step per frame
    update_ca()
    
    # Map cell states to RGB colors
    color_array = colormap[cells]
    
    # Apply vignette
    color_array = (color_array * vignette).astype(np.uint8)
    
    # Write directly to the py5 image's pixel buffer
    global pg_image
    pg_image.load_np_pixels()
    pg_image.np_pixels[..., :3] = color_array
    pg_image.np_pixels[..., 3] = 255
    pg_image.update_np_pixels()
    
    # Draw scaled image to fill the 4K canvas
    py5.background(0)
    py5.image(pg_image, 0, 0, py5.width, py5.height)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        print("[Render Complete] Video and preview successfully generated.")
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()

from pathlib import Path
import shutil
import subprocess
import sys
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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Internal resolution for the metaball computation (to keep it real-time)
W_INT = SIZE[0] // 4
H_INT = SIZE[1] // 4

NUM_BALLS = 15

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global X, Y, pixel_array
    # Create coordinate grid
    y_vals = np.linspace(0, py5.height, H_INT)
    x_vals = np.linspace(0, py5.width, W_INT)
    Y, X = np.meshgrid(y_vals, x_vals, indexing='ij')
    
    # Pre-allocate image array (RGBA)
    pixel_array = np.zeros((H_INT, W_INT, 4), dtype=np.uint8)
    pixel_array[:, :, 3] = 255
    
    # Initialize ball positions and velocities
    global bx, by, bvx, bvy, br
    bx = np.random.rand(NUM_BALLS) * py5.width
    by = np.random.rand(NUM_BALLS) * py5.height
    
    # Balls move relatively slowly
    bvx = (np.random.rand(NUM_BALLS) - 0.5) * 20.0
    bvy = (np.random.rand(NUM_BALLS) - 0.5) * 20.0
    
    # Radiuses of the balls
    br = np.random.rand(NUM_BALLS) * 300 + 100

def draw():
    global bx, by, bvx, bvy, br, pixel_array
    
    # Update positions
    bx += bvx
    by += bvy
    
    # Bounce off walls
    bvx = np.where((bx < 0) | (bx > py5.width), -bvx, bvx)
    bvy = np.where((by < 0) | (by > py5.height), -bvy, bvy)
    bx = np.clip(bx, 0, py5.width)
    by = np.clip(by, 0, py5.height)
    
    # Calculate distance field
    # Sum of R^2 / ((X-x)^2 + (Y-y)^2)
    field = np.zeros((H_INT, W_INT))
    
    for i in range(NUM_BALLS):
        dist_sq = (X - bx[i])**2 + (Y - by[i])**2
        # Add a small epsilon to avoid division by zero
        dist_sq = np.maximum(dist_sq, 0.0001)
        field += (br[i]**2) / dist_sq
        
    # Field values > 1.0 are "inside" the metaballs
    # We will map the field directly to colors to create glowing blobs
    
    # Background gradient
    bg_r = np.linspace(20, 0, H_INT)[:, None]
    bg_b = np.linspace(50, 10, H_INT)[:, None]
    
    # Inside metaball colors
    # Map high field values to bright colors, low field values to background
    # We use a smoothstep-like function for the transition
    mask = np.clip(field * field, 0, 1) # Sharp mask
    
    # Core (very high field values) -> White/Yellow
    # Edge (field values near 1.0) -> Neon Pink/Orange
    
    core_mask = np.clip((field - 1.5) * 2.0, 0, 1)
    edge_mask = np.clip(field * 1.5, 0, 1)
    
    r = (bg_r * (1 - edge_mask) + 255 * edge_mask).astype(np.uint8)
    g = (0 * (1 - edge_mask) + 50 * edge_mask * (1 - core_mask) + 255 * core_mask).astype(np.uint8)
    b = (bg_b * (1 - edge_mask) + 150 * edge_mask * (1 - core_mask) + 100 * core_mask).astype(np.uint8)
    
    pixel_array[:, :, 0] = r
    pixel_array[:, :, 1] = g
    pixel_array[:, :, 2] = b
    
    img = py5.create_image_from_numpy(pixel_array, "RGBA")
    
    # Draw scaled up to full size (bilinear filtering makes it smooth)
    py5.image(img, 0, 0, py5.width, py5.height)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

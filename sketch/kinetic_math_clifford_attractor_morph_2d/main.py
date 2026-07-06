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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Peter de Jong Attractor Parameters
NUM_PARTICLES = 1000000
WARMUP_ITERATIONS = 40
DRAW_ITERATIONS = 30

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.load_np_pixels()
    
def get_dejong_points(a, b, c, d):
    # Initialize random starting points
    x = np.random.uniform(-2, 2, NUM_PARTICLES)
    y = np.random.uniform(-2, 2, NUM_PARTICLES)
    
    # Warmup phase: let particles settle onto the strange attractor manifold
    for _ in range(WARMUP_ITERATIONS):
        x_new = np.sin(a * y) - np.cos(b * x)
        y_new = np.sin(c * x) - np.cos(d * y)
        x, y = x_new, y_new
        
    points_x = []
    points_y = []
    
    # Draw phase: collect points that are now moving along the attractor
    for _ in range(DRAW_ITERATIONS):
        x_new = np.sin(a * y) - np.cos(b * x)
        y_new = np.sin(c * x) - np.cos(d * y)
        x, y = x_new, y_new
        points_x.append(x)
        points_y.append(y)
            
    all_x = np.concatenate(points_x)
    all_y = np.concatenate(points_y)
    return all_x, all_y

def draw():
    # Calculate time parameter for smooth loop
    theta = (py5.frame_count / TOTAL_FRAMES) * np.pi * 2
    nx = np.cos(theta) * 0.5 + 0.5
    ny = np.sin(theta) * 0.5 + 0.5
    
    # Smoothly morphing parameters a, b, c, d using 2D noise for seamless loop
    # Peter de Jong attractors look great with parameters between -3 and 3
    a = (py5.noise(nx * 1.5, ny * 1.5) - 0.5) * 5.0
    b = (py5.noise(nx * 1.5 + 10, ny * 1.5 + 10) - 0.5) * 5.0
    c = (py5.noise(nx * 1.5 + 20, ny * 1.5 + 20) - 0.5) * 5.0
    d = (py5.noise(nx * 1.5 + 30, ny * 1.5 + 30) - 0.5) * 5.0
    
    px, py = get_dejong_points(a, b, c, d)
    
    # Scale to screen (De Jong attractors fit cleanly in -2.5 to 2.5)
    scale = min(py5.width, py5.height) / 4.5
    screen_x = ((px * scale) + py5.width / 2).astype(np.int32)
    screen_y = ((py * scale) + py5.height / 2).astype(np.int32)
    
    # Filter out of bounds
    valid = (screen_x >= 0) & (screen_x < py5.width) & (screen_y >= 0) & (screen_y < py5.height)
    screen_x = screen_x[valid]
    screen_y = screen_y[valid]
    
    # Create 2D histogram (density map) using fast numpy indexing
    # This prevents the JVM from crashing by avoiding millions of py5.points() calls
    actual_height, actual_width = py5.np_pixels.shape[:2]
    density = np.zeros((actual_height, actual_width), dtype=np.int32)
    np.add.at(density, (screen_y, screen_x), 1)
    
    # Logarithmic scaling for beautiful dynamic range
    density_log = np.log1p(density)
    max_dens = np.max(density_log)
    if max_dens > 0:
        normalized = density_log / max_dens
    else:
        normalized = density_log
        
    # Map to colors using a glowing neon palette
    # Calculate a shifting hue
    hue_shift = (py5.frame_count / TOTAL_FRAMES * 2.0 * np.pi)
    
    rgb = np.zeros((actual_height, actual_width, 3), dtype=np.float32)
    
    # Create an iridescent color gradient based on density
    # Low density = dark blue/purple, High density = bright cyan/white
    rgb[:, :, 0] = normalized * (np.sin(normalized * 3.14 + hue_shift) * 0.5 + 0.5) * 255 # R
    rgb[:, :, 1] = normalized * (np.sin(normalized * 3.14 + hue_shift + 2.0) * 0.5 + 0.5) * 255 # G
    rgb[:, :, 2] = normalized * (np.sin(normalized * 3.14 + hue_shift + 4.0) * 0.5 + 0.5) * 255 # B
    
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    
    py5.load_np_pixels()
    # py5 np_pixels is ARGB
    py5.np_pixels[:, :, 1] = rgb[:, :, 0]
    py5.np_pixels[:, :, 2] = rgb[:, :, 1]
    py5.np_pixels[:, :, 3] = rgb[:, :, 2]
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
        import os
        os._exit(0)

py5.run_sketch()

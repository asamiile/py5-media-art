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

NUM_PARTICLES = 50000

x = None
y = None
z = None

# Colors
# Deep Void Background (#03010A)
# Crimson Red (#D90429) -> Hot Pink (#FF006E) -> Vivid Purple (#8338EC) -> Electric Blue (#3A86FF)
C1, C2, C3, C4 = None, None, None, None

def setup():
    global x, y, z, C1, C2, C3, C4
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize near the origin with tiny perturbations
    x = np.random.normal(0.1, 0.01, NUM_PARTICLES)
    y = np.random.normal(0.1, 0.01, NUM_PARTICLES)
    z = np.random.normal(0.1, 0.01, NUM_PARTICLES)
    
    C1 = py5.color(217, 4, 41)
    C2 = py5.color(255, 0, 110)
    C3 = py5.color(131, 56, 236)
    C4 = py5.color(58, 134, 255)
    
    py5.background(3, 1, 10)

def draw():
    global x, y, z
    
    # Semi-transparent background for trails
    py5.fill(3, 1, 10, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Lorenz parameters
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    dt = 0.006
    
    # RK4 or Euler. Euler is fast enough for visual effects.
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    
    x += dx * dt
    y += dy * dt
    z += dz * dt
    
    # Time-varying rotation
    t = py5.frame_count / TOTAL_FRAMES
    angle = t * np.pi * 2.0
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    x_rot = x * cos_a - y * sin_a
    y_rot = x * sin_a + y * cos_a
    
    # Projection
    scale = 35.0
    screen_x = py5.width / 2 + x_rot * scale
    screen_y = py5.height / 2 + (y_rot * 0.4 - z * 0.8) * scale + 600
    
    # Draw points in color bins
    # Color based on Z coordinate
    # Z usually ranges from 0 to 50 in the Lorenz attractor
    
    coords = np.column_stack((screen_x, screen_y))
    
    num_bins = 10
    z_min, z_max = 0.0, 50.0
    
    py5.stroke_weight(2)
    
    for i in range(num_bins):
        bin_start = z_min + (z_max - z_min) * (i / num_bins)
        bin_end = z_min + (z_max - z_min) * ((i + 1) / num_bins)
        
        # Color interpolation
        f = (i + 0.5) / num_bins
        if f < 0.33:
            c = py5.lerp_color(C1, C2, f / 0.33)
        elif f < 0.66:
            c = py5.lerp_color(C2, C3, (f - 0.33) / 0.33)
        else:
            c = py5.lerp_color(C3, C4, (f - 0.66) / 0.34)
            
        mask = (z >= bin_start) & (z < bin_end)
        bin_coords = coords[mask]
        
        if len(bin_coords) > 0:
            py5.stroke(c)
            py5.points(bin_coords)
    
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

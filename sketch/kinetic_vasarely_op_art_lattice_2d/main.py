from pathlib import Path
import shutil
import subprocess
import sys
import math
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

# Grid parameters
R = 40
dx = R * math.sqrt(3)
dy = R * 1.5

colors = [
    "#C1121F", # Red
    "#003049", # Navy
    "#E9C46A", # Yellow
    "#1D1E18"  # Black
]
bg_color = "#F0EFEB"

grid_points = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Pre-calculate grid points
    cols = int(py5.width / dx) + 4
    rows = int(py5.height / dy) + 4
    
    for row in range(-2, rows):
        for col in range(-2, cols):
            x = col * dx
            if row % 2 != 0:
                x += dx / 2
            y = row * dy
            grid_points.append((x, y, col, row))
            
    py5.no_stroke()

def draw():
    py5.background(bg_color)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # We want a seamless loop if possible, so we use a 4D noise cylinder
    # Or just a slow drift for now since noise loop is complex to write purely.
    # Actually, a seamless loop is easy:
    angle = t * py5.TWO_PI
    noise_r = 1.0
    nx = noise_r * math.cos(angle)
    ny = noise_r * math.sin(angle)
    
    for (x, y, col, row) in grid_points:
        # Scale down coordinates for noise sampling
        scale = 0.05
        # 4D noise for seamless looping!
        # X, Y for space, nx, ny for time loop
        n_val = py5.os_noise(col * scale, row * scale, nx, ny)
        
        # Determine radius
        # We want the radius to oscillate to create a bulging effect
        # Map noise (0 to 1) to radius multiplier
        r_mult = py5.remap(n_val, 0.2, 0.8, 0.1, 1.4)
        r_mult = py5.constrain(r_mult, 0.0, 1.5)
        
        # Determine color
        # Offset noise slightly for color so it doesn't perfectly match size
        c_val = py5.os_noise(col * scale + 100, row * scale + 100, nx, ny)
        c_idx = int(py5.remap(c_val, 0.2, 0.8, 0, len(colors)))
        c_idx = py5.constrain(c_idx, 0, len(colors) - 1)
        
        py5.fill(colors[c_idx])
        py5.ellipse(x, y, R * r_mult * 2, R * r_mult * 2)
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_pixels()
        # Ensure we didn't just draw a blank screen
        
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

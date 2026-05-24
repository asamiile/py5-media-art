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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

COLS = 120
ROWS = 80
SPACING_X = 16
SPACING_Y = 14

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(220, 90, 5) # Deep oceanic blue
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    # Render caustics using a grid of displaced points
    py5.stroke_weight(2.0)
    
    # Calculate offset to center the grid
    grid_w = COLS * SPACING_X
    grid_h = ROWS * SPACING_Y
    offset_x = (py5.width - grid_w) / 2
    offset_y = (py5.height - grid_h) / 2
    
    for r in range(ROWS):
        # Y coordinate flows downwards over time
        noise_y = r * 0.05 - t * 1.5
        
        for c in range(COLS):
            noise_x = c * 0.05 + py5.sin(t * 0.5) * 0.5
            
            # 3D Perlin noise to sample height map
            n = py5.noise(noise_x, noise_y, t)
            
            # Calculate gradient (derivative) of noise for displacement
            n_dx = py5.noise(noise_x + 0.01, noise_y, t) - n
            n_dy = py5.noise(noise_x, noise_y + 0.01, t) - n
            
            # The stronger the gradient, the more the light is refracted/displaced
            displace_x = n_dx * 8000
            displace_y = n_dy * 8000
            
            # Base positions
            bx = offset_x + c * SPACING_X
            by = offset_y + r * SPACING_Y
            
            # Displaced positions
            px = bx + displace_x
            py_c = by + displace_y
            
            # Intensity of light concentrates where displacement is minimal (caustics)
            # or where points bundle up together
            intensity = py5.remap(n, 0.2, 0.8, 0, 1) ** 2
            
            if intensity > 0.1:
                # Colors range from deep blue to bioluminescent cyan and white
                hue = (200 + intensity * 60) % 360
                saturation = max(0, 100 - intensity * 50)
                brightness = 30 + intensity * 70
                alpha = 20 + intensity * 80
                
                py5.stroke(hue, saturation, brightness, alpha)
                py5.point(px, py_c)
                
                # Optionally draw a tiny connecting line to the next horizontal point
                # to create fluid streaks
                if c < COLS - 1:
                    next_n = py5.noise(noise_x + 0.05, noise_y, t)
                    next_ndx = py5.noise(noise_x + 0.06, noise_y, t) - next_n
                    next_ndy = py5.noise(noise_x + 0.05, noise_y + 0.01, t) - next_n
                    nx = bx + SPACING_X + next_ndx * 8000
                    ny_c = by + next_ndy * 8000
                    
                    py5.stroke_weight(1.0)
                    py5.stroke(hue, saturation, brightness, alpha * 0.5)
                    py5.line(px, py_c, nx, ny_c)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

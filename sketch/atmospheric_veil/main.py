from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Palette
SPACE_COLOR = (5, 10, 20)
VEIL_BLUE = (180, 210, 255)
VEIL_SILVER = (230, 240, 255)
SOLAR_AMBER = (255, 220, 150)

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(*SPACE_COLOR)

def draw():
    py5.background(*SPACE_COLOR)
    
    t = py5.frame_count * 0.005
    
    # Draw Background Stars
    py5.random_seed(42) # Consistent stars
    for _ in range(200):
        x = py5.random(py5.width)
        y = py5.random(py5.height)
        size = py5.random(0.5, 2)
        alpha = py5.random(50, 180)
        py5.no_stroke()
        py5.fill(255, alpha)
        py5.ellipse(x, y, size, size)

    # Generate Noise-based Veil using NumPy for efficiency
    # We'll use py5.os_noise but sampled onto a grid
    grid_res = 8 # Sample every 8 pixels for speed, then upscale or use rects
    rows = py5.height // grid_res + 1
    cols = py5.width // grid_res + 1
    
    # Create coordinate grid
    x = np.linspace(0, py5.width * 0.002, cols)
    y = np.linspace(0, py5.height * 0.002, rows)
    xv, yv = np.meshgrid(x, y)
    
    # Domain warping
    # q = ( f(p), f(p+d) )
    # r = f(p + 4*q)
    
    # Vectorized noise is harder with py5.os_noise, so we'll do a hybrid approach
    # Sample noise field
    noise_field = np.zeros((rows, cols))
    for r in range(rows):
        for c in range(cols):
            # Domain warp layer 1
            qx = py5.os_noise(xv[r, c], yv[r, c], t)
            qy = py5.os_noise(xv[r, c] + 5.2, yv[r, c] + 1.3, t)
            
            # Domain warp layer 2
            rx = py5.os_noise(xv[r, c] + 4 * qx + 1.7, yv[r, c] + 4 * qy + 9.2, t)
            ry = py5.os_noise(xv[r, c] + 4 * qx + 8.3, yv[r, c] + 4 * qy + 2.8, t)
            
            # Final noise
            noise_field[r, c] = py5.os_noise(xv[r, c] + 4 * rx, yv[r, c] + 4 * ry, t)

    # Render noise field
    py5.no_stroke()
    for r in range(rows - 1):
        for c in range(cols - 1):
            val = noise_field[r, c]
            if val > 0.4: # Cloud threshold
                # Normalize val to 0-1 range above threshold
                nv = (val - 0.4) / 0.6
                
                # Spectral color mapping
                if nv < 0.5:
                    # Blue to Silver transition
                    col = py5.lerp_color(
                        py5.color(*VEIL_BLUE, 0),
                        py5.color(*VEIL_BLUE, 180),
                        nv * 2
                    )
                else:
                    col = py5.lerp_color(
                        py5.color(*VEIL_BLUE, 180),
                        py5.color(*VEIL_SILVER, 255),
                        (nv - 0.5) * 2
                    )
                
                # Solar edge effect (using derivative proxy)
                edge = 0
                if c > 0:
                    edge = abs(noise_field[r, c] - noise_field[r, c-1]) * 10
                
                py5.fill(col)
                py5.rect(c * grid_res, r * grid_res, grid_res, grid_res)
                
                if edge > 0.2:
                    py5.fill(*SOLAR_AMBER, edge * 100)
                    py5.rect(c * grid_res, r * grid_res, grid_res, grid_res)

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()

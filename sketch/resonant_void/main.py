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

# Animation Parameters
GRID_RES = 100
NOISE_SCALE = 0.05
WAVE_SPEED = 0.05
STARS_COUNT = 1000

stars = None

def setup():
    global stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate static starfield
    stars = np.random.uniform(0, 1, (STARS_COUNT, 3))
    stars[:, 0] *= py5.width * 2
    stars[:, 0] -= py5.width
    stars[:, 1] *= py5.height * 2
    stars[:, 1] -= py5.height
    stars[:, 2] *= -2000  # depth

def draw_starfield():
    py5.push_matrix()
    py5.stroke(255, 200)
    py5.stroke_weight(1)
    for i in range(STARS_COUNT):
        py5.point(stars[i, 0], stars[i, 1], stars[i, 2])
    py5.pop_matrix()

def draw():
    py5.background(5, 5, 16)
    
    # Camera setup
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_x(py5.radians(60))
    py5.rotate_z(py5.frame_count * 0.01)
    
    draw_starfield()
    
    # Draw Resonant Membrane
    t = py5.frame_count * WAVE_SPEED
    
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    # Use a grid for the membrane
    step = 800 / GRID_RES
    
    for i in range(GRID_RES):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(GRID_RES + 1):
            for x_idx in [i, i + 1]:
                x = (x_idx - GRID_RES / 2) * step
                y = (j - GRID_RES / 2) * step
                
                # Resonant Wave Math
                dist = np.sqrt(x**2 + y**2)
                # Multiple harmonics
                z = 100 * np.sin(dist * 0.02 - t)
                z += 40 * np.sin(x * 0.05 + t * 0.5)
                z += 30 * np.cos(y * 0.04 - t * 0.8)
                
                # HSB Color Mapping based on z and dist
                # Normalized distance 0 to 1
                norm_dist = dist / 600
                hue = (200 + z * 0.5 + norm_dist * 50) % 255
                sat = 150 + z * 0.2
                brt = 200 + z
                
                py5.color_mode(py5.HSB, 255)
                py5.stroke(hue, sat, brt, 180)
                py5.vertex(x, y, z)
        py5.end_shape()

    py5.color_mode(py5.RGB, 255)
    
    # Save frame
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

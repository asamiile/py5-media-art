from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Grid settings
RES = 6 # High resolution grid
COLS = SIZE[0] // RES + 1
ROWS = SIZE[1] // RES + 1

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 5, 5)
    
    # Set up lighting for metallic feel
    py5.ambient_light(15, 10, 25)
    # Main silver light
    py5.directional_light(160, 165, 180, 0, 1, -0.5)
    # Cyan highlight from the side
    py5.point_light(0, 200, 255, py5.width, -200, 500)
    # Violet accent
    py5.point_light(100, 50, 200, 0, py5.height, 500)
    
    py5.light_specular(255, 255, 255)
    py5.specular(255, 255, 255)
    py5.shininess(30.0)

    t = py5.frame_count * 0.012
    
    # Using meshgrid for efficient calculation
    x_range = np.linspace(0, 4, COLS)
    y_range = np.linspace(0, 4, ROWS)
    xx, yy = np.meshgrid(x_range, y_range)
    
    # Domain warping for viscous flow
    # First layer of noise for warping
    q_x = py5.noise(xx * 0.4, yy * 0.4, t * 0.5)
    q_y = py5.noise(xx * 0.4 + 5.2, yy * 0.4 + 1.3, t * 0.5)
    
    # Second layer (more detailed)
    r_x = py5.noise(xx + 4.0 * q_x + 1.7, yy + 4.0 * q_y + 9.2, t * 0.3)
    r_y = py5.noise(xx + 4.0 * q_x + 8.3, yy + 4.0 * q_y + 2.8, t * 0.3)
    
    # Final terrain height
    z = py5.noise(xx + 2.0 * r_x, yy + 2.0 * r_y, t * 0.2)
    z = (z - 0.5) * 450 # Scale to height range
    
    # Render metallic surface
    py5.no_stroke()
    # Color depends on slope/height slightly to enhance liquid feel
    
    py5.push_matrix()
    # Tilt the whole scene for perspective
    py5.translate(0, 0, -200)
    py5.rotate_x(py5.radians(10))
    
    for r in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        # Material properties
        py5.fill(180, 185, 195)
        for c in range(COLS):
            # We calculate vertices for r and r+1 to build the strip
            # The triangulation helps with smooth lighting in P3D
            py5.vertex(c * RES, r * RES, z[r, c])
            py5.vertex(c * RES, (r + 1) * RES, z[r + 1, c])
        py5.end_shape()
    py5.pop_matrix()

    # Save frame etc
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

py5.run_sketch()

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
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_LAYERS = 24


def setup():
    py5.size(*SIZE)
    py5.background(10, 10, 26)  # Midnight Indigo
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    # Subtle background persistence for trails
    py5.no_stroke()
    py5.fill(10, 10, 26, 30)
    py5.rect(0, 0, py5.width, py5.height)

    # Global time for animation
    t = py5.frame_count * 0.015

    py5.blend_mode(py5.ADD)
    
    # Layered membranes
    for i in range(NUM_LAYERS):
        # Layer specific parameters
        layer_offset = i * 0.3
        noise_scale = 0.0008 + (i % 6) * 0.0001
        
        # Color based on layer index - even softer alphas
        if i % 3 == 0:
            py5.fill(127, 255, 212, 8)  # Seafoam Teal
        elif i % 3 == 1:
            py5.fill(255, 182, 193, 8)  # Soft Rose
        else:
            py5.fill(153, 102, 204, 8)  # Amethyst Violet
            
        py5.begin_shape()
        # Top edge of the membrane
        points = []
        # Higher resolution for smoother curves
        for x in range(0, py5.width + 11, 10):
            # Domain warping
            nx = x * noise_scale
            ny = layer_offset + t
            
            n1 = py5.os_noise(nx, ny)
            wx = nx + n1 * 0.4
            wy = ny + n1 * 0.4
            n2 = py5.os_noise(wx, wy)
            
            # Expanded base y position to cover more canvas
            y_base = py5.height * (0.1 + 0.8 * n2)
            y_shift = (i - NUM_LAYERS/2) * 20
            y_wave = np.sin(x * 0.002 + t * 1.2 + i * 0.15) * 100
            
            y = y_base + y_shift + y_wave
            points.append((x, y))
            py5.vertex(x, y)
            
        # Bottom edge
        for x, y in reversed(points):
            py5.vertex(x, y + 60 + np.sin(x * 0.004 + t * 0.8) * 30)
            
        py5.end_shape(py5.CLOSE)

    py5.blend_mode(py5.BLEND)

    # Marine snow particles - persistent using a small set
    np.random.seed(42)  # Fixed for consistent "snow" positions
    py5.stroke(224, 255, 255, 60)
    py5.stroke_weight(1.5)
    for _ in range(100):
        # Slowly drift snow
        px = (np.random.uniform(0, py5.width) + t * 10) % py5.width
        py = (np.random.uniform(0, py5.height) + t * 5) % py5.height
        py5.point(px, py)

    # Video recording
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error encoding video: {e}")


if __name__ == "__main__":
    py5.run_sketch()

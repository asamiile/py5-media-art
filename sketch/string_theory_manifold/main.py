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

# Animation parameters
rot_speed = 0.01
noise_speed = 0.5
noise_scale = 0.02

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(5, 5, 10)
    py5.color_mode(py5.HSB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Dark indigo background
    py5.background(160, 200, 30) # Dark Blue in HSB (H~160, S~200, B~30)
    
    # Subtle central glow
    py5.no_stroke()
    for r in range(4):
        py5.fill(160, 200, 60, 20)
        py5.circle(SIZE[0]//2, SIZE[1]//2, SIZE[1] * (0.8 - r * 0.1))
    
    # Static starfield
    np.random.seed(42)
    for _ in range(400):
        x, y = np.random.uniform(0, SIZE[0]), np.random.uniform(0, SIZE[1])
        z = np.random.uniform(-1000, 500)
        s = np.random.uniform(0.5, 3.0)
        alpha = np.random.uniform(100, 255) * (0.7 + 0.3 * np.sin(py5.frame_count * 0.1 + x))
        py5.fill(0, 0, 255, alpha) # White in HSB (S=0, B=255)
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.circle(0, 0, s)
        py5.pop_matrix()
    np.random.seed(None)

    py5.push_matrix()
    py5.translate(SIZE[0]//2, SIZE[1]//2, 0)
    
    t = py5.frame_count / FPS
    py5.rotate_y(t * 0.3)
    py5.rotate_x(t * 0.2)
    py5.rotate_z(t * 0.1)

    res = 60
    u_vals = np.linspace(0, py5.PI, res)
    v_vals = np.linspace(0, py5.TWO_PI, res)
    U, V = np.meshgrid(u_vals, v_vals)
    
    k = 3
    n = 1.0 + 0.5 * np.sin(t * 0.5)
    
    X = 420 * np.sin(U) * np.cos(V + k * U)
    Y = 420 * np.sin(U) * np.sin(V + k * U)
    Z = 420 * np.cos(U + n * V)
    
    py5.no_fill()
    
    # Render with glowing lines
    py5.stroke_weight(2.0)
    for i in range(res - 1):
        py5.begin_shape(py5.LINES)
        for j in range(res - 1):
            hue = ( (U[i, j] + V[i, j] + t * 0.2) * 40 ) % 255
            py5.stroke(hue, 180, 255, 180)
            
            py5.vertex(X[i, j], Y[i, j], Z[i, j])
            py5.vertex(X[i+1, j], Y[i+1, j], Z[i+1, j])
            
            py5.vertex(X[i, j], Y[i, j], Z[i, j])
            py5.vertex(X[i, j+1], Y[i, j+1], Z[i, j+1])
        py5.end_shape()

    py5.pop_matrix()

    # Save frames and exit
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

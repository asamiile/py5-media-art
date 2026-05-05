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

# Constants
STAR_COUNT = 800
GRID_RES = 60
TERRAIN_SIZE = 1200

def get_height(x, y, t):
    # Domain warping
    # h = noise(x + noise(x,y), y + noise(x,y))
    q_x = py5.noise(x * 0.002, y * 0.002, t * 0.2) * 200
    q_y = py5.noise(x * 0.002 + 100, y * 0.002 + 100, t * 0.2) * 200
    
    h = py5.noise((x + q_x) * 0.003, (y + q_y) * 0.003, t * 0.1)
    return h * 400

stars = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    
    # Init stars
    for _ in range(STAR_COUNT):
        stars.append((np.random.uniform(-2000, 2000), np.random.uniform(-1000, 1000), np.random.uniform(-2000, 2000), np.random.uniform(50, 150)))
        
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)

def draw():
    t = py5.frame_count / TOTAL_FRAMES
    
    # 1. Background & Lighting
    py5.background(5, 5, 15)
    py5.ambient_light(40, 40, 80)
    py5.directional_light(150, 150, 255, 0.5, 1, -0.5)
    
    # Camera
    angle = py5.frame_count * 0.005
    py5.camera(800 * np.cos(angle), -600, 800 * np.sin(angle), 0, 0, 0, 0, 1, 0)
    
    # 2. Draw Stars
    py5.no_stroke()
    for sx, sy, sz, s_alpha in stars:
        py5.push_matrix()
        py5.translate(sx, sy, sz)
        py5.fill(255, s_alpha)
        py5.box(2)
        py5.pop_matrix()

    # 3. Draw Terrain
    py5.push_matrix()
    py5.translate(-TERRAIN_SIZE/2, 0, -TERRAIN_SIZE/2)
    
    step = TERRAIN_SIZE / GRID_RES
    
    # Render mesh
    for i in range(GRID_RES):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(GRID_RES + 1):
            x = i * step
            z = j * step
            
            h1 = get_height(x, z, t)
            h2 = get_height(x + step, z, t)
            
            # Base terrain color
            py5.fill(30, 30, 50, 200)
            py5.no_stroke()
            py5.vertex(x, -h1, z)
            py5.vertex(x + step, -h2, z)
            
            # Periodic contour pulse
            contour_pulse = np.sin(h1 * 0.1 + t * py5.TWO_PI * 2)
            if contour_pulse > 0.95:
                py5.stroke(0, 255, 150, 200) # Neon Emerald
                py5.stroke_weight(2)
            elif abs(contour_pulse) < 0.05:
                py5.stroke(200, 50, 255, 150) # Electric Amethyst
                py5.stroke_weight(1)
            else:
                py5.no_stroke()
                
        py5.end_shape()
    py5.pop_matrix()

    # 4. Capture
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.5):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

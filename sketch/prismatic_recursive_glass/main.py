import numpy as np
from pathlib import Path
import subprocess
import sys
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
DURATION_SEC = 10  # Reduced to 10s to keep under 50MB
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    py5.background(0)

def draw_recursive_crystal(depth, size):
    if depth == 0:
        return
        
    py5.box(size)
    
    half = size / 2.0
    new_size = size * 0.45
    
    # Time-dependent rotation for the unfolding effect
    t = py5.frame_count * 0.01 + depth * 0.5
    rot = np.sin(t) * py5.PI / 4.0
    
    positions = [
        (half, half, half),
        (-half, half, half),
        (half, -half, half),
        (-half, -half, half),
        (half, half, -half),
        (-half, half, -half),
        (half, -half, -half),
        (-half, -half, -half),
    ]
    
    for pos in positions:
        py5.push_matrix()
        py5.translate(pos[0], pos[1], pos[2])
        py5.rotate_x(rot)
        py5.rotate_y(rot)
        py5.rotate_z(rot)
        draw_recursive_crystal(depth - 1, new_size)
        py5.pop_matrix()

def draw():
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Camera setup
    t_cam = py5.frame_count * 0.005
    py5.camera(np.cos(t_cam) * 800, -400, np.sin(t_cam) * 800,
               0, 0, 0,
               0, 1, 0)
               
    # Chromatic aberration offsets
    offsets = [
        (-0.02, (255, 0, 0)),    # Red
        (0.0, (0, 255, 0)),      # Green
        (0.02, (0, 0, 255))      # Blue
    ]
    
    for offset_angle, color in offsets:
        py5.push_matrix()
        py5.rotate_y(offset_angle * np.sin(py5.frame_count * 0.02))
        py5.stroke(*color, 120)
        draw_recursive_crystal(4, 300)
        py5.pop_matrix()
    
    # Render starfield background (drawn in fixed screen space)
    py5.camera()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    np.random.seed(42)
    py5.stroke_weight(1)
    py5.begin_shape(py5.POINTS)
    for _ in range(2000):
        py5.stroke(255, 255, 255, np.random.randint(50, 150))
        py5.vertex(np.random.uniform(0, py5.width), np.random.uniform(0, py5.height))
    py5.end_shape()
    py5.hint(py5.ENABLE_DEPTH_TEST)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            # Add video bitrate limit to stay under 50MB
            "-b:v", "20M", "-maxrate", "25M", "-bufsize", "30M",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()

from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Pendulum Physics
N_PENDULUMS = 100
LENGTH_START = 0.5
LENGTH_END = 1.0
GRAVITY = 9.81

# Pre-calculate pendulum properties
lengths = np.linspace(LENGTH_START, LENGTH_END, N_PENDULUMS)
frequencies = np.sqrt(GRAVITY / lengths)
phases = np.zeros(N_PENDULUMS)

# 3D layout parameters
SPACING = 30
Z_START = 500

def project_3d_to_2d(points_3d, fov=1200):
    z = points_3d[:, 2] + 2000
    z = np.maximum(z, 1.0)
    x_proj = (points_3d[:, 0] * fov) / z
    y_proj = (points_3d[:, 1] * fov) / z
    x_proj += SIZE[0] / 2
    y_proj += SIZE[1] / 2
    return np.column_stack((x_proj, y_proj))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 5, 16)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count / FPS
    max_angle = np.pi / 4
    angles = max_angle * np.cos(frequencies * time + phases)
    
    x_pos = lengths * 1500 * np.sin(angles)
    y_pos = lengths * 1500 * np.cos(angles) - 1000
    z_pos = np.linspace(Z_START, Z_START - N_PENDULUMS * SPACING, N_PENDULUMS)
    
    points_3d = np.column_stack((x_pos, y_pos, z_pos))
    
    rot_angle = time * 0.1
    c, s = np.cos(rot_angle), np.sin(rot_angle)
    rot_x = points_3d[:, 0] * c - points_3d[:, 2] * s
    rot_z = points_3d[:, 0] * s + points_3d[:, 2] * c
    points_3d[:, 0] = rot_x
    points_3d[:, 2] = rot_z
    
    points_2d = project_3d_to_2d(points_3d)
    
    origin_3d = np.zeros((N_PENDULUMS, 3))
    origin_3d[:, 1] = -1000
    origin_3d[:, 2] = z_pos
    
    rot_x_org = origin_3d[:, 0] * c - origin_3d[:, 2] * s
    rot_z_org = origin_3d[:, 0] * s + origin_3d[:, 2] * c
    origin_3d[:, 0] = rot_x_org
    origin_3d[:, 2] = rot_z_org
    
    origin_2d = project_3d_to_2d(origin_3d)
    
    py5.stroke_weight(2)
    py5.stroke(0, 255, 255, 150)
    
    lines_array = np.column_stack((origin_2d[:, 0], origin_2d[:, 1], points_2d[:, 0], points_2d[:, 1]))
    py5.lines(lines_array)
    
    py5.stroke_weight(12)
    normalized_z = np.linspace(0, 1, N_PENDULUMS)
    
    for i in range(N_PENDULUMS):
        r = int(255 * normalized_z[i])
        g = int(255 * (1 - normalized_z[i]))
        b = 255
        py5.stroke(r, g, b, 255)
        py5.point(points_2d[i, 0], points_2d[i, 1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
        import os
        os._exit(0)

py5.run_sketch()

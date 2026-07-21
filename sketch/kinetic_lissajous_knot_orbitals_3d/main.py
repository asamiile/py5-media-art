from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lissajous resolution
NUM_POINTS = 3000

def get_rotation_matrix_3d_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ])

def get_rotation_matrix_3d_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ])

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40) # Fade to black
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.blend_mode(py5.ADD)
    
    # Base parameters for the Lissajous knot
    # Animate these to make the knot morph
    a = 3.0 + np.sin(t * py5.TWO_PI) * 2.0
    b = 4.0 + np.cos(t * py5.TWO_PI * 1.5) * 1.0
    c = 5.0 + np.sin(t * py5.TWO_PI * 0.5) * 2.0
    
    delta = t * py5.TWO_PI * 2.0
    
    # Generate points
    theta = np.linspace(0, py5.TWO_PI * 10, NUM_POINTS)
    
    # Rotate the whole knot
    rot_y = get_rotation_matrix_3d_y(t * py5.TWO_PI)
    rot_x = get_rotation_matrix_3d_x(t * py5.TWO_PI * 0.5)
    
    # Draw multiple strands
    num_strands = 3
    for s in range(num_strands):
        # Offset each strand slightly
        offset_theta = theta + (s * py5.TWO_PI / num_strands)
        x_s = np.sin(a * offset_theta + delta)
        y_s = np.sin(b * offset_theta)
        z_s = np.sin(c * offset_theta)
        
        strand_3d = np.column_stack((x_s, y_s, z_s))
        strand_3d = strand_3d @ rot_y.T @ rot_x.T
        
        # Simple orthographic projection with scale
        scale = py5.height * 0.35
        
        py5.stroke_weight(5)
        py5.no_fill()
        
        # Calculate color based on strand and time
        # Mix electric blue (210) and fiery orange (30)
        hue = 210 if s % 2 == 0 else 30
        hue = (hue + t * 90) % 360
        py5.stroke(hue, 90, 100, 80)
        
        py5.begin_shape()
        for p in strand_3d:
            py5.vertex(float(p[0] * scale), float(p[1] * scale))
        py5.end_shape()
        
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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

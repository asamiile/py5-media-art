import random
import numpy as np
from pathlib import Path
import shutil
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Randomize structure for each run
np.random.seed()
base_hue = np.random.uniform(0, 360)
branches_per_node = np.random.randint(2, 5)
max_depth = 6

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_crystal(depth, max_depth, t):
    if depth == 0:
        return
        
    scale_factor = 0.7 + 0.1 * np.sin(t * 2 + depth)
    
    length = 400.0 * scale_factor * (depth / max_depth)
    width = 40.0 * scale_factor * (depth / max_depth)
    
    hue = (base_hue + depth * 30 + t * 50) % 360
    py5.fill(hue, 80, 100, 80)
    py5.stroke((hue + 180) % 360, 90, 100, 90)
    py5.stroke_weight(2)
    
    # Draw the crystal segment (an elongated octahedron/box)
    py5.push_matrix()
    py5.translate(0, -length / 2, 0)
    py5.box(width, length, width)
    py5.pop_matrix()
    
    # Move to the end of the segment
    py5.translate(0, -length, 0)
    
    # Branch out
    for i in range(branches_per_node):
        py5.push_matrix()
        # Angle depends on time, depth, and branch index to create organic breathing
        angle_y = i * (py5.TWO_PI / branches_per_node) + t * 0.5
        angle_z = py5.PI / 4.0 + 0.2 * np.sin(t * 3 + i * 1.5 + depth)
        
        py5.rotate_y(angle_y)
        py5.rotate_z(angle_z)
        
        draw_crystal(depth - 1, max_depth, t)
        
        py5.pop_matrix()

def draw():
    py5.background(5, 5, 10)
    py5.lights()
    
    # Complex lighting to highlight the glass/metallic crystals
    py5.ambient_light(50, 50, 50)
    py5.directional_light(200, 200, 255, 1, 1, -1)
    py5.directional_light(255, 150, 100, -1, -1, 0)
    
    # Camera
    t = py5.frame_count * 0.01
    cam_radius = 2000.0 + 500.0 * np.sin(t)
    cam_x = np.cos(t * 0.5) * cam_radius
    cam_z = np.sin(t * 0.5) * cam_radius
    cam_y = -800.0 + 300.0 * np.sin(t * 0.8)
    
    py5.camera(cam_x, cam_y, cam_z, 0, -400, 0, 0, 1, 0)
    
    # Additive blending for a glowing look
    py5.blend_mode(py5.ADD)
    
    py5.push_matrix()
    # Slowly rotate the entire structure
    py5.rotate_y(t * 0.2)
    
    draw_crystal(max_depth, max_depth, t)
    
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

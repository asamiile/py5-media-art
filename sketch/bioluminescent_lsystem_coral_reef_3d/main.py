import math
from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.sphere_detail(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    random.seed(42)

def draw_branch(len_base, depth, t):
    if depth == 0:
        return
        
    # Organic sway via noise
    n = py5.os_noise(depth * 0.1, t * 0.5)
    
    # Calculate color based on depth
    # Base is dark violet, tips are cyan/magenta
    depth_ratio = depth / 7.0
    r = py5.lerp(0, 255, 1 - depth_ratio) if depth < 3 else py5.lerp(20, 0, depth_ratio)
    g = py5.lerp(0, 255, 1 - depth_ratio)
    b = py5.lerp(80, 255, 1 - depth_ratio)
    
    py5.stroke(r, g, b, 150)
    py5.fill(r, g, b, 200)
    
    # Draw segment
    py5.push_matrix()
    
    # Thickness
    w = max(2, depth * 2.0)
    py5.stroke_weight(w * 0.5)
    
    py5.line(0, 0, 0, 0, -len_base, 0)
    py5.translate(0, -len_base, 0)
    
    # Tip glow
    if depth == 1:
        py5.no_stroke()
        py5.fill(255, 255, 0, 200) # Yellow tips
        py5.sphere(4)
        
    # Branching
    new_len = len_base * 0.75
    
    # Branch 1
    py5.push_matrix()
    angle1 = 0.4 + py5.os_noise(depth * 0.2, t * 0.5, 0) * 0.3
    py5.rotate_z(angle1)
    py5.rotate_y(t + depth * 0.5)
    draw_branch(new_len, depth - 1, t)
    py5.pop_matrix()
    
    # Branch 2
    py5.push_matrix()
    angle2 = -0.3 - py5.os_noise(depth * 0.2, t * 0.5, 100) * 0.3
    py5.rotate_z(angle2)
    py5.rotate_y(-t - depth * 0.5)
    draw_branch(new_len, depth - 1, t)
    py5.pop_matrix()
    
    # Occasional Branch 3 for 3D fullness
    if depth % 2 == 0:
        py5.push_matrix()
        angle3 = 0.5 * math.sin(t * 2 + depth)
        py5.rotate_x(angle3)
        py5.rotate_y(t)
        draw_branch(new_len * 0.8, depth - 1, t)
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.background(1, 11, 25) # Deep navy
    py5.lights()
    py5.ambient_light(50, 50, 80)
    py5.directional_light(200, 200, 255, 0, 1, -1)
    
    t = py5.frame_count / 60.0
    
    # Camera orbit
    cam_radius = 800
    cam_x = math.cos(t * 0.2) * cam_radius
    cam_z = math.sin(t * 0.2) * cam_radius
    py5.camera(cam_x, -400, cam_z, 0, -200, 0, 0, 1, 0)
    
    # Global rotation and positioning
    py5.translate(0, 100, 0)
    
    # Draw multiple coral bases
    for i in range(5):
        py5.push_matrix()
        # Position in a ring
        angle = i * (py5.TWO_PI / 5)
        r = 150
        x = math.cos(angle) * r
        z = math.sin(angle) * r
        py5.translate(x, 0, z)
        
        # Base rotation
        py5.rotate_y(angle + t * 0.1)
        
        # Sway the entire base slightly
        py5.rotate_z(math.sin(t + i) * 0.1)
        py5.rotate_x(math.cos(t * 0.8 + i) * 0.1)
        
        draw_branch(120, 7, t + i)
        py5.pop_matrix()
        
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
        import os
        os._exit(0)

py5.run_sketch()

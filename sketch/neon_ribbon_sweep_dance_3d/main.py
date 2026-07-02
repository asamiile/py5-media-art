from pathlib import Path
import shutil
import subprocess
import sys
import random
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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def get_path_point(t, i, total_ribbons):
    base_r = 600 + 200 * np.sin(t * 1.3 + i)
    
    x = base_r * np.sin(t * 1.1) * np.cos(t * 0.7 + i * 0.5)
    y = base_r * np.cos(t * 1.2) * np.sin(t * 0.8 - i * 0.3)
    z = base_r * np.sin(t * 0.9) * np.sin(t * 1.5 + i * 0.7)
    
    nx = 100 * (py5.os_noise(x * 0.002, t * 0.5, i) - 0.5)
    ny = 100 * (py5.os_noise(y * 0.002, t * 0.5 + 10, i) - 0.5)
    nz = 100 * (py5.os_noise(z * 0.002, t * 0.5 + 20, i) - 0.5)
    
    return np.array([x + nx, y + ny, z + nz])

def get_ribbon_normal(p1, p2, p3):
    v1 = p2 - p1
    v2 = p3 - p2
    n = np.cross(v1, v2)
    norm = np.linalg.norm(n)
    if norm > 0:
        return n / norm
    return np.array([1.0, 0.0, 0.0])

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    rot_time = py5.frame_count * 0.005
    py5.rotate_y(rot_time)
    py5.rotate_x(rot_time * 0.7)
    
    num_ribbons = 8
    path_points = 200
    
    time_offset = py5.frame_count * 0.02
    
    for i in range(num_ribbons):
        base_hue = (py5.frame_count * 0.5 + i * (360 / num_ribbons)) % 360
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(path_points):
            t = time_offset + j * 0.03
            
            p1 = get_path_point(t, i, num_ribbons)
            p2 = get_path_point(t + 0.01, i, num_ribbons)
            p3 = get_path_point(t + 0.02, i, num_ribbons)
            
            normal = get_ribbon_normal(p1, p2, p3)
            
            width = 40 + 30 * np.sin(t * 5 + i)
            
            edge1 = p1 + normal * width
            edge2 = p1 - normal * width
            
            alpha = py5.remap(j, 0, path_points, 0, 80)
            if j > path_points - 20:
                alpha = py5.remap(j, path_points - 20, path_points, 80, 0)
                
            hue = (base_hue + j * 0.5) % 360
            py5.fill(hue, 80, 100, alpha)
            
            py5.vertex(edge1[0], edge1[1], edge1[2])
            py5.vertex(edge2[0], edge2[1], edge2[2])
            
        py5.end_shape()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

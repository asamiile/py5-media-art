from pathlib import Path
import shutil
import subprocess
import sys
import math
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.no_stroke()
    py5.sphere_detail(15)

def draw_lissajous_spheres(t_offset, c_r, c_g, c_b):
    num_points = 500
    py5.fill(c_r, c_g, c_b, 40)
    for i in range(num_points):
        t = py5.TWO_PI * i / num_points
        a = 3
        b = 2
        c = 5
        x = py5.width * 0.35 * math.sin(a * t + t_offset)
        y = py5.height * 0.35 * math.sin(b * t + t_offset * 1.3)
        z = py5.height * 0.35 * math.sin(c * t + t_offset * 0.7)
        r = 50 + 25 * math.sin(15 * t - t_offset * 4)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        py5.sphere(r)
        py5.pop_matrix()

def draw():
    py5.background(5, 5, 8)
    
    # Center scene
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Rotate scene
    py5.rotate_y(py5.frame_count * 0.015)
    py5.rotate_x(py5.frame_count * 0.008)
    
    py5.blend_mode(py5.ADD)
    
    t_off = py5.frame_count * 0.02
    
    # Render with chromatic aberration offsets
    draw_lissajous_spheres(t_off, 255, 0, 0)
    draw_lissajous_spheres(t_off + 0.05, 0, 255, 0)
    draw_lissajous_spheres(t_off + 0.1, 0, 0, 255)
    
    py5.blend_mode(py5.BLEND)

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

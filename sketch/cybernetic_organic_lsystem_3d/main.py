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
DURATION_SEC = 10
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
    py5.background(0)
    py5.blend_mode(py5.ADD)

def draw_branch(len, depth, max_depth, t):
    if depth == 0:
        return
        
    hue = (150 + depth * 20 + t * 50) % 360
    py5.stroke(hue, 80, 90, 80)
    
    # Pulse thickness and length
    weight = max(1, depth * 1.5 + py5.sin(t * 3 + depth) * 2)
    py5.stroke_weight(weight)
    
    current_len = len * (0.8 + 0.2 * py5.sin(t * 2 - depth * 0.5))
    py5.line(0, 0, 0, 0, -current_len, 0)
    
    py5.translate(0, -current_len, 0)
    
    sway_x = py5.os_noise(depth * 0.1, t) * py5.PI / 4 - py5.PI / 8
    sway_z = py5.os_noise(depth * 0.1 + 100, t) * py5.PI / 4 - py5.PI / 8
    
    for angle in [py5.PI / 4, -py5.PI / 4]:
        py5.push_matrix()
        py5.rotate_x(sway_x)
        py5.rotate_z(angle + sway_z)
        py5.rotate_y(t * 2 + depth * py5.PI / 3)
        draw_branch(len * 0.7, depth - 1, max_depth, t)
        py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.camera(
        py5.width/2 + py5.cos(t) * 1200, py5.height/2 - 600 + py5.sin(t*0.5)*200, py5.height/2 + py5.sin(t) * 1200,
        py5.width/2, py5.height/2 - 400, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2 + 600, 0)
    py5.rotate_y(t)
    
    # Draw central glowing core
    py5.fill(150, 80, 100, 50)
    py5.no_stroke()
    py5.sphere_detail(10)
    py5.sphere(40 + 20 * py5.sin(t * 5))
    
    draw_branch(300, 9, 9, t)

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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

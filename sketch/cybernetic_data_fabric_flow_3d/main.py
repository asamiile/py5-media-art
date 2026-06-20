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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 10000

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)

def draw():
    # minimal fade for trails
    py5.no_stroke()
    py5.fill(0, 5)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.005
    
    py5.camera(
        py5.width/2 + py5.cos(t) * 800, py5.height/2 + py5.sin(t*0.5) * 600, 800,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_x(py5.PI/3)
    py5.rotate_z(t)
    
    py5.stroke_weight(2)
    
    # draw cyber fabric
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        # map to cylinder
        u = (i % 100) / 100.0 * py5.TWO_PI
        v = (i // 100) / 100.0 * 2000 - 1000
        
        radius = 400 + py5.os_noise(u * 2, v * 0.005, t) * 200
        x = radius * py5.cos(u + t)
        y = radius * py5.sin(u + t)
        z = v
        
        # flow offset
        offset = py5.os_noise(x * 0.002, y * 0.002, z * 0.002 + t * 5) * 100
        x += offset * py5.cos(u)
        y += offset * py5.sin(u)
        
        hue = (200 + offset * 2 + t * 50) % 360
        py5.stroke(hue, 80, 100, 20)
        
        py5.vertex(x, y, z)
    py5.end_shape()

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

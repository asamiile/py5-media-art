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
DURATION_SEC = 15  # Keep it short for testing
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Config
NUM_RIBBONS = 50
POINTS_PER_RIBBON = 100
RIBBON_WIDTH = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.hint(py5.DISABLE_DEPTH_TEST) # Additive blending looks better without depth testing
    py5.blend_mode(py5.ADD)

def draw():
    py5.background(0)
    
    # Camera movement
    t = py5.frame_count * 0.005
    py5.camera(
        py5.width/2 + py5.cos(t) * 800, py5.height/2 + py5.sin(t*0.7) * 400, (py5.height/2) / py5.tan(py5.PI/6) + py5.sin(t*1.1) * 500,
        py5.width/2, py5.height/2, 0,
        0, 1, 0
    )
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t)
    py5.rotate_x(t * 0.5)

    for i in range(NUM_RIBBONS):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        py5.no_stroke()
        
        hue = (180 + i * 5 + py5.frame_count * 0.5) % 360
        py5.fill(hue, 80, 50, 15)
        
        y_offset = (i - NUM_RIBBONS/2) * 20
        
        for j in range(POINTS_PER_RIBBON):
            # parametric ribbon path
            u = j * 0.05
            time_offset = py5.frame_count * 0.02
            
            # noise driven coords
            nx = py5.os_noise(u, i * 0.1, time_offset) * 1000 - 500
            ny = py5.os_noise(u + 10, i * 0.1, time_offset) * 1000 - 500 + y_offset
            nz = py5.os_noise(u + 20, i * 0.1, time_offset) * 1000 - 500
            
            # normal for width expansion
            # derivative approx
            dx = py5.os_noise(u + 0.01, i * 0.1, time_offset) * 1000 - 500 - nx
            dy = py5.os_noise(u + 10.01, i * 0.1, time_offset) * 1000 - 500 + y_offset - ny
            dz = py5.os_noise(u + 20.01, i * 0.1, time_offset) * 1000 - 500 - nz
            
            vec = np.array([dx, dy, dz])
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            
            # up vector
            up = np.array([0, 1, 0])
            side = np.cross(vec, up)
            snorm = np.linalg.norm(side)
            if snorm > 0:
                side /= snorm
                
            w = RIBBON_WIDTH * py5.sin(j / POINTS_PER_RIBBON * py5.PI) # taper edges
            
            py5.vertex(nx + side[0]*w, ny + side[1]*w, nz + side[2]*w)
            py5.vertex(nx - side[0]*w, ny - side[1]*w, nz - side[2]*w)
            
        py5.end_shape()


    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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

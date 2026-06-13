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
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(220, 80, 5) # Deep abyssal blue
    
    py5.ambient_light(200, 50, 40)
    py5.point_light(180, 80, 100, SIZE[0]//2, -SIZE[1]//2, 200) # Cyan light
    py5.point_light(300, 80, 80, -SIZE[0]//2, SIZE[1], 200) # Magenta light
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(t * py5.PI)
    
    py5.blend_mode(py5.ADD)
    
    num_lat = 100
    num_lon = 100
    r_base = 300
    
    for i in range(num_lat):
        lat0 = py5.PI * (-0.5 + float(i - 1) / num_lat)
        z0  = py5.sin(lat0)
        zr0 = py5.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i) / num_lat)
        z1  = py5.sin(lat1)
        zr1 = py5.cos(lat1)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(num_lon + 1):
            lon = py5.TWO_PI * float(j - 1) / num_lon
            x = py5.cos(lon)
            y = py5.sin(lon)
            
            # Parametric deformation (Diatom pores/ridges)
            m = 8
            n = 6
            deformation0 = 1.0 + 0.15 * py5.sin(m * lon) * py5.cos(n * lat0 * 2) + 0.05 * py5.cos(20*lat0 - t*py5.TWO_PI)
            deformation1 = 1.0 + 0.15 * py5.sin(m * lon) * py5.cos(n * lat1 * 2) + 0.05 * py5.cos(20*lat1 - t*py5.TWO_PI)
            
            r0 = r_base * deformation0
            r1 = r_base * deformation1
            
            # Color based on deformation
            hue = 180 + 40 * py5.sin(deformation0 * py5.PI)
            py5.fill(hue, 80, 60, 40)
            py5.vertex(x * zr0 * r0, y * zr0 * r0, z0 * r0)
            
            hue1 = 180 + 40 * py5.sin(deformation1 * py5.PI)
            py5.fill(hue1, 80, 60, 40)
            py5.vertex(x * zr1 * r1, y * zr1 * r1, z1 * r1)
            
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

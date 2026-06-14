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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(10, 20, 15)
    
    # Lighting
    py5.ambient_light(200, 20, 30)
    py5.directional_light(180, 80, 100, 1, 1, -1)
    py5.directional_light(30, 80, 80, -1, -1, 1)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    time = py5.frame_count * 0.02
    
    # Rotate the whole sculpture slowly
    py5.rotate_y(time * 0.3)
    py5.rotate_x(time * 0.2)
    py5.rotate_z(py5.sin(time * 0.1) * 0.5)
    
    num_elements = 60
    base_size = 800
    
    py5.no_stroke()
    
    for i in range(num_elements):
        py5.push_matrix()
        
        # distribute elements spherically using Fibonacci lattice or just noise
        phi = py5.acos(1 - 2*(i+0.5)/num_elements)
        theta = py5.PI * (1 + py5.sqrt(5)) * (i+0.5)
        
        # Expansion and contraction
        r = base_size * (0.5 + py5.sin(time + i*0.1) * 0.2)
        
        x = r * py5.cos(theta) * py5.sin(phi)
        y = r * py5.sin(theta) * py5.sin(phi)
        z = r * py5.cos(phi)
        
        py5.translate(x, y, z)
        
        # Individual rotations
        py5.rotate_x(time * 1.5 + i)
        py5.rotate_y(time * 1.2 + i*0.5)
        
        hue = (180 + py5.sin(time * 0.5 + i * 0.1) * 60) % 360
        py5.fill(hue, 70, 90, 80)
        
        if i % 2 == 0:
            py5.box(r * 0.15)
        else:
            # draw a simple pyramid/tetrahedron
            s = r * 0.2
            py5.begin_shape(py5.TRIANGLES)
            py5.vertex(0, -s, 0)
            py5.vertex(-s, s, s)
            py5.vertex(s, s, s)
            
            py5.vertex(0, -s, 0)
            py5.vertex(s, s, s)
            py5.vertex(0, s, -s)
            
            py5.vertex(0, -s, 0)
            py5.vertex(0, s, -s)
            py5.vertex(-s, s, s)
            
            py5.vertex(-s, s, s)
            py5.vertex(s, s, s)
            py5.vertex(0, s, -s)
            py5.end_shape()
            
        py5.pop_matrix()
        
        # Connect to center
        py5.stroke(hue, 50, 100, 30)
        py5.stroke_weight(2)
        py5.line(0, 0, 0, x, y, z)
        py5.no_stroke()

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

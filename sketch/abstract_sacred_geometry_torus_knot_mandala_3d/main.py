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
DURATION_SEC = 20
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
    py5.no_fill()
    
def draw_torus_knot(p, q, scale, tube_radius, segments, tube_segments, time):
    py5.begin_shape(py5.TRIANGLES)
    
    for i in range(segments):
        t1 = py5.map(i, 0, segments, 0, py5.TWO_PI)
        t2 = py5.map(i + 1, 0, segments, 0, py5.TWO_PI)
        
        # Calculate center path of knot
        r1 = scale * (2 + py5.cos(q * t1))
        x1 = r1 * py5.cos(p * t1)
        y1 = r1 * py5.sin(p * t1)
        z1 = scale * py5.sin(q * t1)
        
        r2 = scale * (2 + py5.cos(q * t2))
        x2 = r2 * py5.cos(p * t2)
        y2 = r2 * py5.sin(p * t2)
        z2 = scale * py5.sin(q * t2)
        
        # We'll just draw lines between points for a wireframe look, it's easier and looks cooler
        py5.vertex(x1, y1, z1)
        py5.vertex(x2, y2, z2)
        
    py5.end_shape()

def draw_wireframe_torus_knot(p, q, scale, points, time):
    py5.begin_shape(py5.LINE_STRIP)
    for i in range(points + 1):
        t = i * py5.TWO_PI / points
        r = scale * (2 + py5.cos(q * t))
        x = r * py5.cos(p * t)
        y = r * py5.sin(p * t)
        z = scale * py5.sin(q * t)
        
        # Add some noise to make it organic
        n = py5.os_noise(x * 0.01, y * 0.01, time * 0.5)
        
        hue = (i * 0.5 + time * 50) % 360
        py5.stroke(hue, 80, 100, 80)
        
        py5.vertex(x * (1 + n*0.2), y * (1 + n*0.2), z * (1 + n*0.2))
    py5.end_shape()

def draw():
    py5.background(5, 5, 15)
    
    time = py5.frame_count * 0.01
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    py5.blend_mode(py5.ADD)
    
    py5.rotate_x(time * 0.3)
    py5.rotate_y(time * 0.5)
    py5.rotate_z(time * 0.2)
    
    py5.stroke_weight(3)
    
    # Draw multiple interlocking knots
    for i in range(5):
        py5.push_matrix()
        
        py5.rotate_x(i * py5.PI / 5 + time * 0.1)
        py5.rotate_y(i * py5.PI / 5 + time * 0.2)
        
        # p=3, q=7 is a complex knot
        draw_wireframe_torus_knot(3, 7, 200 + i * 50, 1500, time + i * 10)
        
        py5.pop_matrix()
        
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

from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_polygon(radius, sides):
    py5.begin_shape()
    for i in range(sides):
        angle = py5.TWO_PI * i / sides
        py5.vertex(radius * np.cos(angle), radius * np.sin(angle))
    py5.end_shape(py5.CLOSE)

def draw_star(radius_in, radius_out, points):
    py5.begin_shape()
    for i in range(points * 2):
        angle = py5.TWO_PI * i / (points * 2)
        r = radius_in if i % 2 == 0 else radius_out
        py5.vertex(r * np.cos(angle), r * np.sin(angle))
    py5.end_shape(py5.CLOSE)

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.01
    
    # Draw multiple layers of the mandala
    layers = 12
    
    for i in range(layers):
        py5.push_matrix()
        
        # Complex rotation logic
        rot = t * (i + 1) * 0.2
        if i % 2 == 0:
            rot *= -1
        py5.rotate(rot)
        
        # Oscillating radius
        base_radius = 50 + i * 40
        radius_offset = np.sin(t * 2 + i) * 30
        r = base_radius + radius_offset
        
        # Color pulsing
        hue = (t * 50 + i * 30) % 360
        py5.stroke(hue, 80, 100, 80)
        py5.stroke_weight(2.0)
        py5.no_fill()
        
        # Geometry type alternates
        if i % 3 == 0:
            draw_polygon(r, 3 + (i % 5))
        elif i % 3 == 1:
            draw_star(r * 0.5, r, 5 + (i % 4))
        else:
            # Draw a ring of circles
            num_circles = 6 + i
            for c in range(num_circles):
                c_angle = py5.TWO_PI * c / num_circles
                py5.push_matrix()
                py5.rotate(c_angle)
                py5.translate(r, 0)
                py5.circle(0, 0, r * 0.3)
                py5.pop_matrix()
                
        py5.pop_matrix()
    
    # Outer intricate ring
    py5.push_matrix()
    py5.rotate(-t * 0.5)
    py5.stroke((t * 20) % 360, 60, 100, 40)
    for j in range(60):
        py5.rotate(py5.TWO_PI / 60)
        py5.line(400, 0, 450 + np.sin(t * 5 + j) * 50, 0)
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

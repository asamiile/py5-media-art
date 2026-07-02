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
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_metatron_cube(r):
    # Calculate the 13 centers
    centers = [(0, 0)]
    # Inner hexagon
    for i in range(6):
        angle = i * py5.PI / 3
        centers.append((py5.cos(angle) * r, py5.sin(angle) * r))
    # Outer hexagon
    for i in range(6):
        angle = i * py5.PI / 3
        centers.append((py5.cos(angle) * r * 2, py5.sin(angle) * r * 2))
        
    py5.stroke(40, 80, 100, 50) # Gold
    py5.stroke_weight(2)
    py5.no_fill()
    
    # Draw circles
    for c in centers:
        py5.ellipse(c[0], c[1], r*2, r*2)
        
    # Draw connecting lines
    py5.stroke_weight(1)
    py5.stroke(40, 80, 100, 30)
    for i in range(len(centers)):
        for j in range(i+1, len(centers)):
            py5.line(centers[i][0], centers[i][1], centers[j][0], centers[j][1])

def draw():
    py5.background(240, 100, 5, 20) # Deep dark blue trail
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.01
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    # Pulsing scale
    s = 1.0 + py5.sin(time) * 0.2
    py5.scale(s)
    
    # Rotate the whole thing
    py5.rotate(time * 0.2)
    
    # Draw kaleidoscope background layers
    num_layers = 6
    for i in range(num_layers):
        py5.push_matrix()
        # Alternate rotation directions
        py5.rotate(time * 0.5 * (-1 if i%2==0 else 1) * (i+1))
        
        hue = (time * 20 + i * 40) % 360
        py5.stroke(hue, 80, 100, 20)
        py5.stroke_weight(3)
        py5.no_fill()
        
        rad = 200 + i * 150
        sides = 3 + (i % 4)
        
        # Draw a polygon
        py5.begin_shape()
        for j in range(sides):
            angle = j * py5.TWO_PI / sides
            py5.vertex(py5.cos(angle) * rad, py5.sin(angle) * rad)
        py5.end_shape(py5.CLOSE)
        
        # draw multiple rotated copies for kaleidoscope
        for k in range(6):
            py5.rotate(py5.PI / 3)
            py5.begin_shape()
            for j in range(sides):
                angle = j * py5.TWO_PI / sides
                py5.vertex(py5.cos(angle) * rad, py5.sin(angle) * rad)
            py5.end_shape(py5.CLOSE)
            
        py5.pop_matrix()
        
    # Draw Metatron's Cube in the center
    py5.push_matrix()
    py5.rotate(-time * 0.1)
    draw_metatron_cube(120)
    py5.pop_matrix()

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

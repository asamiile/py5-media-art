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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Create data for rings
num_rings = 15
rings = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    max_radius = min(py5.width, py5.height) * 0.45
    
    for i in range(num_rings):
        ring = {
            "radius": py5.remap(i, 0, num_rings-1, 50, max_radius),
            "speed": py5.random(-0.02, 0.02),
            "segments": int(py5.random(6, 24)) * 2,
            "thickness": py5.random(1, 8),
            "hue": py5.random(180, 300), # Blues to purples
            "style": int(py5.random(3)) # 0: dots, 1: lines, 2: polygons
        }
        rings.append(ring)

def draw():
    py5.background(5, 5, 10, 30) # Trails
    
    py5.translate(py5.width/2, py5.height/2)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count
    
    for i, ring in enumerate(rings):
        py5.push_matrix()
        # Rotate entire ring over time
        py5.rotate(t * ring["speed"])
        
        # Pulse radius
        r = ring["radius"] + py5.sin(t * 0.05 + i) * 20
        
        py5.stroke(ring["hue"], 90, 100, 80)
        py5.stroke_weight(ring["thickness"])
        py5.no_fill()
        
        seg_angle = py5.TWO_PI / ring["segments"]
        
        if ring["style"] == 0:
            # Dots
            for j in range(ring["segments"]):
                ang = j * seg_angle
                py5.point(r * py5.cos(ang), r * py5.sin(ang))
                
        elif ring["style"] == 1:
            # Lines radiating outward
            for j in range(ring["segments"]):
                ang = j * seg_angle
                l = 10 + py5.sin(t * 0.1 + j) * 20
                x1 = r * py5.cos(ang)
                y1 = r * py5.sin(ang)
                x2 = (r + l) * py5.cos(ang)
                y2 = (r + l) * py5.sin(ang)
                py5.line(x1, y1, x2, y2)
                
        elif ring["style"] == 2:
            # Polygon
            py5.begin_shape()
            for j in range(ring["segments"]):
                ang = j * seg_angle
                # Alternate radius for star-like shapes
                rad = r if j % 2 == 0 else r * 0.8
                py5.vertex(rad * py5.cos(ang), rad * py5.sin(ang))
            py5.end_shape(py5.CLOSE)
            
        py5.pop_matrix()

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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

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
    # 2D rendering for this one
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw_petal(r, theta, width_factor, c1, c2, c3):
    py5.push_matrix()
    py5.rotate(theta)
    
    py5.begin_shape()
    py5.vertex(0, 0)
    # Control points for the bezier curve forming one side of the petal
    py5.bezier_vertex(r * c1, r * width_factor, 
                      r * c2, r * width_factor, 
                      r, 0)
    # Control points for the other side
    py5.bezier_vertex(r * c2, -r * width_factor, 
                      r * c1, -r * width_factor, 
                      0, 0)
    py5.end_shape()
    py5.pop_matrix()

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(15, 20, 10, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.02
    
    layers = 8
    
    for layer in range(layers, 0, -1):
        num_petals = 6 + (layer * 4)
        
        # Animate rotation and shape
        rotation_offset = t * (0.2 if layer % 2 == 0 else -0.2)
        radius = 150 * layer + np.sin(t + layer) * 50
        width_factor = 0.3 + np.cos(t * 0.5 + layer) * 0.2
        
        # Bezier control point modulators
        c1 = 0.3 + np.sin(t * 1.2) * 0.2
        c2 = 0.7 + np.cos(t * 0.8) * 0.2
        
        hue = (160 + layer * 25 + t * 30) % 360
        py5.stroke(hue, 80, 100, 80)
        py5.stroke_weight(3)
        py5.fill(hue, 90, 50, 15)
        
        py5.push_matrix()
        py5.rotate(rotation_offset)
        
        for p in range(num_petals):
            angle = (p / num_petals) * py5.TWO_PI
            draw_petal(radius, angle, width_factor, c1, c2, c3=0)
            
        py5.pop_matrix()
        
    # Draw central star
    py5.fill(60, 20, 100, 90)
    py5.no_stroke()
    num_points = 12
    inner_r = 20 + np.sin(t * 4) * 10
    outer_r = 60 + np.cos(t * 2) * 20
    
    py5.push_matrix()
    py5.rotate(t * 0.5)
    py5.begin_shape()
    for i in range(num_points * 2):
        angle = (i / (num_points * 2)) * py5.TWO_PI
        r = outer_r if i % 2 == 0 else inner_r
        py5.vertex(np.cos(angle) * r, np.sin(angle) * r)
    py5.end_shape(py5.CLOSE)
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

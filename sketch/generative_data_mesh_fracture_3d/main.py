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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Generating a grid of points for triangulation-like mesh
grid_points = []
cols, rows = 40, 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize base grid points with some random jitter
    for i in range(cols):
        for j in range(rows):
            x = py5.remap(i, 0, cols - 1, -600, 600)
            y = py5.remap(j, 0, rows - 1, -600, 600)
            
            # Add subtle jitter
            x += random.uniform(-10, 10)
            y += random.uniform(-10, 10)
            
            grid_points.append({'base_x': x, 'base_y': y})

def draw():
    py5.background(10, 12, 25) # Dark navy
    py5.translate(py5.width / 2, py5.height / 2 + 100, -200)
    
    # Slowly rotate landscape
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.005)
    
    # Define directional lighting for the surface
    py5.directional_light(200, 200, 200, 0.5, 0.5, -1)
    py5.ambient_light(50, 50, 60)
    
    # Render mesh as TRIANGLES
    py5.begin_shape(py5.TRIANGLES)
    for i in range(cols - 1):
        for j in range(rows - 1):
            idx1 = i * rows + j
            idx2 = (i + 1) * rows + j
            idx3 = i * rows + (j + 1)
            idx4 = (i + 1) * rows + (j + 1)
            
            indices = [(idx1, idx2, idx3), (idx2, idx4, idx3)]
            
            for tri in indices:
                pts = []
                # Determine if this triangle is "fracturing" based on noise and time
                center_x = sum([grid_points[idx]['base_x'] for idx in tri]) / 3
                center_y = sum([grid_points[idx]['base_y'] for idx in tri]) / 3
                
                n_val = py5.os_noise(center_x * 0.002, center_y * 0.002, py5.frame_count * 0.005)
                
                # Threshold for fracture spreads over time
                fracture_threshold = py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 0.2, 0.8)
                is_fractured = n_val < fracture_threshold
                
                for idx in tri:
                    p = grid_points[idx]
                    z = py5.os_noise(p['base_x'] * 0.005, p['base_y'] * 0.005, 0) * 200 - 100
                    
                    # If fractured, pull it up and scale it down slightly towards center
                    px, py, pz = p['base_x'], p['base_y'], z
                    if is_fractured:
                        px = py5.lerp(px, center_x, 0.15)
                        py = py5.lerp(py, center_y, 0.15)
                        pz += py5.remap(n_val, 0, fracture_threshold, 150, 0) # lift up
                        
                    pts.append((px, py, pz))
                
                if is_fractured:
                    py5.fill(15, 15, 20, 200) # Dark inside
                    # Neon magenta/cyan stroke for fractured edges
                    if (i + j) % 3 == 0:
                        py5.stroke(0, 255, 255) # Cyan
                    else:
                        py5.stroke(255, 0, 150) # Magenta
                    py5.stroke_weight(2)
                else:
                    py5.fill(180, 185, 190) # Silver surface
                    py5.no_stroke()
                
                for pt in pts:
                    py5.vertex(pt[0], pt[1], pt[2])
                    
    py5.end_shape()

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

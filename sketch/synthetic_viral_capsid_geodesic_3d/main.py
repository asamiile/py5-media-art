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

# Icosahedron constants
phi = (1.0 + np.sqrt(5.0)) / 2.0
base_vertices = [
    np.array([-1,  phi, 0]), np.array([ 1,  phi, 0]), np.array([-1, -phi, 0]), np.array([ 1, -phi, 0]),
    np.array([0, -1,  phi]), np.array([0,  1,  phi]), np.array([0, -1, -phi]), np.array([0,  1, -phi]),
    np.array([ phi, 0, -1]), np.array([ phi, 0,  1]), np.array([-phi, 0, -1]), np.array([-phi, 0,  1])
]
# Normalize
base_vertices = [v / np.linalg.norm(v) for v in base_vertices]

base_faces = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
]

def subdivide(triangles):
    new_triangles = []
    for tri in triangles:
        v0, v1, v2 = tri
        
        # Midpoints
        v01 = v0 + v1
        v12 = v1 + v2
        v20 = v2 + v0
        
        # Normalize
        v01 = v01 / np.linalg.norm(v01)
        v12 = v12 / np.linalg.norm(v12)
        v20 = v20 / np.linalg.norm(v20)
        
        new_triangles.append((v0, v01, v20))
        new_triangles.append((v1, v12, v01))
        new_triangles.append((v2, v20, v12))
        new_triangles.append((v01, v12, v20))
    return new_triangles

global sphere_triangles
sphere_triangles = []
for f in base_faces:
    sphere_triangles.append((base_vertices[f[0]], base_vertices[f[1]], base_vertices[f[2]]))

# Subdivide 3 times
for _ in range(3):
    sphere_triangles = subdivide(sphere_triangles)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(5, 90, 5) # Dark crimson/black
    py5.lights()
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, -500)
    
    t = py5.frame_count * 0.02
    
    # Rotate the whole structure
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.4)
    
    # py5.no_fill()
    py5.stroke(15, 90, 100, 80) # Bright red-orange lines
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)
    
    R = 800
    distortion_scale = 300
    noise_freq = 1.5
    
    py5.begin_shape(py5.TRIANGLES)
    for tri in sphere_triangles:
        # Calculate center of triangle to color it
        center = (tri[0] + tri[1] + tri[2]) / 3.0
        n_color = py5.os_noise(center[0]*noise_freq, center[1]*noise_freq, center[2]*noise_freq + t)
        
        hue = py5.remap(n_color, -1, 1, 0, 50) # Red to Yellow
        py5.fill(hue, 90, 80, 70)
        
        for v in tri:
            # Calculate displacement for each vertex
            n = py5.os_noise(v[0]*noise_freq, v[1]*noise_freq, v[2]*noise_freq + t)
            disp_v = v * (R + n * distortion_scale)
            py5.vertex(disp_v[0], disp_v[1], disp_v[2])
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

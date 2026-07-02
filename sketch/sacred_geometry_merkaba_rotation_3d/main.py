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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_tetrahedron(r):
    # Vertices of a tetrahedron inscribed in a sphere of radius r
    v0 = np.array([0, -r, 0])
    
    # Base triangle
    angle = np.pi * 2 / 3
    y_base = r * 1.0 / 3.0
    r_base = r * np.sqrt(8.0) / 3.0
    
    v1 = np.array([r_base, y_base, 0])
    v2 = np.array([r_base * np.cos(angle), y_base, r_base * np.sin(angle)])
    v3 = np.array([r_base * np.cos(2*angle), y_base, r_base * np.sin(2*angle)])
    
    verts = [v0, v1, v2, v3]
    faces = [(0,1,2), (0,2,3), (0,3,1), (1,3,2)]
    
    py5.begin_shape(py5.TRIANGLES)
    for face in faces:
        for i in face:
            py5.vertex(*verts[i])
    py5.end_shape()

def draw_star_tetrahedron(r):
    # Draw two intersecting tetrahedrons, one inverted
    py5.push_matrix()
    draw_tetrahedron(r)
    py5.pop_matrix()
    
    py5.push_matrix()
    py5.rotate_x(py5.PI)
    draw_tetrahedron(r)
    py5.pop_matrix()

def draw_icosahedron(r):
    # Icosahedron vertices
    phi = (1 + np.sqrt(5)) / 2
    a = r / np.sqrt(1 + phi**2)
    b = a * phi
    
    verts = [
        (-a, b, 0), (a, b, 0), (-a, -b, 0), (a, -b, 0),
        (0, -a, b), (0, a, b), (0, -a, -b), (0, a, -b),
        (b, 0, -a), (b, 0, a), (-b, 0, -a), (-b, 0, a)
    ]
    
    faces = [
        (0,11,5), (0,5,1), (0,1,7), (0,7,10), (0,10,11),
        (1,5,9), (5,11,4), (11,10,2), (10,7,6), (7,1,8),
        (3,9,4), (3,4,2), (3,2,6), (3,6,8), (3,8,9),
        (4,9,5), (2,4,11), (6,2,10), (8,6,7), (9,8,1)
    ]
    
    py5.begin_shape(py5.TRIANGLES)
    for face in faces:
        for i in face:
            py5.vertex(*verts[i])
    py5.end_shape()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(220, 90, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera / Perspective breathing
    fov = py5.PI / 3.0 + np.sin(t * 0.5) * 0.1
    camera_z = (py5.height / 2.0) / np.tan(fov / 2.0)
    py5.perspective(fov, py5.width / py5.height, camera_z / 10.0, camera_z * 10.0)
    
    py5.rotate_x(t * 0.3)
    py5.rotate_y(t * 0.4)
    py5.rotate_z(t * 0.2)
    
    num_layers = 4
    
    for i in range(num_layers):
        py5.push_matrix()
        
        # Complex nested rotations
        py5.rotate_x(t * (0.5 + i * 0.2))
        py5.rotate_y(-t * (0.4 + i * 0.3))
        
        radius = 200 + i * 350
        
        hue = (160 + i * 45 + t * 20) % 360
        
        # Wireframe solid combo
        py5.stroke(hue, 90, 100, 80)
        py5.stroke_weight(4)
        py5.fill((hue + 180) % 360, 80, 50, 15)
        
        if i % 2 == 0:
            draw_star_tetrahedron(radius)
        else:
            draw_icosahedron(radius)
            
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

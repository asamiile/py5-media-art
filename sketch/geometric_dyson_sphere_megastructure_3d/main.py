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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Icosahedron generation
phi = (1 + np.sqrt(5)) / 2
vertices = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
])
# Normalize
vertices /= np.linalg.norm(vertices[0])

faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

def subdivide(verts, fcs, iterations=1):
    for _ in range(iterations):
        new_faces = []
        cache = {}
        for f in fcs:
            v0, v1, v2 = f
            def get_midpoint(i1, i2):
                key = tuple(sorted([i1, i2]))
                if key in cache:
                    return cache[key]
                new_v = np.array(verts[i1]) + np.array(verts[i2])
                new_v /= np.linalg.norm(new_v)
                verts.append(new_v)
                cache[key] = len(verts) - 1
                return cache[key]
            
            a = get_midpoint(v0, v1)
            b = get_midpoint(v1, v2)
            c = get_midpoint(v2, v0)
            
            new_faces.extend([
                [v0, a, c],
                [v1, b, a],
                [v2, c, b],
                [a, b, c]
            ])
        fcs = new_faces
    return np.array(verts), fcs

# Subdivide to create geodesic panels
vertices, faces = subdivide(vertices.tolist(), faces, iterations=4)
# Calculate face centers and normals
face_centers = []
face_normals = []
for f in faces:
    pts = vertices[f]
    center = np.mean(pts, axis=0)
    normal = center / np.linalg.norm(center)
    face_centers.append(center)
    face_normals.append(normal)
    
face_centers = np.array(face_centers)
face_normals = np.array(face_normals)
    
BASE_RADIUS = 350
CORE_RADIUS = 250

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    
    # Core Glow
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Core
    py5.push_matrix()
    py5.rotate_y(-py5.frame_count * 0.01)
    py5.fill(255, 200, 100, 150)
    py5.sphere_detail(30)
    # Pulsing core
    core_pulse = CORE_RADIUS + 20 * np.sin(py5.frame_count * 0.1)
    py5.sphere(core_pulse)
    py5.pop_matrix()
    
    # Megastructure
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.blend_mode(py5.BLEND)
    
    py5.ambient_light(50, 60, 70)
    py5.directional_light(200, 220, 255, 1, 1, -1)
    py5.point_light(255, 255, 200, 0, 0, 0) # Core light illuminating inner faces
    
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    
    py5.stroke(0, 50, 100, 100)
    py5.stroke_weight(1)
    
    t = py5.frame_count * 0.01
    
    py5.begin_shape(py5.TRIANGLES)
    for i, f in enumerate(faces):
        center = face_centers[i]
        normal = face_normals[i]
        
        # Determine panel height based on noise
        # This creates the "megastructure" varied panel look
        n = py5.os_noise(center[0]*3, center[1]*3, center[2]*3 + t)
        
        # Gap logic - some panels are missing to show the core
        if py5.os_noise(center[0]*1.5, center[1]*1.5, center[2]*1.5 - t*0.5) > 0.3:
            continue
            
        panel_height = BASE_RADIUS + n * 100
        
        # Color based on height
        if n > 0.4:
            py5.fill(0, 200, 255, 255) # Cyan energy lines on tall panels
        else:
            c_val = 100 + n * 100
            py5.fill(c_val, c_val, c_val + 20) # Steel blue/grey
            
        pts = vertices[f]
        
        # We scale the vertices out by panel_height, and slightly shrink them towards center to create gaps
        for v_idx in range(3):
            v = pts[v_idx]
            v_dir = v / np.linalg.norm(v)
            # Shrink toward face center
            v_shrunk = center + (v - center) * 0.9
            v_final = v_shrunk * panel_height
            
            py5.vertex(*v_final)
            
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

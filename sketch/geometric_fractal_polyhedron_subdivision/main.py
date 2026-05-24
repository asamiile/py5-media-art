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

# Pre-calculate an Icosahedron (12 vertices, 20 faces)
phi = (1.0 + np.sqrt(5.0)) / 2.0
base_vertices = np.array([
    [-1,  phi, 0], [ 1,  phi, 0], [-1, -phi, 0], [ 1, -phi, 0],
    [0, -1,  phi], [0,  1,  phi], [0, -1, -phi], [0,  1, -phi],
    [ phi, 0, -1], [ phi, 0,  1], [-phi, 0, -1], [-phi, 0,  1]
])
# Normalize to unit sphere
base_vertices = base_vertices / np.linalg.norm(base_vertices[0])

base_faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

def subdivide(vertices, faces):
    new_faces = []
    # Using a dictionary to avoid duplicating midpoints
    midpoint_cache = {}
    
    def get_midpoint(v1_idx, v2_idx):
        key = tuple(sorted([v1_idx, v2_idx]))
        if key in midpoint_cache:
            return midpoint_cache[key]
        
        v1 = vertices[v1_idx]
        v2 = vertices[v2_idx]
        mid = (v1 + v2) / 2.0
        # Project back to unit sphere
        mid = mid / np.linalg.norm(mid)
        
        vertices.append(mid)
        mid_idx = len(vertices) - 1
        midpoint_cache[key] = mid_idx
        return mid_idx

    for face in faces:
        v1, v2, v3 = face
        a = get_midpoint(v1, v2)
        b = get_midpoint(v2, v3)
        c = get_midpoint(v3, v1)
        
        new_faces.append([v1, a, c])
        new_faces.append([v2, b, a])
        new_faces.append([v3, c, b])
        new_faces.append([a, b, c])
        
    return vertices, new_faces

# Pre-subdivide to level 4
mesh_vertices = list(base_vertices)
mesh_faces = base_faces
for _ in range(4):
    mesh_vertices, mesh_faces = subdivide(mesh_vertices, mesh_faces)

mesh_vertices = np.array(mesh_vertices)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.3)
    py5.rotate_z(py5.sin(t * 0.2) * 0.5)
    
    # Base scale of the polyhedron
    scale = 350.0
    
    py5.stroke_weight(1.0)
    
    # To make it "breathe", we displace vertices along their normal (which is the vertex itself for a unit sphere)
    # We use a 3D sine wave interference pattern for the displacement.
    
    py5.begin_shape(py5.TRIANGLES)
    for face in mesh_faces:
        v1, v2, v3 = face
        
        pts = []
        for v_idx in [v1, v2, v3]:
            v = mesh_vertices[v_idx]
            
            # 3D spatial sine wave
            displacement = py5.sin(v[0]*5 + t) * py5.cos(v[1]*5 + t) * py5.sin(v[2]*5 - t)
            
            # The pulse strength also changes over time
            pulse = py5.remap(py5.sin(t * 0.5), -1, 1, 0, 150)
            
            r = scale + displacement * pulse
            
            px, py, pz = v * r
            pts.append((px, py, pz))
            
        # Face normal for lighting/coloring (approximate via cross product)
        p1 = np.array(pts[0])
        p2 = np.array(pts[1])
        p3 = np.array(pts[2])
        normal = np.cross(p2 - p1, p3 - p1)
        normal_len = np.linalg.norm(normal)
        if normal_len > 0:
            normal = normal / normal_len
        else:
            normal = np.array([0, 0, 1])
            
        # Color based on normal direction and time
        hue = (180 + normal[0] * 60 + normal[1] * 60 + t * 30) % 360
        brightness = py5.remap(normal[2], -1, 1, 20, 100)
        
        # Transparent, glass-like faces with glowing edges
        py5.fill(hue, 80, brightness, 40)
        py5.stroke(hue, 100, 100, 80)
        
        py5.vertex(*pts[0])
        py5.vertex(*pts[1])
        py5.vertex(*pts[2])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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

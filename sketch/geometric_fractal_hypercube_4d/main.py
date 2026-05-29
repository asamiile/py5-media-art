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
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global vertices, edges
    vertices = []
    for i in [-1, 1]:
        for j in [-1, 1]:
            for k in [-1, 1]:
                for l in [-1, 1]:
                    vertices.append([i, j, k, l])
    vertices = np.array(vertices, dtype=float)
    
    edges = []
    for i in range(16):
        for j in range(i+1, 16):
            diff = np.sum(np.abs(vertices[i] - vertices[j]))
            if np.isclose(diff, 2.0):
                edges.append((i, j))

def mat_rotate_xy(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0, 0],
        [np.sin(theta),  np.cos(theta), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

def mat_rotate_zw(theta):
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, np.cos(theta), -np.sin(theta)],
        [0, 0, np.sin(theta),  np.cos(theta)]
    ])
    
def mat_rotate_xw(theta):
    return np.array([
        [np.cos(theta), 0, 0, -np.sin(theta)],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [np.sin(theta), 0, 0,  np.cos(theta)]
    ])

def draw():
    # Motion blur using semi-transparent background
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.02
    
    # Apply 4D rotations
    rotated = vertices.copy()
    r_xy = mat_rotate_xy(t * 0.5)
    r_zw = mat_rotate_zw(t * 0.8)
    r_xw = mat_rotate_xw(t * 0.3)
    
    for i in range(len(rotated)):
        rotated[i] = r_xy.dot(rotated[i])
        rotated[i] = r_zw.dot(rotated[i])
        rotated[i] = r_xw.dot(rotated[i])
    
    # Project 4D to 3D
    w_distance = 3.0
    projected_3d = []
    for v in rotated:
        w = 1.0 / (w_distance - v[3])
        proj_matrix = np.array([
            [w, 0, 0, 0],
            [0, w, 0, 0],
            [0, 0, w, 0]
        ])
        p3d = proj_matrix.dot(v)
        projected_3d.append(p3d)
    
    projected_3d = np.array(projected_3d) * 400
    
    # Slowly rotate the 3D projection
    py5.rotate_y(t * 0.4)
    py5.rotate_x(t * 0.2)
    
    # Draw edges
    py5.stroke_weight(3)
    py5.no_fill()
    for edge in edges:
        p1 = projected_3d[edge[0]]
        p2 = projected_3d[edge[1]]
        
        dist = np.linalg.norm(p1 - p2)
        hue = (180 + t * 40 + dist * 0.5) % 360
        py5.stroke(hue, 90, 100, 60)
        
        py5.begin_shape(py5.LINES)
        py5.vertex(*p1)
        py5.vertex(*p2)
        py5.end_shape()

    # Draw vertices
    py5.stroke_weight(12)
    for p in projected_3d:
        hue = (200 + t * 40 + p[2] * 0.2) % 360
        py5.stroke(hue, 90, 100, 80)
        py5.point(*p)

    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

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

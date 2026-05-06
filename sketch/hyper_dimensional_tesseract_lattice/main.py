from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
STAR_COUNT = 3000

def get_tesseract():
    # 16 vertices
    verts = []
    for i in range(16):
        verts.append([
            1 if (i & 1) else -1,
            1 if (i & 2) else -1,
            1 if (i & 4) else -1,
            1 if (i & 8) else -1
        ])
    verts = np.array(verts, dtype=float)
    
    # 32 edges (connect verts with Hamming distance 1)
    edges = []
    for i in range(16):
        for j in range(i + 1, 16):
            if bin(i ^ j).count('1') == 1:
                edges.append((i, j))
    return verts, edges

def rotate4d(v, angle, plane='xw'):
    c, s = np.cos(angle), np.sin(angle)
    m = np.eye(4)
    if plane == 'xw':
        m[0, 0], m[0, 3], m[3, 0], m[3, 3] = c, -s, s, c
    elif plane == 'yw':
        m[1, 1], m[1, 3], m[3, 1], m[3, 3] = c, -s, s, c
    elif plane == 'zw':
        m[2, 2], m[2, 3], m[3, 2], m[3, 3] = c, -s, s, c
    elif plane == 'xy':
        m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return v @ m.T

def project4d(v, dist=4):
    # 4D perspective projection
    w = 1.0 / (dist - v[:, 3])
    p = v[:, :3] * w[:, np.newaxis]
    return p * 200 # scale

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global v_base, edges, stars
    v_base, edges = get_tesseract()
    
    # Create a lattice of 4D vertices
    lattice_v = []
    for i in [-2, 0, 2]:
        for j in [-2, 0, 2]:
            for k in [-2, 0, 2]:
                lattice_v.append(v_base + np.array([i*2, j*2, k*2, 0]))
    v_base = np.vstack(lattice_v)
    
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    py5.background(0, 0, 15)
    
    time_val = py5.frame_count / 60.0
    
    # 4D Rotation
    v = v_base.copy()
    v = rotate4d(v, time_val * 0.5, 'xw')
    v = rotate4d(v, time_val * 0.3, 'yw')
    v = rotate4d(v, time_val * 0.2, 'zw')
    
    # 3D Projection
    p = project4d(v, dist=10)
    
    # Camera
    cam_dist = 1200 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               cam_dist * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Hyper-dimensional Lattice
    py5.blend_mode(py5.ADD)
    
    # Each tesseract has 16 vertices, we have 27 tesseracts
    for t_idx in range(27):
        offset = t_idx * 16
        t_p = p[offset : offset + 16]
        t_v = v[offset : offset + 16]
        
        # Draw edges
        for i, j in edges:
            # Color and alpha based on W coordinate (depth in 4D)
            avg_w = (t_v[i, 3] + t_v[j, 3]) / 2
            alpha = py5.remap(avg_w, -2, 2, 40, 200)
            
            if t_idx % 2 == 0:
                py5.stroke(0, 255, 255, alpha) # Cyan
            else:
                py5.stroke(255, 0, 255, alpha) # Magenta
                
            py5.stroke_weight(1)
            py5.line(*t_p[i], *t_p[j])
            
        # Draw vertices
        py5.stroke(255, 255, 255, 150)
        py5.stroke_weight(2)
        py5.points(t_p)
            
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "10M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()

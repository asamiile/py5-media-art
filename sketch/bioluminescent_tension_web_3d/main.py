from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import cKDTree

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
    
    global nodes, edges
    num_nodes = 800
    radius = min(SIZE) * 0.4
    
    # Random spherical distribution
    phi = np.random.uniform(0, 2 * np.pi, num_nodes)
    costheta = np.random.uniform(-1, 1, num_nodes)
    u = np.random.uniform(0, 1, num_nodes)
    theta = np.arccos(costheta)
    r = radius * np.cbrt(u)
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    nodes = np.vstack((x, y, z)).T
    
    # Find edges using KDTree
    tree = cKDTree(nodes)
    pairs = tree.query_pairs(r=radius * 0.25)
    edges = np.array(list(pairs))

def draw():
    py5.background(15, 100, 10) # Dark midnight blue background
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    t = py5.frame_count * 0.01
    
    # Camera rotation
    py5.rotate_y(t)
    py5.rotate_x(np.sin(t * 0.5) * 0.5)
    
    # Perturb nodes with noise
    perturbed_nodes = np.zeros_like(nodes)
    for i in range(len(nodes)):
        nx = py5.os_noise(nodes[i,0]*0.005, nodes[i,1]*0.005, t) - 0.5
        ny = py5.os_noise(nodes[i,1]*0.005, nodes[i,2]*0.005, t) - 0.5
        nz = py5.os_noise(nodes[i,2]*0.005, nodes[i,0]*0.005, t) - 0.5
        
        displacement = 200 * np.array([nx, ny, nz])
        perturbed_nodes[i] = nodes[i] + displacement

    py5.stroke_weight(2)
    py5.no_fill()
    py5.blend_mode(py5.ADD)
    
    py5.begin_shape(py5.LINES)
    for i, j in edges:
        p1 = perturbed_nodes[i]
        p2 = perturbed_nodes[j]
        
        # Distance determines color and opacity
        dist = np.linalg.norm(p1 - p2)
        hue = (200 + dist * 0.5) % 360 # Blues, cyans, to purples
        opacity = max(0, 80 - dist * 0.2)
        
        py5.stroke(hue, 80, 100, opacity)
        py5.vertex(*p1)
        py5.vertex(*p2)
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

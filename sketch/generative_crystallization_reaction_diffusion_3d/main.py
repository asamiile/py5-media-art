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

# We will approximate crystallization with 3D fractal branching (Diffusion-Limited Aggregation style)
points = []
tree = []

max_tree_size = 4000
growth_radius = 20.0
bounding_radius = 800.0

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Root of the crystal
    tree.append(np.array([0.0, 0.0, 0.0]))
    py5.no_stroke()

def get_random_point():
    ang1 = py5.random(py5.TWO_PI)
    ang2 = py5.random(py5.TWO_PI)
    r = py5.random(bounding_radius * 0.5, bounding_radius)
    x = r * py5.sin(ang1) * py5.cos(ang2)
    y = r * py5.sin(ang1) * py5.sin(ang2)
    z = r * py5.cos(ang1)
    return np.array([x, y, z])

def draw():
    py5.background(10, 5, 20)
    
    py5.translate(py5.width/2, py5.height/2, -500)
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.frame_count * 0.005)
    
    # Grow the crystal (add points to tree)
    pts_to_add = int(py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 5, 30))
    for _ in range(pts_to_add):
        if len(tree) >= max_tree_size:
            break
            
        p = get_random_point()
        
        # Simulate DLA random walk but faster: just step towards origin until close to tree
        for step in range(200):
            # Find closest tree node
            dists = np.linalg.norm(np.array(tree) - p, axis=1)
            min_idx = np.argmin(dists)
            min_dist = dists[min_idx]
            
            if min_dist < growth_radius:
                tree.append(p)
                break
                
            # Move towards closest node or origin
            closest = tree[min_idx]
            dir_vec = closest - p
            dir_vec = dir_vec / np.linalg.norm(dir_vec)
            p += dir_vec * (growth_radius * 0.8)
            
            # add noise to walk
            p += np.array([py5.random(-5, 5), py5.random(-5, 5), py5.random(-5, 5)])

    # Draw tree
    py5.blend_mode(py5.ADD)
    for i, p in enumerate(tree):
        hue = (280 + i * 0.05) % 360 # Purple/Magenta
        
        py5.push_matrix()
        py5.translate(p[0], p[1], p[2])
        
        py5.fill(hue, 80, 100, 80)
        py5.box(growth_radius * 0.6)
        
        # Glow
        py5.fill(hue, 90, 80, 15)
        py5.box(growth_radius * 2.0)
        
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} | Tree size: {len(tree)}")

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

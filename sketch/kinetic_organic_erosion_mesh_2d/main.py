from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
from scipy.spatial import Delaunay

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

pts = None
vels = None
edges = None
edge_break_times = None
broken_edges = None
dust_mode = None

def setup():
    global pts, vels, edges, edge_break_times, broken_edges, dust_mode
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    n_points = 2000
    pts = np.random.rand(n_points, 2) * np.array([SIZE[0], SIZE[1]])
    vels = np.zeros_like(pts)
    dust_mode = np.zeros(n_points, dtype=bool)
    
    tri = Delaunay(pts)
    edges_set = set()
    for simplex in tri.simplices:
        for i in range(3):
            edge = tuple(sorted((simplex[i], simplex[(i+1)%3])))
            edges_set.add(edge)
            
    edges = np.array(list(edges_set))
    n_edges = len(edges)
    broken_edges = np.zeros(n_edges, dtype=bool)
    
    edge_break_times = np.zeros(n_edges)
    for i, e in enumerate(edges):
        p1, p2 = pts[e[0]], pts[e[1]]
        mid = (p1 + p2) / 2
        noise_val = py5.os_noise(mid[0]*0.002, mid[1]*0.002, 0)
        base_time = py5.remap(mid[1], SIZE[1], 0, 0, TOTAL_FRAMES)
        edge_break_times[i] = base_time + noise_val * 400 - 100
        
def draw():
    global pts, vels, edges, broken_edges, dust_mode
    
    py5.background(15, 15, 18, 50)
    
    curr_frame = py5.frame_count
    new_broken = (edge_break_times < curr_frame) & ~broken_edges
    broken_edges[new_broken] = True
    
    connected_nodes = np.unique(edges[~broken_edges])
    dust_mode[:] = True
    dust_mode[connected_nodes] = False
    
    py5.stroke(180, 100, 60, 160)
    py5.stroke_weight(1.5)
    
    py5.begin_shape(py5.LINES)
    active_edges = edges[~broken_edges]
    for e in active_edges:
        p1 = pts[e[0]]
        p2 = pts[e[1]]
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
    py5.end_shape()
    
    py5.no_stroke()
    dust_idx = np.where(dust_mode)[0]
    
    for idx in dust_idx:
        p = pts[idx]
        v = vels[idx]
        
        n_ang = py5.os_noise(p[0]*0.005, p[1]*0.005, curr_frame*0.01) * py5.TWO_PI * 2
        v[0] += np.cos(n_ang) * 0.1
        v[1] += np.sin(n_ang) * 0.1 + 0.05
        
        speed = np.linalg.norm(v)
        if speed > 3:
            v = (v / speed) * 3
            
        pts[idx] += v
        vels[idx] = v
        
    py5.fill(200, 200, 210, 200)
    for idx in dust_idx:
        p = pts[idx]
        if random.random() < 0.02:
            py5.fill(255, 120, 60, 255)
            py5.circle(p[0], p[1], 4)
            py5.fill(200, 200, 210, 200)
        else:
            py5.circle(p[0], p[1], 2)
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
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

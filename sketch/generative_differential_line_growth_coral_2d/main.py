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

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Differential Line Growth Constants
R = 40.0
MAX_EDGE = 15.0
REPULSION_STRENGTH = 0.2
ATTRACTION_STRENGTH = 0.4
MAX_NODES = 4500

pts = None

def setup():
    global pts
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(5, 8, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize a jagged circle to encourage early folding
    N_init = 60
    theta = np.linspace(0, py5.TWO_PI, N_init, endpoint=False)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    radii = 100 + np.random.randn(N_init) * 15
    
    pts = np.column_stack((np.cos(theta) * radii + cx, np.sin(theta) * radii + cy))

def update_physics():
    global pts
    N = len(pts)
    
    # 1. Repulsion
    # cdist using numpy broadcasting
    # To save memory, if N is huge we could process in chunks, but for N=4500, it's 4500x4500x2 float64 = 324MB.
    # To be extremely safe with memory on smaller machines, we can use float32.
    pts_f32 = pts.astype(np.float32)
    
    dx = pts_f32[:, 0:1] - pts_f32[:, 0:1].T
    dy = pts_f32[:, 1:2] - pts_f32[:, 1:2].T
    dist2 = dx**2 + dy**2
    
    mask = (dist2 > 0) & (dist2 < R**2)
    dist = np.sqrt(dist2)
    # prevent div by zero
    dist[dist == 0] = 1.0 
    
    # Repulsion force magnitude
    f = (R - dist) / dist
    fx = dx * f * mask
    fy = dy * f * mask
    
    repulsion = np.column_stack((np.sum(fx, axis=1), np.sum(fy, axis=1))) * REPULSION_STRENGTH
    
    # 2. Attraction (Spring) to immediate neighbors
    left = np.roll(pts, 1, axis=0)
    right = np.roll(pts, -1, axis=0)
    
    attraction = ((left - pts) + (right - pts)) * ATTRACTION_STRENGTH
    
    # Update positions
    pts += repulsion + attraction
    
    # Brownian motion
    pts += np.random.randn(*pts.shape) * 0.2
    
    # 3. Growth
    if N < MAX_NODES:
        d_next = np.linalg.norm(right - pts, axis=1)
        
        # We can vectorize the rebuild or use a list comprehension
        # Doing it in python list is actually very fast for N=4500
        new_pts = []
        for i in range(N):
            new_pts.append(pts[i])
            if d_next[i] > MAX_EDGE:
                mid = (pts[i] + right[i]) / 2.0
                new_pts.append(mid)
        
        pts = np.array(new_pts)

def draw():
    # Subtle fade for motion trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 8, 15, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    # Physics updates (run a few steps per frame for faster growth)
    for _ in range(3):
        update_physics()
    
    # Draw the line
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    t = py5.frame_count * 0.01
    
    py5.begin_shape()
    for i, p in enumerate(pts):
        # Color based on node index and time
        # Bioluminescent coral colors (Neon pink, warm orange, seafoam green)
        n_ratio = i / len(pts)
        
        r = py5.remap(np.sin(n_ratio * py5.TWO_PI * 3 + t), -1, 1, 50, 255)
        g = py5.remap(np.sin(n_ratio * py5.TWO_PI * 5 - t * 1.5), -1, 1, 100, 255)
        b = py5.remap(np.cos(n_ratio * py5.TWO_PI * 2 + t * 0.5), -1, 1, 150, 255)
        
        py5.stroke(r, g, b, 200)
        py5.vertex(p[0], p[1])
    py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} (Nodes: {len(pts)}) ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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

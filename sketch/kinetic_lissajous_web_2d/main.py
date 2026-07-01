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
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_NODES = 800
MAX_DIST = 300.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global A, B, a, b, d
    # A and B are amplitudes
    A = py5.width * 0.4
    B = py5.height * 0.4
    
    # Frequencies
    a = np.random.uniform(1.0, 5.0, NUM_NODES)
    b = np.random.uniform(1.0, 5.0, NUM_NODES)
    
    # Phase shifts
    d = np.linspace(0, py5.PI * 2, NUM_NODES)

def draw():
    # Fade background slightly to create light trails
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 15, 60)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / float(FPS) * 0.5  # Slow down time
    
    # Compute Lissajous positions
    cx = py5.width / 2
    cy = py5.height / 2
    
    X = cx + A * np.sin(a * t + d)
    Y = cy + B * np.sin(b * t)
    
    # Compute distances between all pairs
    # X[:, None] - X[None, :] creates a NUM_NODES x NUM_NODES matrix
    dx = X[:, None] - X[None, :]
    dy = Y[:, None] - Y[None, :]
    dist_sq = dx**2 + dy**2
    
    # Find pairs that are close enough
    # We only look at upper triangle to avoid duplicates and self-connections
    mask = (dist_sq < MAX_DIST**2) & np.triu(np.ones((NUM_NODES, NUM_NODES), dtype=bool), k=1)
    
    i_idx, j_idx = np.where(mask)
    
    if len(i_idx) > 0:
        # Get coordinates of connected pairs
        p1_x = X[i_idx]
        p1_y = Y[i_idx]
        p2_x = X[j_idx]
        p2_y = Y[j_idx]
        
        # Interleave to create line segments: p1, p2, p1, p2...
        lines_x = np.empty(len(p1_x) * 2, dtype=np.float32)
        lines_x[0::2] = p1_x
        lines_x[1::2] = p2_x
        
        lines_y = np.empty(len(p1_y) * 2, dtype=np.float32)
        lines_y[0::2] = p1_y
        lines_y[1::2] = p2_y
        
        points = np.column_stack((lines_x, lines_y))
        
        # Draw lines in a few opacity buckets to simulate varying intensity based on distance
        # But for absolute speed in py5 Python, we'll draw them all with one color
        # The density of overlapping lines creates the bright nodes naturally
        
        py5.stroke(0, 200, 255, 15)
        py5.stroke_weight(2)
        py5.no_fill()
        
        py5.begin_shape(py5.LINES)
        py5.vertices(points)
        py5.end_shape()
        
    # Draw the nodes themselves
    py5.fill(255, 50, 150, 200)
    py5.no_stroke()
    
    # To draw all circles quickly, we can't use a loop if it's too slow, but 800 circles is fast enough
    for i in range(NUM_NODES):
        py5.circle(X[i], Y[i], 4)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
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

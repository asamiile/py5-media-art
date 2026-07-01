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

NUM_POINTS = 500000
NUM_VERTICES = 5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global points, cx, cy
    cx, cy = py5.width / 2, py5.height / 2
    
    # Initialize points clustered in the center
    points = np.random.normal(loc=[cx, cy], scale=100, size=(NUM_POINTS, 2))

def draw():
    global points
    
    # Darken background slightly to leave trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Animate the parameters
    t = py5.frame_count / TOTAL_FRAMES
    
    # Vertices rotate over time
    angle_offset = t * py5.PI * 2
    angles = np.linspace(0, py5.PI * 2, NUM_VERTICES, endpoint=False) + angle_offset
    radius = 800 + np.sin(t * py5.PI * 4) * 200
    
    vertices = np.column_stack((
        cx + np.cos(angles) * radius,
        cy + np.sin(angles) * radius
    ))
    
    # Jump factor oscillates
    jump_factor = 0.5 + np.sin(t * py5.PI * 2) * 0.15
    
    # Vectorized Chaos Game steps
    # We do a few steps per frame so the fractal structure forms instantly
    STEPS = 5
    for _ in range(STEPS):
        target_indices = np.random.randint(0, NUM_VERTICES, NUM_POINTS)
        targets = vertices[target_indices]
        points = points + (targets - points) * jump_factor
        
    # Draw points
    # We can split them by their last target index to color them
    colors = [
        (255, 50, 50, 10),
        (50, 255, 50, 10),
        (50, 50, 255, 10),
        (255, 255, 50, 10),
        (50, 255, 255, 10)
    ]
    
    py5.stroke_weight(1)
    for i in range(NUM_VERTICES):
        mask = (target_indices == i)
        cluster = points[mask]
        if len(cluster) > 0:
            py5.stroke(*colors[i])
            py5.points(cluster)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} (Time: {t:.2f})")

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

from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(10, 15)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 15000
positions = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
hues = np.zeros(NUM_PARTICLES, dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    py5.background(0)

    # Initialize
    positions[:, 0] = np.random.uniform(0, py5.width, NUM_PARTICLES)
    positions[:, 1] = np.random.uniform(0, py5.height, NUM_PARTICLES)
    hues[:] = np.random.uniform(0, 360, NUM_PARTICLES)

def draw():
    # Keep trails by drawing a low opacity black rectangle instead of clear
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    # We'll use simple math for a flow field to avoid slow os_noise calls
    # Vectorized flow field
    x = positions[:, 0]
    y = positions[:, 1]
    
    # Simple complex trigonometric flow field
    angle = np.sin(x * 0.005 + t) * np.cos(y * 0.005 + t) * np.pi * 2
    angle += np.sin(y * 0.002 - t) * np.pi
    
    speed = 3.0
    positions[:, 0] += np.cos(angle) * speed
    positions[:, 1] += np.sin(angle) * speed
    
    # Wrap around
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Slowly shift hues
    hues[:] = (hues[:] + 0.5) % 360
    
    # Render using points (very fast)
    py5.stroke_weight(2)
    
    # Since py5.points() expects a 2D array, we can draw them all at once!
    # Wait, py5.points() only takes coordinates, not colors per point easily.
    # We will do a vectorized approach using py5.points, but with a single color.
    # To use multiple colors, we'd have to use py5.begin_shape(py5.POINTS), which is still a loop.
    # Let's loop in Python, it's 15k points, might be ~10ms.
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.stroke(hues[i], 80, 100, 40)
        py5.vertex(positions[i, 0], positions[i, 1])
    py5.end_shape()
    py5.no_stroke()

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

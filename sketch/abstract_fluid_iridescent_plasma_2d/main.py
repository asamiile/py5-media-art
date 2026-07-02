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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 8000
positions = None
velocities = None
lifetimes = None

def setup():
    global positions, velocities, lifetimes
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(10)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.rand(NUM_PARTICLES, 2) * np.array([py5.width, py5.height])
    velocities = np.zeros((NUM_PARTICLES, 2))
    lifetimes = np.random.rand(NUM_PARTICLES) * 100

def get_flow(pts, t):
    scale1 = 0.002
    scale2 = 0.005
    angles1 = py5.os_noise(pts[:, 0] * scale1, pts[:, 1] * scale1, t * 0.5) * py5.TWO_PI * 4
    angles2 = py5.os_noise(pts[:, 0] * scale2, pts[:, 1] * scale2, t * 0.2 + 100) * py5.TWO_PI * 2
    
    final_angles = angles1 + angles2
    u = np.cos(final_angles)
    v = np.sin(final_angles)
    return np.column_stack((u, v))

def draw():
    global positions, velocities, lifetimes
    
    py5.fill(10, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    flow = get_flow(positions, t)
    
    velocities = velocities * 0.95 + flow * 0.6
    
    new_positions = positions + velocities
    
    lifetimes -= 1
    
    out_of_bounds = (
        (new_positions[:, 0] < 0) | (new_positions[:, 0] > py5.width) |
        (new_positions[:, 1] < 0) | (new_positions[:, 1] > py5.height) |
        (lifetimes <= 0)
    )
    
    if np.any(out_of_bounds):
        count = np.sum(out_of_bounds)
        new_positions[out_of_bounds] = np.random.rand(count, 2) * np.array([py5.width, py5.height])
        velocities[out_of_bounds] = 0
        lifetimes[out_of_bounds] = np.random.rand(count) * 100 + 50
    
    speeds = np.linalg.norm(velocities, axis=1)
    hues = (speeds * 40 + py5.frame_count * 0.5) % 360
    
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PARTICLES):
        py5.stroke(hues[i], 80, 100, 100)
        py5.vertex(new_positions[i, 0], new_positions[i, 1])
    py5.end_shape()
    
    positions = new_positions
    
    py5.blend_mode(py5.BLEND)

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

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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Simulation parameters
NUM_NODES = 800
nodes_pos = None
nodes_vel = None
nodes_target = None
connections = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes_pos, nodes_vel, nodes_target, connections
    nodes_pos = np.random.rand(NUM_NODES, 2) * np.array([SIZE[0], SIZE[1]])
    nodes_vel = (np.random.rand(NUM_NODES, 2) - 0.5) * 2.0
    nodes_target = np.copy(nodes_pos)
    connections = []

def draw():
    global nodes_pos, nodes_vel
    
    # Semi-transparent background for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 20, 20)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Update positions
    time_val = py5.frame_count * 0.02
    
    # Simple flocking / wander
    noise_angles = np.array([py5.os_noise(p[0]*0.002, p[1]*0.002, time_val) for p in nodes_pos]) * py5.TWO_PI * 4
    nodes_vel[:, 0] += np.cos(noise_angles) * 0.1
    nodes_vel[:, 1] += np.sin(noise_angles) * 0.1
    nodes_vel *= 0.95 # friction
    nodes_pos += nodes_vel
    
    # Wrap around
    nodes_pos[:, 0] %= SIZE[0]
    nodes_pos[:, 1] %= SIZE[1]
    
    # Draw nodes
    py5.no_stroke()
    for i in range(NUM_NODES):
        py5.fill(0, 200, 255, 100)
        py5.circle(nodes_pos[i, 0], nodes_pos[i, 1], 4)
        
    # Connections
    py5.stroke(0, 255, 150, 40)
    py5.stroke_weight(1.5)
    
    # Naive distance check for a subset to stay fast
    # We only check connections for a random subset of nodes per frame to keep FPS high
    subset = np.random.choice(NUM_NODES, min(NUM_NODES, 300), replace=False)
    for i in subset:
        dists = np.sum((nodes_pos - nodes_pos[i])**2, axis=1)
        # Find neighbors within radius squared
        neighbors = np.where((dists > 0) & (dists < 15000))[0]
        for j in neighbors:
            # Draw line
            d = dists[j]
            alpha = max(0, 100 - (d / 150))
            py5.stroke(50, 255, 200, alpha)
            py5.line(nodes_pos[i, 0], nodes_pos[i, 1], nodes_pos[j, 0], nodes_pos[j, 1])
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

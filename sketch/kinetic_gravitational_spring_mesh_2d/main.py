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
from lib.preview import preview_filename
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

# Mesh parameters
GRID_W = 60
GRID_H = 40
SPACING = SIZE[0] / GRID_W
NUM_NODES = GRID_W * GRID_H

nodes_pos = np.zeros((NUM_NODES, 2))
nodes_vel = np.zeros((NUM_NODES, 2))
nodes_base = np.zeros((NUM_NODES, 2))

# Connections (springs)
edges = []

def get_idx(r, c):
    return r * GRID_W + c

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize nodes
    for r in range(GRID_H):
        for c in range(GRID_W):
            idx = get_idx(r, c)
            x = c * SPACING + SPACING / 2
            y = r * SPACING + (SIZE[1] - GRID_H * SPACING) / 2
            nodes_pos[idx] = [x, y]
            nodes_base[idx] = [x, y]
            
            # Connect to right and down
            if c < GRID_W - 1:
                edges.append([idx, get_idx(r, c+1)])
            if r < GRID_H - 1:
                edges.append([idx, get_idx(r+1, c)])
            if r < GRID_H - 1 and c < GRID_W - 1:
                edges.append([idx, get_idx(r+1, c+1)])
                
    py5.stroke_weight(2)

def draw():
    py5.background(5, 10, 25)
    
    t = py5.frame_count / 60.0
    
    # Gravitational attractors
    attractor1 = np.array([SIZE[0]/2 + np.sin(t * 0.5) * 600, SIZE[1]/2 + np.cos(t * 0.7) * 400])
    attractor2 = np.array([SIZE[0]/2 + np.cos(t * 0.8) * 700, SIZE[1]/2 + np.sin(t * 0.4) * 300])
    
    # Physics update
    for i in range(NUM_NODES):
        # Base spring force
        force = (nodes_base[i] - nodes_pos[i]) * 0.05
        
        # Attractor 1 force
        d1 = attractor1 - nodes_pos[i]
        dist1 = np.linalg.norm(d1)
        if dist1 > 10:
            force += (d1 / dist1) * (15000 / (dist1 * dist1))
            
        # Attractor 2 force
        d2 = attractor2 - nodes_pos[i]
        dist2 = np.linalg.norm(d2)
        if dist2 > 10:
            force += (d2 / dist2) * (15000 / (dist2 * dist2))
            
        nodes_vel[i] = (nodes_vel[i] + force) * 0.85 # Damping
        nodes_pos[i] += nodes_vel[i]

    # Draw edges
    py5.stroke(100, 200, 255, 80)
    for e in edges:
        p1 = nodes_pos[e[0]]
        p2 = nodes_pos[e[1]]
        dist = np.linalg.norm(p1 - p2)
        if dist < 250: # Only draw if not stretched too far
            # Color based on stretch
            stretch = dist / SPACING
            py5.stroke(100 + stretch*50, 255 - stretch*50, 255, 150 - stretch*20)
            py5.line(p1[0], p1[1], p2[0], p2[1])

    # Draw attractors
    py5.no_stroke()
    py5.fill(255, 100, 100, 200)
    py5.circle(attractor1[0], attractor1[1], 20)
    py5.fill(100, 255, 100, 200)
    py5.circle(attractor2[0], attractor2[1], 20)

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

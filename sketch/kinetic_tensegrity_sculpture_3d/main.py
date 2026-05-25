from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_NODES = 24
nodes = None
velocities = None

struts = []
cables = []

def setup():
    global nodes, velocities, struts, cables
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize nodes randomly on a sphere
    nodes = np.random.randn(NUM_NODES, 3)
    norms = np.linalg.norm(nodes, axis=1, keepdims=True)
    nodes = (nodes / norms) * (SIZE[1] * 0.25)
    velocities = np.zeros_like(nodes)
    
    # Generate connections
    for i in range(NUM_NODES):
        distances = np.linalg.norm(nodes - nodes[i], axis=1)
        sorted_indices = np.argsort(distances)
        # connect nearest neighbors as struts
        for j in sorted_indices[1:3]:
            if i < j:
                struts.append((i, j, distances[j]))
        # further away as cables
        for j in sorted_indices[3:8]:
            if i < j:
                cables.append((i, j, distances[j]))

def draw():
    global nodes, velocities
    
    py5.background(10, 15, 25)
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count / TOTAL_FRAMES
    rot_y = t * py5.TWO_PI
    rot_x = py5.sin(t * py5.TWO_PI) * 0.5
    py5.rotate_y(rot_y)
    py5.rotate_x(rot_x)
    
    forces = np.zeros_like(nodes)
    
    # Struts (repel to original length)
    for i, j, length in struts:
        dir_vec = nodes[j] - nodes[i]
        dist = np.linalg.norm(dir_vec)
        if dist > 0:
            dir_norm = dir_vec / dist
            diff = dist - length
            f = dir_norm * diff * 0.1
            forces[i] += f
            forces[j] -= f
            
    # Cables (pull to dynamic length)
    for i, j, length in cables:
        noise_val = py5.os_noise(i * 0.1, j * 0.1, t * 5.0) - 0.5
        dynamic_length = length * (1.0 + noise_val * 0.9)
        dir_vec = nodes[j] - nodes[i]
        dist = np.linalg.norm(dir_vec)
        if dist > 0:
            dir_norm = dir_vec / dist
            diff = dist - dynamic_length
            f = dir_norm * diff * 0.02
            forces[i] += f
            forces[j] -= f
            
    # Gravity to center (soft tether)
    forces -= nodes * 0.005
    
    # Update physics
    velocities += forces
    velocities *= 0.9 # damping
    nodes += velocities
    
    # Draw Cables
    py5.stroke_weight(1.5)
    py5.blend_mode(py5.ADD)
    for i, j, _ in cables:
        dist = np.linalg.norm(nodes[i] - nodes[j])
        tension = min(dist / (SIZE[1] * 0.5), 1.0)
        c = py5.color(255 * (1 - tension), 100, 255 * tension, 180)
        py5.stroke(c)
        py5.line(nodes[i][0], nodes[i][1], nodes[i][2], nodes[j][0], nodes[j][1], nodes[j][2])
        
    py5.blend_mode(py5.BLEND)
    
    # Draw Struts
    py5.stroke_weight(4)
    py5.stroke(200, 255, 255)
    for i, j, _ in struts:
        py5.line(nodes[i][0], nodes[i][1], nodes[i][2], nodes[j][0], nodes[j][1], nodes[j][2])
        
    # Draw Nodes
    py5.no_stroke()
    py5.fill(255, 255, 255)
    for node in nodes:
        py5.push_matrix()
        py5.translate(node[0], node[1], node[2])
        py5.box(6)
        py5.pop_matrix()
        
    py5.pop_matrix()

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

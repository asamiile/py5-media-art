from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import random

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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes, edges, pulses
    num_nodes = 250
    nodes = []
    
    # Generate nodes in a sphere
    for _ in range(num_nodes):
        r = py5.random(0, 1000)
        theta = py5.random(0, py5.TWO_PI)
        phi = py5.random(0, py5.PI)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        
        # Node structure: pos, base_hue, phase
        nodes.append([np.array([x, y, z]), py5.random(180, 260), py5.random(py5.TWO_PI)])
        
    edges = []
    connection_dist = 250
    
    for i in range(num_nodes):
        for j in range(i+1, num_nodes):
            dist = np.linalg.norm(nodes[i][0] - nodes[j][0])
            if dist < connection_dist:
                edges.append((i, j, dist))
                
    # Pulses traverse edges
    num_pulses = 100
    pulses = []
    for _ in range(num_pulses):
        edge_idx = random.randint(0, len(edges)-1)
        direction = 1 if random.random() > 0.5 else -1
        progress = random.random()
        speed = random.uniform(0.01, 0.03)
        pulses.append([edge_idx, progress, direction, speed])

def draw():
    # Background
    py5.blend_mode(py5.BLEND)
    py5.background(220, 100, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera movement
    py5.rotate_y(t * 0.3)
    py5.rotate_x(np.sin(t * 0.5) * 0.2)
    py5.translate(np.sin(t * 0.2) * 200, 0, np.cos(t * 0.1) * 300)
    
    # Draw edges
    py5.stroke_weight(2)
    py5.no_fill()
    for (i, j, dist) in edges:
        p1 = nodes[i][0]
        p2 = nodes[j][0]
        
        # Wavy edge using perlin noise
        noise_val = py5.os_noise(i * 0.1, j * 0.1, t)
        alpha = py5.remap(dist, 0, 250, 60, 0) * (0.5 + noise_val * 0.5)
        
        py5.stroke(220, 80, 100, alpha)
        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
        
    # Draw pulses
    py5.no_stroke()
    for idx, pulse in enumerate(pulses):
        edge_idx, progress, direction, speed = pulse
        
        # Update progress
        progress += direction * speed
        
        # Reset if reached end
        if progress > 1.0 or progress < 0.0:
            edge_idx = random.randint(0, len(edges)-1)
            direction = 1 if random.random() > 0.5 else -1
            progress = 0.0 if direction == 1 else 1.0
            speed = random.uniform(0.01, 0.04)
            pulses[idx] = [edge_idx, progress, direction, speed]
            
        edge = edges[edge_idx]
        p1 = nodes[edge[0]][0]
        p2 = nodes[edge[1]][0]
        
        pos = p1 + (p2 - p1) * progress
        
        # Glow
        for i in range(3):
            py5.fill(180, 100, 100, 80 / (i+1))
            py5.push_matrix()
            py5.translate(*pos)
            py5.sphere(3 + i * 2)
            py5.pop_matrix()
            
    # Draw nodes
    for idx, (pos, base_hue, phase) in enumerate(nodes):
        # Slight drift
        drift_x = np.sin(t + phase) * 20
        drift_y = np.cos(t * 0.8 + phase) * 20
        drift_z = np.sin(t * 1.2 + phase) * 20
        
        pulse_val = (np.sin(t * 5 + phase) + 1) * 0.5
        size = 8 + pulse_val * 6
        
        py5.push_matrix()
        py5.translate(pos[0] + drift_x, pos[1] + drift_y, pos[2] + drift_z)
        
        py5.fill(base_hue, 90, 100, 90)
        py5.sphere(size)
        
        # Core
        py5.fill(0, 0, 100, 100)
        py5.sphere(size * 0.4)
        
        py5.pop_matrix()
        
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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

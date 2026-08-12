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
DURATION_SEC = 6
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Differential line parameters
MAX_NODES = 1200
nodes = []  # List of np.array([x, y], dtype=float)

# Spring and repulsion thresholds
REST_DIST = 12.0
REPEL_DIST = 25.0
GROWTH_RATE = 2  # split node when distance > threshold

# Gravitational Attractors
attractors = []  # List of dicts (pos, mass, phase, radius)


class Node:
    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=np.float32)
        self.vel = np.zeros(2, dtype=np.float32)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize a small ring of nodes in the center
    center = np.array([SIZE[0] / 2, SIZE[1] / 2], dtype=np.float32)
    num_init = 40
    for i in range(num_init):
        angle = i * py5.TWO_PI / num_init
        r = 100.0
        x = center[0] + r * np.cos(angle)
        y = center[1] + r * np.sin(angle)
        nodes.append(Node(x, y))
        
    # Initialize 3 orbital attractors
    # pos, speed, orbital radius, angle
    global attractors
    attractors = [
        {"angle": 0.0, "speed": 0.03, "orb_r": 350.0, "mass": 180.0, "color": (255, 215, 0)},
        {"angle": py5.TWO_PI / 3, "speed": 0.02, "orb_r": 420.0, "mass": 220.0, "color": (75, 0, 130)},
        {"angle": 2 * py5.TWO_PI / 3, "speed": -0.04, "orb_r": 280.0, "mass": 150.0, "color": (57, 255, 20)}
    ]


def draw():
    global nodes, attractors
    
    # Fade background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 5, 8, 30)
    py5.rect(0, 0, *SIZE)
    
    py5.blend_mode(py5.ADD)
    
    center = np.array([SIZE[0] / 2, SIZE[1] / 2], dtype=np.float32)
    
    # Update orbital attractors
    for att in attractors:
        att["angle"] += att["speed"]
        att["pos"] = center + np.array([
            att["orb_r"] * np.cos(att["angle"]),
            att["orb_r"] * np.sin(att["angle"])
        ], dtype=np.float32)
        
        # Draw attractor glows
        py5.no_fill()
        c = att["color"]
        py5.stroke(c[0], c[1], c[2], 15)
        py5.stroke_weight(50)
        py5.circle(att["pos"][0], att["pos"][1], 100)
        py5.stroke(c[0], c[1], c[2], 80)
        py5.stroke_weight(10)
        py5.circle(att["pos"][0], att["pos"][1], 30)
        py5.stroke(255, 255, 255, 200)
        py5.stroke_weight(3)
        py5.circle(att["pos"][0], att["pos"][1], 8)
        
    num_nodes = len(nodes)
    if num_nodes < 2:
        return
        
    # Vectorized physics calculations for growth
    positions = np.array([n.pos for n in nodes], dtype=np.float32)
    velocities = np.zeros_like(positions)
    
    # 1. Spring forces between adjacent nodes
    # Forward connections
    diff_forward = np.roll(positions, -1, axis=0) - positions
    dist_forward = np.linalg.norm(diff_forward, axis=1)[:, None]
    dist_forward = np.maximum(dist_forward, 0.1)
    force_forward = diff_forward / dist_forward * (dist_forward - REST_DIST) * 0.18
    
    # Backward connections
    diff_backward = np.roll(positions, 1, axis=0) - positions
    dist_backward = np.linalg.norm(diff_backward, axis=1)[:, None]
    dist_backward = np.maximum(dist_backward, 0.1)
    force_backward = diff_backward / dist_backward * (dist_backward - REST_DIST) * 0.18
    
    velocities += force_forward + force_backward
    
    # 2. Local repulsion forces (vectorized chunk comparison for speed)
    # Compare each node with a subset of other nodes
    repulsion = np.zeros_like(positions)
    for step in [2, 3, 5, 7, 11, 13]:  # sample steps
        other_positions = np.roll(positions, step, axis=0)
        diff = positions - other_positions
        dist = np.linalg.norm(diff, axis=1)[:, None]
        dist = np.maximum(dist, 0.1)
        mask = dist < REPEL_DIST
        weight = (REPEL_DIST - dist) / REPEL_DIST
        repulsion += np.where(mask, (diff / dist) * weight * 0.25, 0.0)
        
    velocities += repulsion
    
    # 3. Gravitational pull towards attractors
    gravity = np.zeros_like(positions)
    for att in attractors:
        diff_att = att["pos"][None, :] - positions
        dist_att = np.linalg.norm(diff_att, axis=1)[:, None]
        dist_att = np.maximum(dist_att, 10.0)
        # Pull force proportional to mass, inversely proportional to distance
        pull = (diff_att / dist_att) * (att["mass"] / dist_att) * 0.45
        gravity += pull
        
    velocities += gravity
    
    # Update velocities and positions
    for i, n in enumerate(nodes):
        n.vel = n.vel * 0.75 + velocities[i] * 0.25
        # Cap velocity
        v_len = np.linalg.norm(n.vel)
        if v_len > 8.0:
            n.vel = (n.vel / v_len) * 8.0
        n.pos += n.vel
        
    # 4. Growth step: Insert new nodes where distance between neighbors is too large
    if num_nodes < MAX_NODES and py5.frame_count % 3 == 0:
        new_nodes = []
        for i in range(num_nodes):
            n1 = nodes[i]
            n2 = nodes[(i + 1) % num_nodes]
            new_nodes.append(n1)
            
            d = np.linalg.norm(n1.pos - n2.pos)
            if d > REST_DIST * 1.5:
                # Insert midpoint node
                mid = (n1.pos + n2.pos) * 0.5
                # Add tiny random perturbation
                mid += np.random.normal(0, 0.2, size=2).astype(np.float32)
                new_nodes.append(Node(mid[0], mid[1]))
        nodes = new_nodes
        
    # Draw growth curves
    py5.no_fill()
    
    # Main glowing green curve
    py5.stroke(57, 255, 20, 180)
    py5.stroke_weight(4)
    py5.begin_shape()
    for n in nodes:
        py5.vertex(n.pos[0], n.pos[1])
    py5.end_shape(py5.CLOSE)
    
    # Inner glow violet curve
    py5.stroke(138, 43, 226, 80)
    py5.stroke_weight(8)
    py5.begin_shape()
    for n in nodes:
        py5.vertex(n.pos[0], n.pos[1])
    py5.end_shape(py5.CLOSE)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)
            
    # Progress feedback
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

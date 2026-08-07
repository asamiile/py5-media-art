"""
kinetic_abyssal_space_colonization_2d
A 4K kinetic visualization of a bioluminescent vascular network growing and 
colonizing a cloud of organic attractors in a deep abyssal void, based on 
the Space Colonization algorithm with dynamic thickness propagation.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import math
import numpy as np
import py5

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

# --- Simulation Parameters ---
SEGMENT_LEN = 8.0
INFLUENCE_RADIUS = 120.0
KILL_RADIUS = 15.0
NUM_ATTRACTORS = 800

# Nodes list of dicts: {"x", "y", "parent", "depth", "descendants"}
nodes = []
attractors = []
active = True


def scatter_attractors(W, H):
    # Scatter attractors in multiple overlapping blobs to form a beautiful organic structure
    pts = []
    # 4 centers
    centers = [
        (W * 0.35, H * 0.35),
        (W * 0.65, H * 0.30),
        (W * 0.50, H * 0.45),
        (W * 0.50, H * 0.22)
    ]
    np_rng = np.random.default_rng(42)
    while len(pts) < NUM_ATTRACTORS:
        cx, cy = centers[np_rng.choice(len(centers))]
        x = np_rng.normal(cx, 160.0)
        y = np_rng.normal(cy, 120.0)
        if 50 < x < W - 50 and 50 < y < H - 50:
            pts.append([x, y])
    return np.array(pts, dtype=np.float32)


def setup():
    global nodes, attractors, active
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    W, H = SIZE
    # Root node at the bottom center
    nodes = [{"x": W * 0.5, "y": H * 0.88, "parent": -1, "depth": 0, "descendants": 1}]
    attractors = scatter_attractors(W, H)
    active = True
    print("[Setup] Space Colonization initialized.")


def step_growth():
    global active, attractors, nodes
    if not active or len(attractors) == 0:
        active = False
        return

    # Convert nodes to numpy array for fast distance calculations
    n_pts = np.array([[n["x"], n["y"]] for n in nodes], dtype=np.float32)
    
    # For each attractor, find the index of the nearest node and the distance
    # shape: (n_attractors, n_nodes)
    diffs = attractors[:, None, :] - n_pts[None, :, :]
    dists = np.hypot(diffs[:, :, 0], diffs[:, :, 1])
    
    nearest_nodes = np.argmin(dists, axis=1)
    min_dists = np.min(dists, axis=1)
    
    # Remove attractors within KILL_RADIUS
    kill_mask = min_dists < KILL_RADIUS
    attractors = attractors[~kill_mask]
    nearest_nodes = nearest_nodes[~kill_mask]
    min_dists = min_dists[~kill_mask]
    
    if len(attractors) == 0:
        active = False
        return
        
    # Find attractors within INFLUENCE_RADIUS
    influence_mask = min_dists < INFLUENCE_RADIUS
    valid_attractors = attractors[influence_mask]
    valid_nearest = nearest_nodes[influence_mask]
    
    if len(valid_attractors) == 0:
        # If no attractors are in range but active, slowly expand anyway (wander)
        # to prevent sudden stops
        active = False
        return
        
    # Group influence vectors by node index
    influenced_dirs = {}
    for attr, ni in zip(valid_attractors, valid_nearest):
        node = nodes[ni]
        dx = attr[0] - node["x"]
        dy = attr[1] - node["y"]
        influenced_dirs.setdefault(ni, []).append((dx, dy))
        
    # Add new nodes
    for ni, dirs in influenced_dirs.items():
        node = nodes[ni]
        avg_dx = sum(d[0] for d in dirs)
        avg_dy = sum(d[1] for d in dirs)
        mag = math.hypot(avg_dx, avg_dy)
        if mag < 1e-6:
            continue
        avg_dx /= mag
        avg_dy /= mag
        
        new_node = {
            "x": node["x"] + avg_dx * SEGMENT_LEN,
            "y": node["y"] + avg_dy * SEGMENT_LEN,
            "parent": ni,
            "depth": node["depth"] + 1,
            "descendants": 1
        }
        nodes.append(new_node)
        
    # Recalculate descendant counts for thickness (backward pass)
    # Reset descendants
    for n in nodes:
        n["descendants"] = 1
    # Accumulate parent descendants
    for i in range(len(nodes) - 1, 0, -1):
        parent_idx = nodes[i]["parent"]
        if parent_idx >= 0:
            nodes[parent_idx]["descendants"] += nodes[i]["descendants"]


def draw():
    global active
    W, H = SIZE
    frame = py5.frame_count
    
    # Run multiple steps per frame to animate growth quickly
    if active:
        steps_per_frame = 3
        for _ in range(steps_per_frame):
            step_growth()
            
    py5.background(240, 35, 5)  # Abyssal indigo-black void
    
    # Calculate max depth for coloring
    max_depth = max((n["depth"] for n in nodes), default=1)
    
    # Draw branches
    for node in nodes:
        if node["parent"] >= 0:
            p = nodes[node["parent"]]
            
            # Pipe model thickness calculation: stroke weight based on descendant count
            sw = math.sqrt(node["descendants"]) * 0.45
            sw = py5.constrain(sw, 0.9, 18.0)
            
            # Depth-based color mapping (Warm amber/gold near root, electric cyan/teal at tips)
            t = node["depth"] / max_depth
            hue = py5.remap(t, 0.0, 1.0, 35, 185)
            sat = py5.remap(t, 0.0, 1.0, 85, 90)
            bri = py5.remap(t, 0.0, 1.0, 75, 95)
            alpha = py5.remap(t, 0.0, 1.0, 85, 95)
            
            # Wide soft glow pass
            py5.stroke(hue, sat * 0.8, bri * 0.8, alpha * 0.25)
            py5.stroke_weight(sw * 2.8)
            py5.line(p["x"], p["y"], node["x"], node["y"])
            
            # Sharp core pass
            py5.stroke(hue, sat, bri, alpha)
            py5.stroke_weight(sw)
            py5.line(p["x"], p["y"], node["x"], node["y"])
            
    # Draw attractors (Bioluminescent auxin spores fading/pulsing)
    py5.no_stroke()
    pulse = math.sin(frame * 0.1) * 1.5 + 2.5
    for ax, ay in attractors:
        # Random hues for organic feel
        py5.fill(325, 80, 85, 45)
        py5.circle(ax, ay, pulse)

    # Vignette shadow
    for i in range(16):
        alpha = int(4 + i * 5)
        m = i * 22
        py5.fill(240, 35, 3, alpha)
        py5.rect(0, 0, W, m)
        py5.rect(0, H - m, W, m)
        py5.rect(0, 0, m, H)
        py5.rect(W - m, 0, m, H)

    # HUD readout
    py5.fill(185, 40, 90, 140)
    py5.text_size(20)
    status = "growing" if active else "complete"
    py5.text(f"t={frame/FPS:.2f}s  nodes: {len(nodes)}  attractors: {len(attractors)}  status: {status}", 50, H - 50)

    # Blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {frame}. Aborting.")
            import os
            os._exit(1)

    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")

    if frame == TOTAL_FRAMES // 2:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] frames removed.")
        import os
        os._exit(0)


py5.run_sketch()

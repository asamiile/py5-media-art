from pathlib import Path
import random
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
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Offscreen graphics size for competitive learning visualization
# 960x540 has 16x fewer pixels than 4K, drastically speeding up CPU alpha blending
PG_WIDTH, PG_HEIGHT = 960, 540

# GNG Parameters
EPS_B = 0.15       # Winner node learning rate
EPS_N = 0.005      # Topological neighbors learning rate
BASE_MAX_AGE = 65  # Edge age threshold for pruning
LAMBDA = 90        # Steps between inserting a new neuron
ALPHA = 0.5        # Error decay fraction for insertion nodes
BETA = 0.0006      # Global error decay per step
MAX_NODES = 450
STEPS_PER_FRAME = 25

# Global GNG simulation state
_nodes = []   # list of [x, y] coordinates (normalized to [0, 1])
_errors = []  # list of floats representing cumulative topological error
_edges = {}   # dictionary matching edge tuples (i, j) to integer age
_step = 0
pg = None     # Py5Graphics offscreen buffer

def sample_distribution(fc):
    """
    Generate target coordinates from a dynamic, swirling double ring distribution.
    The rings rotate, their center orbits, and their radii drift slowly.
    """
    angle = fc * 0.009
    
    if random.random() < 0.55:
        r = 0.30 + math.sin(fc * 0.006) * 0.06
    else:
        r = 0.15 + math.cos(fc * 0.006) * 0.03
        
    t = random.uniform(0, 2.0 * math.pi) + angle
    
    cx = 0.5 + 0.10 * math.sin(fc * 0.004)
    cy = 0.5 + 0.10 * math.cos(fc * 0.004)
    
    px = cx + r * math.cos(t)
    py = cy + r * math.sin(t)
    return np.array([px, py], dtype=np.float32)

def gng_initialize():
    global _nodes, _errors, _edges, _step
    _nodes = [sample_distribution(0).tolist(), sample_distribution(0).tolist()]
    _errors = [0.0, 0.0]
    _edges = {}
    _step = 0

def gng_learn_step(fc, max_age):
    global _step, _nodes, _errors, _edges
    
    signal = sample_distribution(fc)
    
    # Find two nearest nodes
    pos = np.array(_nodes, dtype=np.float32)
    diffs = pos - signal
    dists = (diffs * diffs).sum(axis=1)
    order = np.argsort(dists)
    b1, b2 = int(order[0]), int(order[1])
    
    # Age edges emanating from winner node, prepare deletion list
    to_remove = []
    for (i, j), age in list(_edges.items()):
        if i == b1 or j == b1:
            _edges[(i, j)] = age + 1
            if _edges[(i, j)] > max_age:
                to_remove.append((i, j))
    for e in to_remove:
        del _edges[e]
        
    # Create or refresh topological edge connection
    key = (min(b1, b2), max(b1, b2))
    _edges[key] = 0
    
    # Accumulate learning error
    _errors[b1] += float(dists[b1])
    
    # Move winner and its direct neighbors towards the signal
    _nodes[b1] = (np.array(_nodes[b1]) + EPS_B * (signal - np.array(_nodes[b1]))).tolist()
    neighbors_b1 = {j for (i, j) in _edges if i == b1} | {i for (i, j) in _edges if j == b1}
    for nb in neighbors_b1:
        _nodes[nb] = (np.array(_nodes[nb]) + EPS_N * (signal - np.array(_nodes[nb]))).tolist()
        
    # Remove isolated nodes (excluding base seed nodes)
    connected = set()
    for i, j in _edges:
        connected.add(i)
        connected.add(j)
    to_del = [i for i in range(len(_nodes)) if i not in connected and i >= 2]
    
    for i in sorted(to_del, reverse=True):
        _nodes.pop(i)
        _errors.pop(i)
        
        # Adjust indices in edges
        new_edges = {}
        for (a, b), age in _edges.items():
            a2 = a - (a > i) if a != i else None
            b2 = b - (b > i) if b != i else None
            if a2 is not None and b2 is not None:
                new_edges[(min(a2, b2), max(a2, b2))] = age
        _edges = new_edges
        
    # Decay all errors globally
    for k in range(len(_errors)):
        _errors[k] *= (1.0 - BETA)
        
    # Grow network
    if fc <= 780 and _step % LAMBDA == 0 and len(_nodes) < MAX_NODES:
        q = int(np.argmax(_errors))
        neighbors_q = {j for (i, j) in _edges if i == q} | {i for (i, j) in _edges if j == q}
        if neighbors_q:
            f = max(neighbors_q, key=lambda n: _errors[n])
            new_pos = ((np.array(_nodes[q]) + np.array(_nodes[f])) * 0.5).tolist()
            new_idx = len(_nodes)
            _nodes.append(new_pos)
            _errors.append((_errors[q] + _errors[f]) * ALPHA)
            
            key_qf = (min(q, f), max(q, f))
            if key_qf in _edges:
                del _edges[key_qf]
            _edges[(min(q, new_idx), max(q, new_idx))] = 0
            _edges[(min(f, new_idx), max(f, new_idx))] = 0
            _errors[q] *= ALPHA
            _errors[f] *= ALPHA
            
    _step += 1

def setup():
    global pg
    py5.size(*SIZE)
    py5.smooth(2)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize offscreen canvas
    pg = py5.create_graphics(PG_WIDTH, PG_HEIGHT)
    
    # Initialize competitive network state
    random.seed(42)
    gng_initialize()

def draw():
    global _nodes, _errors, _edges
    fc = py5.frame_count
    
    # Slowly accelerate edge aging in the final phase to dissolve the network
    if fc > 780:
        max_age = max(1, int(BASE_MAX_AGE * py5.remap(fc, 780, 900, 1.0, 0.05)))
    else:
        max_age = BASE_MAX_AGE
        
    # 1. Update GNG Simulation
    for _ in range(STEPS_PER_FRAME):
        gng_learn_step(fc, max_age)
        
    # 2. Render to offscreen canvas (smooth 2x handles anti-aliasing here)
    pg.begin_draw()
    pg.smooth(2)
    pg.color_mode(pg.HSB, 360, 100, 100, 100)
    pg.background(240, 70, 3, 100)  # Dark navy void
    pg.blend_mode(pg.ADD)
    
    # Draw ghost template of the input distribution (200 random samples)
    pg.no_stroke()
    pg.fill(185, 80, 70, 15)  # Faint cyan dust
    for _ in range(200):
        pos = sample_distribution(fc)
        x = pos[0] * PG_WIDTH
        y = pos[1] * PG_HEIGHT
        pg.circle(x, y, 1.5)
        
    # Draw Network Edges
    max_err = max(_errors) if _errors else 1.0
    for (i, j), age in _edges.items():
        age_ratio = age / BASE_MAX_AGE
        hue = py5.lerp(185, 275, age_ratio)
        sat = py5.lerp(80, 90, age_ratio)
        bri = py5.lerp(90, 25, age_ratio)
        alpha = py5.lerp(85, 25, age_ratio)
        
        pg.stroke(hue, sat, bri, alpha)
        pg.stroke_weight(py5.lerp(1.6, 0.4, age_ratio))
        
        xi, yi = _nodes[i][0] * PG_WIDTH, _nodes[i][1] * PG_HEIGHT
        xj, yj = _nodes[j][0] * PG_WIDTH, _nodes[j][1] * PG_HEIGHT
        pg.line(xi, yi, xj, yj)
        
    # Draw Network Nodes
    pg.no_stroke()
    for k, (nx, ny) in enumerate(_nodes):
        err_ratio = min(_errors[k] / (max_err + 1e-9), 1.0)
        hue = py5.lerp(145, 325, err_ratio)
        size = py5.lerp(3.2, 9.6, err_ratio)
        
        # Soft glowing outer aura
        pg.fill(hue, 85, 90, 20)
        pg.circle(nx * PG_WIDTH, ny * PG_HEIGHT, size * 2.2)
        
        # Solid core
        pg.fill(hue, 90, 95, 95)
        pg.circle(nx * PG_WIDTH, ny * PG_HEIGHT, size * 0.8)
        
    pg.end_draw()
    
    # 3. Draw upscaled offscreen buffer to main canvas and overlay 4K crisp HUD
    py5.background(240, 70, 3)
    py5.image(pg, 0, 0, py5.width, py5.height)
    
    # Outer boundary thin lines
    py5.stroke(185, 80, 50, 25)
    py5.stroke_weight(1.0)
    py5.no_fill()
    py5.rect(80, 80, py5.width - 160, py5.height - 160)
    
    # Corner crosses
    py5.line(70, 80, 90, 80)
    py5.line(80, 70, 80, 90)
    py5.line(py5.width - 90, 80, py5.width - 70, 80)
    py5.line(py5.width - 80, 70, py5.width - 80, 90)
    py5.line(80, py5.height - 80, 80, py5.height - 70)
    py5.line(80, py5.height - 80, 70, py5.height - 80)
    
    # Text metadata (rendered in crisp 4K)
    py5.fill(185, 60, 85, 75)
    py5.text_size(14)
    py5.text("TOPOLOGY ADAPTATION NET // FRITZKE GROWING NEURAL GAS", 110, 120)
    py5.text(f"NEURONS ACTIVE: {len(_nodes):03d} / {MAX_NODES}", 110, 150)
    py5.text(f"SYNAPTIC EDGES: {len(_edges):04d}", 110, 175)
    py5.text(f"LEARNING RATES: WINNER={EPS_B:.3f} | NEIGHBORS={EPS_N:.3f}", 110, 200)
    py5.text(f"PRUNING AGE THRESHOLD: {max_age:02d} SEC", 110, 225)
    py5.text(f"SIMULATION TIME STEP: {_step:05d}", 110, 250)
    
    # Render Progress
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()

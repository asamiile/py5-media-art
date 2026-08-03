import math
import shutil
import subprocess
import sys
from pathlib import Path
import random
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

# 15 seconds @ 60 FPS (900 frames)
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Simulation constants
N_NODES = 120
K_NEIGH = 8  # k-regular ring lattice neighborhood

# Structural data arrays
node_pos = None  # (N, 2) unit circle positions
base_edges = []  # List of dict: {'u': u, 'v': v, 'threshold': t, 'target': new_v}
history_cc = []  # Clustering coefficient history
history_pl = []  # Path length history
history_p = []   # Rewiring probability history

def setup():
    global node_pos, base_edges
    py5.size(*SIZE)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # 1. Generate node coordinates on a circle
    angles = np.linspace(0, math.tau, N_NODES, endpoint=False)
    node_pos = np.column_stack([np.cos(angles), np.sin(angles)]).astype(np.float32)
    
    # 2. Build initial edge structures
    # We assign each lattice connection a pre-determined rewiring threshold and target
    # to guarantee a continuous, flicker-free topological transition.
    random.seed(42)  # Seed for deterministic structural flow
    for i in range(N_NODES):
        for d in range(1, K_NEIGH // 2 + 1):
            j = (i + d) % N_NODES
            
            # Find a valid rewired target (avoid self loops)
            possible_targets = [m for m in range(N_NODES) if m != i and m != j]
            target = random.choice(possible_targets)
            
            base_edges.append({
                'u': i,
                'v': j,
                'threshold': random.uniform(0.02, 0.98),  # Trigger rewire inside this interval
                'target': target
            })

def compute_clustering_coeff(adj):
    # Compute mean local clustering coefficient using vector slicing
    cc_sum = 0.0
    for i in range(N_NODES):
        nbrs = np.where(adj[i])[0]
        ki = len(nbrs)
        if ki < 2:
            continue
        # Count connections within neighbors
        sub_adj = adj[nbrs][:, nbrs]
        links = np.sum(sub_adj) // 2
        cc_sum += 2 * links / (ki * (ki - 1))
    return cc_sum / N_NODES

def compute_path_length_approx(adj, samples=40):
    # Fast randomized BFS approximation of average path length
    total_dist = 0.0
    valid_pairs = 0
    
    for _ in range(samples):
        u = random.randint(0, N_NODES - 1)
        v = random.randint(0, N_NODES - 1)
        if u == v:
            continue
            
        # BFS search
        visited = {u}
        queue = [(u, 0)]
        found_dist = -1
        while queue:
            curr, d = queue.pop(0)
            if curr == v:
                found_dist = d
                break
            for nbr in np.where(adj[curr])[0]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append((nbr, d + 1))
                    
        if found_dist != -1:
            total_dist += found_dist
            valid_pairs += 1
            
    return total_dist / valid_pairs if valid_pairs > 0 else 0.0

def draw():
    global history_cc, history_pl, history_p
    fc = py5.frame_count
    
    # Sweep probability p smoothly from 0.0 to 1.0
    p = fc / TOTAL_FRAMES
    
    # 1. Resolve network structure for the current p
    adj = np.zeros((N_NODES, N_NODES), dtype=np.int8)
    active_edges = []  # List of (x1, y1, x2, y2, is_shortcut)
    
    for edge in base_edges:
        u, v = edge['u'], edge['v']
        if p >= edge['threshold']:
            # Rewired edge (shortcut)
            target = edge['target']
            adj[u, target] = adj[target, u] = 1
            active_edges.append((u, target, True))
        else:
            # Regular lattice edge
            adj[u, v] = adj[v, u] = 1
            active_edges.append((u, v, False))
            
    # 2. Compute network statistics
    cc = compute_clustering_coeff(adj)
    pl = compute_path_length_approx(adj)
    
    # Record stats history
    history_cc.append(cc)
    history_pl.append(pl)
    history_p.append(p)
    
    # 3. Draw Background
    py5.background(10, 12, 20)  # Deep Obsidian Slate
    
    # Outer ring coordinate scaling
    cx, cy = py5.width * 0.5, py5.height * 0.5
    ring_radius = py5.height * 0.38
    
    # Map node positions
    node_x = node_pos[:, 0] * ring_radius + cx
    node_y = node_pos[:, 1] * ring_radius + cy
    
    # 4. Draw Edges
    # Draw lattice edges (low opacity indigo) first
    py5.stroke_weight(1.0)
    for u, v, is_shortcut in active_edges:
        if not is_shortcut:
            py5.stroke(30, 50, 140, 45)  # Deep Cobalt Indigo
            py5.line(node_x[u], node_y[u], node_x[v], node_y[v])
            
    # Draw rewired shortcut edges (glowing amber)
    py5.stroke_weight(1.8)
    for u, v, is_shortcut in active_edges:
        if is_shortcut:
            py5.stroke(255, 160, 20, 120)  # Solar Amber Gold
            py5.line(node_x[u], node_y[u], node_x[v], node_y[v])
            
            # Glowing signal pulse traveling along shortcut
            pulse_t = (fc * 0.03 + u * 0.1) % 1.0
            px = py5.lerp(node_x[u], node_x[v], pulse_t)
            py5.fill(255, 160, 20, 200)
            py5.no_stroke()
            py5.circle(px, py5.lerp(node_y[u], node_y[v], pulse_t), 6)

    # 5. Draw Nodes (glowing vector dots with technical ticks)
    deg = adj.sum(axis=1)
    max_deg = max(deg.max(), 1)
    
    for i in range(N_NODES):
        t = deg[i] / max_deg
        
        # Draw node core
        py5.fill(0, 210, 255, 180 + t * 75)  # Electric Cyan
        py5.no_stroke()
        py5.circle(node_x[i], node_y[i], 8 + t * 6)
        
        # Outer crosshair ticks for high-degree hubs
        if deg[i] > K_NEIGH:
            py5.no_fill()
            py5.stroke(0, 210, 255, 100)
            py5.stroke_weight(1)
            py5.circle(node_x[i], node_y[i], 18)
            
            # Tiny radial tick marks
            angle = (fc * 0.02 + i * 0.5)
            tx = node_x[i] + math.cos(angle) * 12
            ty = node_y[i] + math.sin(angle) * 12
            py5.stroke(0, 210, 255, 180)
            py5.line(node_x[i], node_y[i], tx, ty)

    # 6. Adjacency Matrix Visualizer (bottom-left corner)
    matrix_x, matrix_y = 100, py5.height - 350
    matrix_size = 220
    py5.fill(15, 20, 32, 180)
    py5.stroke(0, 210, 255, 60)
    py5.stroke_weight(2)
    py5.rect(matrix_x - 10, matrix_y - 30, matrix_size + 20, matrix_size + 40)
    
    py5.fill(0, 210, 255, 220)
    py5.text_size(14)
    py5.text("CONNECTIVITY MATRIX A[i, j]", matrix_x, matrix_y - 12)
    
    # Draw grid cells
    cell_w = matrix_size / N_NODES
    py5.no_stroke()
    for i in range(N_NODES):
        for j in range(N_NODES):
            if adj[i, j] > 0:
                # Highlight rewired edges in amber, regular in cyan
                is_rewired = False
                for edge in base_edges:
                    if (edge['u'] == i and edge['target'] == j) or (edge['u'] == j and edge['target'] == i):
                        if p >= edge['threshold']:
                            is_rewired = True
                            break
                if is_rewired:
                    py5.fill(255, 160, 20, 180)
                else:
                    py5.fill(0, 210, 255, 90)
                py5.rect(matrix_x + i * cell_w, matrix_y + j * cell_w, cell_w + 0.5, cell_w + 0.5)

    # 7. Real-time Metrics Plotter (top-right corner)
    plot_x, plot_y = py5.width - 450, 100
    plot_w, plot_h = 350, 180
    
    py5.fill(15, 20, 32, 180)
    py5.stroke(0, 210, 255, 60)
    py5.stroke_weight(2)
    py5.rect(plot_x - 15, plot_y - 35, plot_w + 30, plot_h + 70)
    
    py5.fill(0, 210, 255, 220)
    py5.text_size(14)
    py5.text("TOPOLOGICAL PHASE TRANSITION", plot_x, plot_y - 15)
    
    # Plot grid lines
    py5.stroke(0, 210, 255, 30)
    py5.stroke_weight(1)
    for grid_idx in range(5):
        gy = plot_y + grid_idx * (plot_h / 4)
        py5.line(plot_x, gy, plot_x + plot_w, gy)
        gx = plot_x + grid_idx * (plot_w / 4)
        py5.line(gx, plot_y, gx, plot_y + plot_h)
        
    # Plot Clustering Coefficient (Cyan) and Path Length (Amber)
    if len(history_p) > 1:
        # Scale Path Length to match 0.0 - 1.0 range (base ring path length is ~N/(2K))
        # Initial ring lattice path length is approx N_NODES / (2 * K_NEIGH) = 120 / 16 = 7.5
        max_pl = N_NODES / (2.0 * K_NEIGH)
        
        py5.no_fill()
        # Draw C(p)
        py5.stroke(0, 210, 255, 220)
        py5.stroke_weight(2)
        py5.begin_shape()
        for idx, hp in enumerate(history_p):
            px = plot_x + hp * plot_w
            py = plot_y + plot_h - (history_cc[idx] * plot_h)
            py5.vertex(px, py)
        py5.end_shape()
        
        # Draw L(p)
        py5.stroke(255, 160, 20, 220)
        py5.stroke_weight(2)
        py5.begin_shape()
        for idx, hp in enumerate(history_p):
            px = plot_x + hp * plot_w
            # Normalized path length
            norm_pl = history_pl[idx] / max_pl
            py = plot_y + plot_h - (norm_pl * plot_h)
            py5.vertex(px, py)
        py5.end_shape()
        
    # Plot Legend
    py5.text_size(12)
    py5.fill(0, 210, 255, 220)
    py5.text(f"Clustering C(p) : {cc:.3f}", plot_x, plot_y + plot_h + 20)
    py5.fill(255, 160, 20, 220)
    py5.text(f"Path Length L(p) : {pl:.2f}", plot_x + 180, plot_y + plot_h + 20)

    # 8. Cybernetic HUD Telemetry and Borders
    py5.stroke(0, 210, 255, 90)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.rect(40, 40, py5.width - 80, py5.height - 80)
    
    # Corner targets
    for tx, ty in [(40, 40), (py5.width - 40, 40), (40, py5.height - 40), (py5.width - 40, py5.height - 40)]:
        py5.stroke(0, 210, 255, 180)
        py5.stroke_weight(3)
        py5.line(tx - 20, ty, tx + 20, ty)
        py5.line(tx, ty - 20, tx, ty + 20)

    # Telemetry text (top-left)
    py5.fill(0, 210, 255, 220)
    py5.text_size(24)
    py5.text("SYSTEM: WATTS-STROGATZ SMALL-WORLD DYNAMICS", 80, 100)
    
    py5.text_size(18)
    py5.fill(255, 200)
    py5.text(f"TOTAL NODES : {N_NODES} STATIONS", 80, 145)
    py5.text(f"NEIGHBORS   : K = {K_NEIGH} (LATTICE)", 80, 175)
    py5.text(f"REWIRE PROB : p = {p:.3f} ({p*100.0:.1f}%)", 80, 205)
    
    # Highlight the Small-World regime: p in [0.01, 0.15]
    if 0.01 <= p <= 0.15:
        py5.fill(0, 210, 255, 255)
        py5.text("REGIME      : SMALL-WORLD STATE (HIGH C, LOW L)", 80, 235)
    elif p < 0.01:
        py5.fill(100, 150, 255, 200)
        py5.text("REGIME      : REGULAR RING LATTICE", 80, 235)
    else:
        py5.fill(255, 160, 20, 200)
        py5.text("REGIME      : RANDOM ERDŐS-RÉNYI GRAPH", 80, 235)

    # Progress bar (top-right)
    bar_width = 300
    bar_x = py5.width - 80 - bar_width
    bar_y = py5.height - 90
    py5.no_fill()
    py5.stroke(0, 210, 255, 100)
    py5.stroke_weight(2)
    py5.rect(bar_x, bar_y, bar_width, 16)
    
    py5.fill(0, 210, 255, 180)
    py5.no_stroke()
    py5.rect(bar_x + 2, bar_y + 2, (bar_width - 4) * (fc / TOTAL_FRAMES), 12)
    
    py5.fill(255, 220)
    py5.text_size(18)
    py5.text(f"FRAME RENDER : {fc} / {TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)", bar_x, bar_y - 15)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if blank screen
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress logging
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

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
        
        # Save preview snapshot (around p=0.08, which is the perfect small-world regime!)
        preview_frame_idx = int(0.08 * TOTAL_FRAMES)
        mid = str(FRAMES_DIR / f"frame-{preview_frame_idx:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()

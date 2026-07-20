from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    global num_nodes, nodes, edges, hierarchy
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create a random DAG
    num_nodes = 60
    G = nx.gnp_random_graph(num_nodes, 0.08, directed=True)
    G = nx.DiGraph([(u, v) for (u, v) in G.edges() if u < v]) # ensure acyclic
    
    edges = list(G.edges())
    
    # Calculate hierarchy levels (longest path to leaf)
    hierarchy = {}
    for n in G.nodes():
        hierarchy[n] = 0
        
    for n in list(nx.topological_sort(G)):
        for child in G.successors(n):
            hierarchy[child] = max(hierarchy[child], hierarchy[n] + 1)
            
    max_level = max(hierarchy.values()) if hierarchy else 1
    
    nodes = []
    for n in G.nodes():
        # Start random, end up sorted by hierarchy
        start_x = random.uniform(SIZE[0] * 0.1, SIZE[0] * 0.9)
        start_y = random.uniform(SIZE[1] * 0.1, SIZE[1] * 0.9)
        
        target_y = SIZE[1] * 0.1 + (hierarchy[n] / max_level) * (SIZE[1] * 0.8)
        
        # distribute evenly on x
        level_nodes = [k for k, v in hierarchy.items() if v == hierarchy[n]]
        level_nodes.sort()
        idx = level_nodes.index(n)
        if len(level_nodes) > 1:
            target_x = SIZE[0] * 0.1 + (idx / (len(level_nodes) - 1)) * (SIZE[0] * 0.8)
        else:
            target_x = SIZE[0] * 0.5
            
        nodes.append({
            'id': n,
            'start_x': start_x,
            'start_y': start_y,
            'target_x': target_x,
            'target_y': target_y,
            'x': start_x,
            'y': start_y,
            'size': random.uniform(20, 60)
        })

def draw():
    py5.background(15, 20, 25) # Dark grey-blue
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Smoothstep interpolation
    t_smooth = t * t * (3 - 2 * t)
    
    # Update node positions
    for n in nodes:
        # A bit of noise
        noise_x = (py5.os_noise(n['id'], py5.frame_count * 0.01) - 0.5) * 150 * (1 - t_smooth)
        noise_y = (py5.os_noise(n['id'] + 100, py5.frame_count * 0.01) - 0.5) * 150 * (1 - t_smooth)
        
        n['x'] = n['start_x'] + (n['target_x'] - n['start_x']) * t_smooth + noise_x
        n['y'] = n['start_y'] + (n['target_y'] - n['start_y']) * t_smooth + noise_y

    # Draw edges
    py5.no_fill()
    py5.stroke_weight(3)
    for u_id, v_id in edges:
        u = nodes[u_id]
        v = nodes[v_id]
        
        # Distance fade
        d = py5.dist(u['x'], u['y'], v['x'], v['y'])
        alpha = py5.remap(d, 0, SIZE[1] * 1.5, 200, 20)
        
        py5.stroke(50, 150, 255, alpha) # Glowing blue
        
        # Bezier curve
        cx1 = u['x']
        cy1 = u['y'] + (v['y'] - u['y']) * 0.5
        cx2 = v['x']
        cy2 = v['y'] - (v['y'] - u['y']) * 0.5
        
        py5.bezier(u['x'], u['y'], cx1, cy1, cx2, cy2, v['x'], v['y'])

    # Draw nodes
    py5.no_stroke()
    for n in nodes:
        # Glow
        for r in [n['size'] * 2.5, n['size'] * 1.5, n['size']]:
            alpha = py5.remap(r, n['size'], n['size'] * 2.5, 255, 0)
            py5.fill(255, 100, 0, alpha * 0.8) # Neon orange
            py5.ellipse(n['x'], n['y'], r, r)
        
        py5.fill(255)
        py5.ellipse(n['x'], n['y'], n['size'] * 0.3, n['size'] * 0.3)

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
        import os
        os._exit(0)

py5.run_sketch()

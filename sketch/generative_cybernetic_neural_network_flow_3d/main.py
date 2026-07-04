from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Configuration
NUM_NODES = 400
NUM_PACKETS = 4000
CONNECTION_RADIUS = 0.35 # in normalized coordinates [-1, 1]

# State
nodes = None
edges = None # List of (node_i, node_j)
adjacency = None # List of lists of neighbor indices
packets = None # Array of shape (NUM_PACKETS, 3): [edge_idx, progress (0 to 1), speed]

def setup():
    global nodes, edges, adjacency, packets
    
    py5.size(*SIZE)
    
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Generate nodes
    # Use points on the surface of a sphere or within a volume
    theta = np.random.uniform(0, 2 * np.pi, NUM_NODES)
    phi = np.arccos(np.random.uniform(-1, 1, NUM_NODES))
    r = np.random.uniform(0.3, 1.0, NUM_NODES) ** (1/3) # uniform volume distribution
    
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    nodes = np.column_stack((x, y, z))
    
    # Generate edges (Random Geometric Graph)
    edges_list = []
    adjacency_list = [[] for _ in range(NUM_NODES)]
    
    for i in range(NUM_NODES):
        for j in range(i + 1, NUM_NODES):
            dist = np.linalg.norm(nodes[i] - nodes[j])
            if dist < CONNECTION_RADIUS:
                edges_list.append((i, j))
                edge_idx = len(edges_list) - 1
                adjacency_list[i].append((j, edge_idx))
                adjacency_list[j].append((i, edge_idx))
                
    edges = np.array(edges_list)
    adjacency = adjacency_list
    
    # Remove isolated nodes (nodes with 0 edges) by connecting them to their nearest neighbor
    for i in range(NUM_NODES):
        if len(adjacency[i]) == 0:
            dists = np.linalg.norm(nodes - nodes[i], axis=1)
            dists[i] = np.inf
            nearest = np.argmin(dists)
            edges_list.append((i, nearest))
            edge_idx = len(edges_list) - 1
            adjacency[i].append((nearest, edge_idx))
            adjacency[nearest].append((i, edge_idx))
            
    edges = np.array(edges_list)
    
    # Generate packets
    packets = np.zeros((NUM_PACKETS, 3))
    packets[:, 0] = np.random.randint(0, len(edges), NUM_PACKETS) # random edge
    packets[:, 1] = np.random.uniform(0, 1, NUM_PACKETS) # random progress
    # speed depends on edge length so they don't jump too fast
    edge_lengths = np.linalg.norm(nodes[edges[:, 0]] - nodes[edges[:, 1]], axis=1)
    
    # speed assigned later per update

def draw():
    global packets
    
    py5.background(5, 5, 5) # Very dark gray/black
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Define rotation matrices
    theta_y = t * py5.TWO_PI
    theta_x = np.sin(t * py5.TWO_PI) * 0.2
    
    cy, sy = np.cos(theta_y), np.sin(theta_y)
    cx, sx = np.cos(theta_x), np.sin(theta_x)
    
    rot_y = np.array([
        [cy, 0, sy],
        [0, 1, 0],
        [-sy, 0, cy]
    ])
    
    rot_x = np.array([
        [1, 0, 0],
        [0, cx, -sx],
        [0, sx, cx]
    ])
    
    def project(pts_3d):
        # Rotate
        rotated = pts_3d @ rot_y.T @ rot_x.T
        
        # Perspective project
        z = rotated[:, 2]
        # Camera distance
        dist = 3.0
        w = dist / (dist - z)
        
        scale_factor = min(py5.width, py5.height) * 0.4
        x2d = py5.width / 2 + rotated[:, 0] * w * scale_factor
        y2d = py5.height / 2 + rotated[:, 1] * w * scale_factor
        
        return np.column_stack((x2d, y2d))
        
    projected_nodes = project(nodes)
    
    # Draw edges
    py5.stroke(280, 80, 40, 20) # Dark purple edges
    py5.stroke_weight(1.0)
    
    py5.begin_shape(py5.LINES)
    for edge in edges:
        p1 = projected_nodes[edge[0]]
        p2 = projected_nodes[edge[1]]
        py5.vertex(p1[0], p1[1])
        py5.vertex(p2[0], p2[1])
    py5.end_shape()
    
    # Draw nodes
    py5.stroke(300, 50, 60, 50)
    py5.stroke_weight(4.0)
    py5.begin_shape(py5.POINTS)
    for node in projected_nodes:
        py5.vertex(node[0], node[1])
    py5.end_shape()
    
    # Update packets
    edge_lengths = np.linalg.norm(nodes[edges[:, 0]] - nodes[edges[:, 1]], axis=1)
    
    packet_positions = np.zeros((NUM_PACKETS, 3))
    
    for i in range(NUM_PACKETS):
        edge_idx = int(packets[i, 0])
        progress = packets[i, 1]
        
        speed = 0.01 / max(edge_lengths[edge_idx], 0.01)
        progress += speed
        
        if progress >= 1.0:
            dest_node = edges[edge_idx, 1]
            neighbors = adjacency[dest_node]
            if neighbors:
                next_neighbor = neighbors[np.random.randint(0, len(neighbors))]
                packets[i, 0] = next_neighbor[1]
                packets[i, 1] = 0.0
            else:
                progress = 1.0
        
        packets[i, 1] = progress
        
        edge = edges[int(packets[i, 0])]
        p1 = nodes[edge[0]]
        p2 = nodes[edge[1]]
        packet_positions[i] = p1 + (p2 - p1) * progress

    # Project and draw packets
    projected_packets = project(packet_positions)
    py5.stroke_weight(8.0)
    py5.begin_shape(py5.POINTS)
    
    for i in range(NUM_PACKETS):
        hue = 180 if i % 2 == 0 else 320
        py5.stroke(hue, 90, 100, 80)
        p = projected_packets[i]
        py5.vertex(p[0], p[1])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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

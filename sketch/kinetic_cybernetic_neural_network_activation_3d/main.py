import os
from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import KDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Network Setup
N_NODES = 2000
CONNECTION_RADIUS = 300
NETWORK_RADIUS = 1200

# Pre-calculate graph
nodes_3d = np.random.normal(0, NETWORK_RADIUS / 2.5, (N_NODES, 3))

# Calculate connections using KDTree
tree = KDTree(nodes_3d)
pairs = tree.query_pairs(CONNECTION_RADIUS)
edges = np.array(list(pairs))

# Pre-calculate edges start and end
edge_starts = nodes_3d[edges[:, 0]]
edge_ends = nodes_3d[edges[:, 1]]
n_edges = len(edges)

def project_3d_to_2d(points_3d, fov=1500):
    z = points_3d[:, 2] + 2500
    z = np.maximum(z, 1.0)
    x_proj = (points_3d[:, 0] * fov) / z
    y_proj = (points_3d[:, 1] * fov) / z
    x_proj += SIZE[0] / 2
    y_proj += SIZE[1] / 2
    return np.column_stack((x_proj, y_proj))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0, 0, 5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    # Rotate network slowly
    rot_angle_y = t * 0.1
    rot_angle_x = t * 0.05
    
    # Y-axis rotation
    cy, sy = np.cos(rot_angle_y), np.sin(rot_angle_y)
    ry_x = nodes_3d[:, 0] * cy - nodes_3d[:, 2] * sy
    ry_z = nodes_3d[:, 0] * sy + nodes_3d[:, 2] * cy
    rotated = np.column_stack((ry_x, nodes_3d[:, 1], ry_z))
    
    # X-axis rotation
    cx, sx = np.cos(rot_angle_x), np.sin(rot_angle_x)
    rx_y = rotated[:, 1] * cx - rotated[:, 2] * sx
    rx_z = rotated[:, 1] * sx + rotated[:, 2] * cx
    rotated[:, 1] = rx_y
    rotated[:, 2] = rx_z
    
    # Propagating activation wave
    # The wave travels from bottom to top, left to right
    activation_field = np.sin(rotated[:, 0]*0.002 + rotated[:, 1]*0.003 - t * 4)
    # Normalize to 0-1 and steepen the curve
    activation_field = np.clip(activation_field, 0, 1) ** 4
    
    # Project nodes
    nodes_2d = project_3d_to_2d(rotated)
    
    # Re-calculate rotated edges dynamically (for accurate line drawing)
    edge_starts_rot = rotated[edges[:, 0]]
    edge_ends_rot = rotated[edges[:, 1]]
    
    starts_2d = project_3d_to_2d(edge_starts_rot)
    ends_2d = project_3d_to_2d(edge_ends_rot)
    
    # Calculate edge activations as the average of their nodes
    edge_activations = (activation_field[edges[:, 0]] + activation_field[edges[:, 1]]) / 2
    
    # Base network lines
    py5.stroke_weight(1)
    py5.stroke(0, 68, 255, 30)
    lines_array = np.column_stack((starts_2d[:, 0], starts_2d[:, 1], ends_2d[:, 0], ends_2d[:, 1]))
    py5.lines(lines_array)
    
    # Active lines
    active_mask = edge_activations > 0.1
    if np.any(active_mask):
        active_lines = lines_array[active_mask]
        py5.stroke_weight(3)
        py5.stroke(0, 255, 255, 150)
        py5.lines(active_lines)
    
    # Nodes
    py5.stroke_weight(5)
    py5.stroke(0, 68, 255, 100)
    py5.points(nodes_2d)
    
    # Active nodes
    active_node_mask = activation_field > 0.2
    if np.any(active_node_mask):
        py5.stroke_weight(12)
        py5.stroke(255, 255, 255, 200)
        py5.points(nodes_2d[active_node_mask])

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
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()

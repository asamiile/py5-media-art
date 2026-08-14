from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
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

# Grid dimension for DBM simulation (small grid for speed, upscaled to 4K)
GRID_W = 120
GRID_H = 120
phi = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Cluster mask: 1 if part of growing tree, 0 otherwise
cluster = np.zeros((GRID_H, GRID_W), dtype=np.uint8)
# Seed the center
cy, cx = GRID_H // 2, GRID_W // 2
cluster[cy, cx] = 1

# List of nodes in the cluster for rendering
nodes = [(cx, cy)]
# Parent links for drawing lines: parent[child_index] = parent_index
parent = {0: 0}

# Fractal dimension tracking
fractal_dims = []
img_rgb_mid = None


def solve_laplace(max_iter=40):
    """
    Solves Laplace equation \nabla^2 \phi = 0 with boundary conditions:
    \phi = 0 on cluster
    \phi = 1 on outer boundaries (circular boundary)
    """
    global phi
    # Reset potential
    phi.fill(0.5)
    # Set cluster boundary condition
    phi[cluster == 1] = 0.0
    
    # Jacobi relaxation solver
    h, w = GRID_H, GRID_W
    r_max = min(w, h) // 2 - 2
    cy, cx = h // 2, w // 2
    
    # Precompute distance mask for circular outer boundary
    y_indices, x_indices = np.indices((h, w))
    dist_from_center = np.sqrt((x_indices - cx)**2 + (y_indices - cy)**2)
    boundary_mask = dist_from_center >= r_max
    
    phi[boundary_mask] = 1.0
    
    # Internal mask where updates happen (inside circle, not in cluster)
    update_mask = (dist_from_center < r_max) & (cluster == 0)
    
    for _ in range(max_iter):
        # 4-neighbor average
        next_phi = 0.25 * (
            np.roll(phi, 1, axis=0) +
            np.roll(phi, -1, axis=0) +
            np.roll(phi, 1, axis=1) +
            np.roll(phi, -1, axis=1)
        )
        # Apply boundary conditions
        phi[update_mask] = next_phi[update_mask]
        phi[cluster == 1] = 0.0
        phi[boundary_mask] = 1.0


def grow_dbm(eta=2.5):
    """
    Grow the cluster by selecting a candidate neighbor based on probability field (\nabla \phi)^\eta
    """
    global cluster, nodes, parent
    
    # Find all perimeter candidate sites (0s that are adjacent to 1s)
    # Dilate cluster
    kernel = np.array([[0, 1, 0],
                       [1, 1, 1],
                       [0, 1, 0]], dtype=np.uint8)
    dilated = cv2.dilate(cluster, kernel)
    candidates_mask = (dilated == 1) & (cluster == 0)
    
    # Outer boundary check (restrict growth close to edges)
    h, w = GRID_H, GRID_W
    r_max = min(w, h) // 2 - 4
    cy, cx = h // 2, w // 2
    y_indices, x_indices = np.indices((h, w))
    dist_from_center = np.sqrt((x_indices - cx)**2 + (y_indices - cy)**2)
    candidates_mask = candidates_mask & (dist_from_center < r_max)
    
    candidate_y, candidate_x = np.where(candidates_mask)
    if len(candidate_y) == 0:
        return
        
    # Growth probability is proportional to (\nabla \phi)^\eta = (phi_neighbor - phi_candidate)^\eta
    # Since phi_candidate is 0 (as candidate is adjacent to cluster where phi=0),
    # the gradient is approximately the potential of the candidate itself (from the 1s around it).
    potentials = phi[candidates_mask]
    
    # Growth probability is higher where potential gradient is steep (high phi)
    probs = potentials ** eta
    sum_probs = np.sum(probs)
    if sum_probs > 0:
        probs /= sum_probs
    else:
        probs = np.ones(len(probs)) / len(probs)
        
    # Select candidate
    idx = np.random.choice(len(probs), p=probs)
    new_y, new_x = candidate_y[idx], candidate_x[idx]
    
    # Find which node in the cluster this candidate attaches to
    # Check 4 neighbors
    neighbors = [
        (new_x - 1, new_y),
        (new_x + 1, new_y),
        (new_x, new_y - 1),
        (new_x, new_y + 1)
    ]
    
    attached_parent = None
    for nx, ny in neighbors:
        if 0 <= nx < w and 0 <= ny < h and cluster[ny, nx] == 1:
            try:
                attached_parent = nodes.index((nx, ny))
                break
            except ValueError:
                continue
                
    if attached_parent is not None:
        new_node_idx = len(nodes)
        nodes.append((new_x, new_y))
        parent[new_node_idx] = attached_parent
        cluster[new_y, new_x] = 1


def calculate_fractal_dimension():
    """
    Estimates fractal dimension using box counting on the cluster.
    """
    if len(nodes) < 10:
        return 1.0
    # Simple radius scaling estimation: count N(R) vs R
    h, w = GRID_H, GRID_W
    cy, cx = h // 2, w // 2
    y_indices, x_indices = np.indices((h, w))
    dist = np.sqrt((x_indices - cx)**2 + (y_indices - cy)**2)
    
    # N(R) = number of cluster nodes inside radius R
    radii = [10.0, 20.0, 30.0, 40.0, 50.0]
    counts = []
    for r in radii:
        counts.append(np.sum(cluster & (dist < r)))
        
    # Fit log(N) vs log(R)
    log_r = np.log(radii)
    log_n = np.log(np.array(counts) + 1.0)
    
    # Linear fit
    slope, _ = np.polyfit(log_r, log_n, 1)
    return max(1.0, min(2.0, slope))


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 2, 5)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics: Solve Laplace and Grow Cluster ---
    # Perform multiple growth steps per frame to see development
    growth_per_frame = 2
    for _ in range(growth_per_frame):
        solve_laplace()
        grow_dbm(eta=2.2)
        
    # Calculate fractal dimension every 10 frames
    if py5.frame_count % 10 == 0:
        f_dim = calculate_fractal_dimension()
        fractal_dims.append(f_dim)
        if len(fractal_dims) > 300:
            fractal_dims.pop(0)
            
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rectangle
    py5.fill(2, 2, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Draw growth boundary guide circle
    py5.stroke(255, 255, 255, 6)
    py5.stroke_weight(1.5)
    py5.no_fill()
    py5.ellipse(py5.width // 2, py5.height // 2, py5.height - 100, py5.height - 100)
    
    # Map coordinates from grid (120x120) to output resolution
    scale_x = py5.width / GRID_W
    scale_y = py5.height / GRID_H
    
    py5.push_matrix()
    # Additive glow for branching filaments
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Draw branches
    for child, prnt in parent.items():
        if child == prnt:
            continue
        cx_grid, cy_grid = nodes[child]
        px_grid, py_grid = nodes[prnt]
        
        # Screen positions
        x1 = cx_grid * scale_x + scale_x / 2
        y1 = cy_grid * scale_y + scale_y / 2
        x2 = px_grid * scale_x + scale_x / 2
        y2 = py_grid * scale_y + scale_y / 2
        
        # Color gradient: base to tip (depth of node in tree)
        # Tip is newer nodes (high index), base is parent (low index)
        h = 180.0 + (child / max(1, len(nodes))) * 60.0  # Cyan to Purple-Blue
        # Probe tips flash with Lime Green
        if child > len(nodes) - 8:
            h = 90.0  # Lime
            py5.stroke(h, 95, 95, 220)
            py5.stroke_weight(5.0)
        else:
            py5.stroke(h, 85, 90, 140)
            py5.stroke_weight(3.0)
            
        py5.line(x1, y1, x2, y2)
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for HUD text
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD Overlay
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("LAPLACIAN BRANCHING DELTA // DIELECTRIC BREAKDOWN MODEL", 50, 50)
    py5.text(f"CLUSTER NODES: {len(nodes):04d} | RESOLUTION: 3840 x 2160 (4K)", 50, 85)
    py5.text(f"LAPLACE FIELD: GRID 120 x 120 | GROWTH EXPONENT (ETA): 2.20", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    current_f_dim = fractal_dims[-1] if len(fractal_dims) > 0 else 1.0
    py5.text(f"FRACTAL DIMENSION D_F: {current_f_dim:.3f}", SIZE[0] - 50, 85)
    
    # Fractal Dimension Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("FRACTAL DIMENSION HIST", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(0, 240, 255, 180)
    py5.begin_shape()
    for idx, val in enumerate(fractal_dims):
        xx = gx + idx * (graph_w / 300)
        # Normalize to fit graph box (val is between 1.0 and 2.0)
        yy = gy + graph_h - (val - 1.0) * (graph_h - 15) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Blank screen check
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
        
        # Save preview mid-frame (grab from screen buffer)
        py5.load_np_pixels()
        img_rgb_mid = py5.np_pixels[:, :, :3].copy()
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()

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

# Sketch Identification
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Size Setup
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Model Parameters (Barabási-Albert)
M_INIT = 5  # Initial fully-connected nodes
M_ATTACH = 3  # Edges per new node
N_MAX = 240  # Maximum nodes in network
GROW_EVERY = 4  # Grow network every N frames

# Force-Directed Layout Constants
K_REP = 4000.0  # Repulsion strength
K_ATT = 0.45  # Attraction strength along edges
DAMPING = 0.85  # Velocity damping factor
DT = 0.4  # Physics step delta

# State Variables
_adj = np.zeros((N_MAX, N_MAX), dtype=np.int8)
_pos = np.random.uniform(-50, 50, (N_MAX, 2)).astype(np.float32)
_vel = np.zeros((N_MAX, 2), dtype=np.float32)
_deg = np.zeros(N_MAX, dtype=np.int32)
_edges = []
_n = M_INIT

# Smoothed scaling state variables (to prevent scale jitter)
smoothed_center = np.array([0.0, 0.0], dtype=np.float32)
smoothed_span = 80.0


def initialize_network() -> None:
    """Create a fully-connected initial seed network arranged in a ring."""
    global _adj, _pos, _vel, _deg, _edges, _n, smoothed_center, smoothed_span
    _adj.fill(0)
    _pos = np.random.uniform(-40, 40, (N_MAX, 2)).astype(np.float32)
    _vel.fill(0.0)
    _deg.fill(0)
    _edges = []
    _n = M_INIT
    smoothed_center = np.array([0.0, 0.0], dtype=np.float32)
    smoothed_span = 80.0

    # Place seed nodes in a circle
    for i in range(M_INIT):
        ang = py5.TWO_PI * i / M_INIT
        _pos[i] = [np.cos(ang) * 35.0, np.sin(ang) * 35.0]

    # Connect all seed nodes
    for i in range(M_INIT):
        for j in range(i + 1, M_INIT):
            _adj[i, j] = _adj[j, i] = 1
            _deg[i] += 1
            _deg[j] += 1
            _edges.append((i, j))


def add_node() -> None:
    """Add one node to the network using Barabási-Albert preferential attachment."""
    global _n
    if _n >= N_MAX:
        return
    i = _n
    degrees = _deg[:_n].astype(np.float64)
    total_degree = degrees.sum()

    # Probability is proportional to degree
    probs = degrees / total_degree if total_degree > 0 else np.ones(_n) / _n

    targets = set()
    m = min(M_ATTACH, _n)
    attempts = 0
    while len(targets) < m and attempts < _n * 30:
        t = int(np.random.choice(_n, p=probs))
        targets.add(t)
        attempts += 1

    # Place new node near the center of its attachment targets with slight noise
    if targets:
        _pos[i] = _pos[list(targets)].mean(axis=0) + np.random.randn(2).astype(np.float32) * 20.0
    else:
        _pos[i] = np.random.uniform(-30, 30, 2).astype(np.float32)
    _vel[i] = 0.0

    # Attach edges
    for t in targets:
        _adj[i, t] = _adj[t, i] = 1
        _deg[i] += 1
        _deg[t] += 1
        _edges.append((min(i, t), max(i, t)))

    _n += 1


def layout_forces_step() -> None:
    """Compute one step of Fruchterman-Reingold spring layout dynamics."""
    n = _n
    if n < 2:
        return

    p = _pos[:n]
    v = _vel[:n]

    # Compute pairwise vectors and distances
    diff = p[:, np.newaxis, :] - p[np.newaxis, :, :]  # Shape: (n, n, 2)
    dist = np.sqrt((diff * diff).sum(axis=2) + 1.0)  # Shape: (n, n), +1.0 prevents division by zero
    unit = diff / dist[:, :, np.newaxis]  # Shape: (n, n, 2)

    # 1. Repulsion forces (all pairs push apart)
    rep = K_REP / (dist * dist)
    np.fill_diagonal(rep, 0.0)
    rep_force = (rep[:, :, np.newaxis] * unit).sum(axis=1)

    # 2. Attraction forces (edges pull together)
    adjacency_sub = _adj[:n, :n].astype(np.float32)
    att = K_ATT * dist * adjacency_sub
    att_force = (att[:, :, np.newaxis] * (-unit)).sum(axis=1)

    total_force = (rep_force + att_force).astype(np.float32)

    # Update velocities and positions
    v[:] = np.clip(v * DAMPING + total_force * DT, -35.0, 35.0)
    p[:] += v * DT

    _pos[:n] = p
    _vel[:n] = v


def setup() -> None:
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    initialize_network()
    py5.background(5, 6, 11)  # Cosmic obsidian background


def draw() -> None:
    global smoothed_center, smoothed_span

    # Network growth and physics updates
    if py5.frame_count % GROW_EVERY == 0:
        add_node()
    layout_forces_step()

    # Render translucent background overlay to keep motion trails
    py5.no_stroke()
    py5.fill(5, 6, 11, 20)  # Trail decay
    py5.rect(0, 0, py5.width, py5.height)

    n = _n
    if n == 0:
        return

    # Calculate scale dynamically but smoothly
    p = _pos[:n]
    lo, hi = p.min(axis=0), p.max(axis=0)
    span = (hi - lo).max()

    # Lerp center and span to smooth layout transition
    current_center = (lo + hi) * 0.5
    smoothed_center = smoothed_center * 0.95 + current_center * 0.05
    smoothed_span = smoothed_span * 0.95 + span * 0.05

    viz_s = (min(py5.width, py5.height) * 0.70) / (smoothed_span + 1e-4)
    cx, cy = py5.width * 0.5, py5.height * 0.5

    # Screen coordinates
    sx = (p[:, 0] - smoothed_center[0]) * viz_s + cx
    sy = (p[:, 1] - smoothed_center[1]) * viz_s + cy

    # Draw Edges (faded based on creation age)
    n_edges = len(_edges)
    for idx, (u, v) in enumerate(_edges):
        if u >= n or v >= n:
            continue
        # Color gradient based on edge index (earlier edges represent older core paths)
        edge_frac = idx / max(n_edges, 1)

        # Fades from Glacial Cyan (0, 229, 255) to Deep Indigo (40, 30, 90)
        r = int(0 * edge_frac + 40 * (1.0 - edge_frac))
        g = int(229 * edge_frac + 30 * (1.0 - edge_frac))
        b = int(255 * edge_frac + 90 * (1.0 - edge_frac))
        alpha = int(45 + edge_frac * 80)

        py5.stroke(r, g, b, alpha)
        py5.stroke_weight(1.0 + edge_frac * 2.5)
        py5.line(float(sx[u]), float(sy[u]), float(sx[v]), float(sy[v]))

    # Draw Nodes (size and color dictated by topological degree hierarchy)
    py5.no_stroke()
    max_deg = max(int(_deg[:n].max()), 1)
    t_norm = py5.frame_count / TOTAL_FRAMES

    for i in range(n):
        d = int(_deg[i])
        deg_frac = d / max_deg  # Normalized degree [0, 1]

        # Pulse animation factor for star flicker
        pulse = py5.noise(float(sx[i]) * 0.02, float(sy[i]) * 0.02, t_norm * 25.0)

        # Color mapping:
        # Hubs (High Degree) -> Radiant Magenta (#ff2a85 : 255, 42, 133)
        # Medium Degree -> Violet (#b356ff : 179, 86, 255)
        # Leaves (Low Degree) -> Glacial Cyan (#00e5ff : 0, 229, 255)
        if deg_frac > 0.5:
            # Interpolate between Violet and Magenta
            t_sub = (deg_frac - 0.5) * 2.0
            r = int(179 * (1.0 - t_sub) + 255 * t_sub)
            g = int(86 * (1.0 - t_sub) + 42 * t_sub)
            b = int(255 * (1.0 - t_sub) + 133 * t_sub)
        else:
            # Interpolate between Cyan and Violet
            t_sub = deg_frac * 2.0
            r = int(0 * (1.0 - t_sub) + 179 * t_sub)
            g = int(229 * (1.0 - t_sub) + 86 * t_sub)
            b = int(255 * (1.0 - t_sub) + 255 * t_sub)

        alpha = int((140 + deg_frac * 115) * (0.8 + 0.2 * pulse))
        size = (5.0 + np.sqrt(deg_frac) * 22.0) * (0.85 + 0.3 * pulse)

        # Concentric glow bloom layers
        py5.fill(r, g, b, int(25 * (0.7 + 0.3 * pulse)))
        py5.circle(float(sx[i]), float(sy[i]), size * 2.6)

        py5.fill(r, g, b, alpha)
        py5.circle(float(sx[i]), float(sy[i]), size)

    # Fail-safe check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Output frame saving
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Exit and compile
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot from the middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

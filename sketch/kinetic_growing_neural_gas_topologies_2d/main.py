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

# GNG Hyperparameters
EPS_B = 0.1  # Winner move fraction
EPS_N = 0.005  # Neighbor move fraction
LAMBDA = 40  # Steps between neuron insertions
MAX_AGE = 80  # Edge age limit
ALPHA = 0.5  # Error reduction on insertion
BETA = 0.0008  # Global error decay per step
MAX_NODES = 350  # Cap on neuron count
STEPS_PER_FRAME = 25

# State Variables
_nodes = []  # List of [x, y] positions
_errors = []  # List of error floats
_edges = {}  # Dict (i, j) -> age, where i < j
_step = 0


def sample_signal(t_norm: float) -> np.ndarray:
    """Sample a signal from a dynamic multi-center moving distribution."""
    choice = random.random()
    if choice < 0.4:
        # Attractor 1: Lissajous orbit
        cx = 0.5 + 0.26 * py5.sin(t_norm * py5.TWO_PI * 1.5)
        cy = 0.5 + 0.26 * py5.cos(t_norm * py5.TWO_PI * 2.2)
        r = 0.04
    elif choice < 0.8:
        # Attractor 2: Shifting counter-orbit
        cx = 0.5 + 0.24 * py5.cos(t_norm * py5.TWO_PI * 1.8 + 1.5)
        cy = 0.5 + 0.24 * py5.sin(t_norm * py5.TWO_PI * 1.1)
        r = 0.05
    else:
        # Attractor 3: Moving breathing ring
        center_x = 0.5 + 0.15 * py5.sin(t_norm * py5.TWO_PI * 0.9)
        center_y = 0.5 + 0.15 * py5.cos(t_norm * py5.TWO_PI * 0.9)
        angle = random.uniform(0, py5.TWO_PI)
        rad = 0.18 + 0.04 * py5.sin(t_norm * py5.TWO_PI * 3.0)
        cx = center_x + rad * np.cos(angle)
        cy = center_y + rad * np.sin(angle)
        r = 0.02

    # Add Gaussian noise around the chosen center
    x = cx + random.gauss(0, r)
    y = cy + random.gauss(0, r)

    # Keep coordinates strictly within [0.05, 0.95] boundary
    x = np.clip(x, 0.05, 0.95)
    y = np.clip(y, 0.05, 0.95)
    return np.array([x, y], dtype=np.float32)


def reset_gng() -> None:
    """Initialize GNG structure with two random nodes."""
    global _nodes, _errors, _edges, _step
    t_init = 0.0
    _nodes = [sample_signal(t_init).tolist(), sample_signal(t_init).tolist()]
    _errors = [0.0, 0.0]
    _edges = {}
    _step = 0


def gng_step(t_norm: float) -> None:
    """Execute one step of Fritzke's Growing Neural Gas algorithm."""
    global _step, _edges, _nodes, _errors

    signal = sample_signal(t_norm)

    # 1. Find the two nearest nodes
    pos = np.array(_nodes, dtype=np.float32)
    diffs = pos - signal
    dists = (diffs * diffs).sum(axis=1)
    if len(dists) < 2:
        return
    order = np.argsort(dists)
    b1, b2 = int(order[0]), int(order[1])

    # 2. Increment edge ages connected to winner
    to_remove = []
    for (i, j), age in list(_edges.items()):
        if i == b1 or j == b1:
            _edges[(i, j)] = age + 1
            if _edges[(i, j)] > MAX_AGE:
                to_remove.append((i, j))
    for e in to_remove:
        del _edges[e]

    # 3. Add or refresh the edge between winner and second-nearest
    key = (min(b1, b2), max(b1, b2))
    _edges[key] = 0

    # 4. Accumulate local reconstruction error
    _errors[b1] += float(dists[b1])

    # 5. Move winner and its direct topological neighbors towards signal
    _nodes[b1] = (np.array(_nodes[b1]) + EPS_B * (signal - np.array(_nodes[b1]))).tolist()
    neighbors_b1 = {j for (i, j) in _edges if i == b1} | {i for (i, j) in _edges if j == b1}
    for nb in neighbors_b1:
        _nodes[nb] = (np.array(_nodes[nb]) + EPS_N * (signal - np.array(_nodes[nb]))).tolist()

    # 6. Remove isolated nodes (no connected edges)
    connected = set()
    for i, j in _edges:
        connected.add(i)
        connected.add(j)
    to_del = [i for i in range(len(_nodes)) if i not in connected and i >= 2]
    for i in reversed(sorted(to_del)):
        _nodes.pop(i)
        _errors.pop(i)
        # Renumber the remaining edges
        new_edges = {}
        for (a, b), age in _edges.items():
            a2 = a - (a > i) if a != i else None
            b2 = b - (b > i) if b != i else None
            if a2 is not None and b2 is not None:
                new_edges[(min(a2, b2), max(a2, b2))] = age
        _edges = new_edges

    # 7. Decay errors globally
    for k in range(len(_errors)):
        _errors[k] *= 1.0 - BETA

    # 8. Periodically insert a new node
    if _step > 0 and _step % LAMBDA == 0 and len(_nodes) < MAX_NODES:
        q = int(np.argmax(_errors))
        neighbors_q = {j for (i, j) in _edges if i == q} | {i for (i, j) in _edges if j == q}
        if neighbors_q:
            # Find neighbor with largest error
            f = max(neighbors_q, key=lambda n: _errors[n])
            # Place new node in the middle
            new_pos = ((np.array(_nodes[q]) + np.array(_nodes[f])) * 0.5).tolist()
            new_idx = len(_nodes)
            _nodes.append(new_pos)
            _errors.append((_errors[q] + _errors[f]) * ALPHA)

            # Split edge q-f by deleting it and adding q-new and new-f
            key_qf = (min(q, f), max(q, f))
            if key_qf in _edges:
                del _edges[key_qf]
            _edges[(min(q, new_idx), max(q, new_idx))] = 0
            _edges[(min(f, new_idx), max(f, new_idx))] = 0

            # Reduce error of parents
            _errors[q] *= ALPHA
            _errors[f] *= ALPHA

    _step += 1


def map_to_screen(x: float, y: float) -> tuple[float, float]:
    """Map normalized [0, 1] coordinates to screen maintaining 1:1 aspect ratio centered."""
    cx = py5.width / 2.0 + (x - 0.5) * py5.height
    cy = y * py5.height
    return cx, cy


def setup() -> None:
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    reset_gng()
    py5.background(5, 7, 12)  # Obsidian dark background base


def draw() -> None:
    # Calculate current time normalized [0, 1]
    t_norm = py5.frame_count / TOTAL_FRAMES

    # Run internal GNG simulation steps
    for _ in range(STEPS_PER_FRAME):
        gng_step(t_norm)

    # Blend translucent black overlay to create motion blur trails
    py5.no_stroke()
    py5.fill(5, 7, 12, 16)
    py5.rect(0, 0, py5.width, py5.height)

    # Draw GNG Edges
    py5.stroke_cap(py5.ROUND)
    for (i, j), age in _edges.items():
        age_frac = age / MAX_AGE
        # Color transition: Neon Cyan/Teal (0, 229, 255) -> Deep Indigo/Purple (37, 48, 92)
        r = int(0 * (1 - age_frac) + 37 * age_frac)
        g = int(229 * (1 - age_frac) + 48 * age_frac)
        b = int(255 * (1 - age_frac) + 92 * age_frac)
        alpha = int(200 * (1.0 - age_frac * 0.8))

        py5.stroke(r, g, b, alpha)
        # Line weight fades with age
        py5.stroke_weight(1.5 + (1.0 - age_frac) * 3.5)

        x1, y1 = map_to_screen(_nodes[i][0], _nodes[i][1])
        x2, y2 = map_to_screen(_nodes[j][0], _nodes[j][1])
        py5.line(x1, y1, x2, y2)

    # Draw GNG Nodes (with glow Bloom and organic noise pulsing)
    max_err = max(_errors) if _errors else 1.0
    py5.no_stroke()
    for k, (nx, ny) in enumerate(_nodes):
        err_n = _errors[k] / (max_err + 1e-9)

        # Introduce an organic pulsing factor using 3D noise based on node position and time
        pulse = py5.noise(nx * 8.0, ny * 8.0, t_norm * 20.0)

        # Color: Low error (Cyan) -> High error (Solar Gold: 255, 213, 79)
        r = int((1 - err_n) * 0 + err_n * 255)
        g = int((1 - err_n) * 229 + err_n * 213)
        b = int((1 - err_n) * 255 + err_n * 79)
        alpha = int((170 + err_n * 85) * (0.75 + 0.25 * pulse))

        cx, cy = map_to_screen(nx, ny)
        size = (5.0 + err_n * 15.0) * (0.8 + 0.4 * pulse)

        # Bloom glow outer circle
        py5.fill(r, g, b, int(35 * (0.7 + 0.3 * pulse)))
        py5.circle(cx, cy, size * 2.5)

        # Solid inner circle
        py5.fill(r, g, b, alpha)
        py5.circle(cx, cy, size)

    # Fail-safe check for blank screen aborting
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Output frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Render Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    # Finalization and compilation
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

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)  # Force exit to prevent macOS JVM/AWT hangs


if __name__ == "__main__":
    py5.run_sketch()

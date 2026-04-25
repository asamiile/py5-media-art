from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Clifford attractor parameters — produces a dense, intricate structure
A, B, C, D = -1.7, 1.3, -0.1, -1.2

N_TRAJ  = 2000   # parallel trajectories (vectorized)
N_STEPS = 1200   # steps per trajectory
BURN_IN = 200    # discard initial steps until convergence


def setup():
    py5.size(*SIZE)

    # Vectorized multi-trajectory generation — fast and produces ~2M points
    rng = np.random.default_rng()
    x = rng.uniform(-0.2, 0.2, N_TRAJ)
    y = rng.uniform(-0.2, 0.2, N_TRAJ)

    chunks_x, chunks_y = [], []
    for step in range(N_STEPS):
        xn = np.sin(A * y) + C * np.cos(A * x)
        yn = np.sin(B * x) + D * np.cos(B * y)
        x, y = xn, yn
        if step >= BURN_IN:
            chunks_x.append(x)
            chunks_y.append(y)

    xs = np.concatenate(chunks_x)
    ys = np.concatenate(chunks_y)

    # Use actual pixel buffer dimensions (2x on Retina)
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    margin = 100

    px = ((xs - xs.min()) / (xs.max() - xs.min()) * (w - 2 * margin) + margin).astype(np.int32)
    py_arr = ((ys - ys.min()) / (ys.max() - ys.min()) * (h - 2 * margin) + margin).astype(np.int32)
    np.clip(px, 0, w - 1, out=px)
    np.clip(py_arr, 0, h - 1, out=py_arr)

    density = np.zeros((h, w), dtype=np.float32)
    np.add.at(density, (py_arr, px), 1.0)

    d = np.log1p(density)
    d /= d.max()

    # High-contrast palette: black → deep purple → orange → bright yellow-white
    r = (d * 255 + d ** 0.5 * 80 - 30).clip(0, 255).astype(np.uint8)
    g = (d ** 1.5 * 200).clip(0, 255).astype(np.uint8)
    b = (d * 120 * (1 - d)).clip(0, 255).astype(np.uint8)
    alpha = np.full((h, w), 255, dtype=np.uint8)

    py5.np_pixels[:, :, 0] = alpha
    py5.np_pixels[:, :, 1] = r
    py5.np_pixels[:, :, 2] = g
    py5.np_pixels[:, :, 3] = b
    py5.update_np_pixels()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

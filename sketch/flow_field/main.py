from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 500

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Theme: "Signal degrading" — structured center attractor, chaos at edges
N_PARTICLES = 150000
SPEED = 2.0

# Teal at high density (center); crimson at low density (edges)
TEAL    = np.array([0.157, 0.769, 0.659], dtype=np.float64)  # #28c4a8
CRIMSON = np.array([0.478, 0.188, 0.251], dtype=np.float64)  # #7a3040

particles = None
density   = None


def flow_angle(x, y):
    cx, cy = SIZE[0] / 2.0, SIZE[1] / 2.0
    dx = x - cx
    dy = y - cy
    # Inward spiral: angle toward center + slight rotation
    toward_center = np.arctan2(-dy, -dx)
    r_norm = np.sqrt((dx / cx) ** 2 + (dy / cy) ** 2)
    # Perturbation grows with radius — structured center, chaos at edge
    perturb = np.sin(x / 120.0 + y / 80.0) * np.pi * r_norm ** 1.8
    return toward_center + 0.3 + perturb


def setup():
    global particles, density
    py5.size(*SIZE)
    particles = np.random.rand(N_PARTICLES, 2) * np.array([SIZE[0], SIZE[1]])
    density = np.zeros((SIZE[1], SIZE[0]), dtype=np.float64)


def draw():
    global particles, density

    angle = flow_angle(particles[:, 0], particles[:, 1])
    cx, cy = SIZE[0] / 2.0, SIZE[1] / 2.0
    r_norm = np.sqrt(((particles[:, 0] - cx) / cx) ** 2 + ((particles[:, 1] - cy) / cy) ** 2)
    jitter = r_norm * 1.2

    vx = np.cos(angle) * SPEED + np.random.randn(N_PARTICLES) * jitter
    vy = np.sin(angle) * SPEED + np.random.randn(N_PARTICLES) * jitter

    # Wrap-around
    particles[:, 0] = (particles[:, 0] + vx) % SIZE[0]
    particles[:, 1] = (particles[:, 1] + vy) % SIZE[1]

    xi = particles[:, 0].astype(np.int32) % SIZE[0]
    yi = particles[:, 1].astype(np.int32) % SIZE[1]
    flat = yi * SIZE[0] + xi
    total = SIZE[0] * SIZE[1]

    counts = np.bincount(flat, minlength=total).reshape(SIZE[1], SIZE[0]).astype(np.float64)

    # Slow decay to accumulate structure
    density = density * 0.992 + counts

    log_d = np.log1p(density * 60.0)
    max_d = log_d.max()

    if max_d > 0:
        d_norm = log_d / max_d  # 0 at dark edges, 1 at bright center

        # Color: TEAL where dense, CRIMSON where sparse but visible
        r_out = d_norm * TEAL[0] + (1 - d_norm) * CRIMSON[0]
        g_out = d_norm * TEAL[1] + (1 - d_norm) * CRIMSON[1]
        b_out = d_norm * TEAL[2] + (1 - d_norm) * CRIMSON[2]

        r_px = np.clip(r_out * d_norm * 255, 0, 255).astype(np.uint8)
        g_px = np.clip(g_out * d_norm * 255, 0, 255).astype(np.uint8)
        b_px = np.clip(b_out * d_norm * 255, 0, 255).astype(np.uint8)
    else:
        r_px = g_px = b_px = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)

    display = np.stack([r_px, g_px, b_px], axis=-1)
    alpha = np.full((SIZE[1], SIZE[0], 1), 255, dtype=np.uint8)
    argb = np.concatenate([alpha, display], axis=-1)

    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = argb
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(argb, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

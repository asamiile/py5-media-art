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
PREVIEW_FRAME = 60

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

MAX_ITER = 256
C = complex(-0.7269, 0.1889)  # Douady rabbit — intricate spiral dendrites

pixels = None


def compute_julia(width, height):
    aspect = width / height
    x = np.linspace(-1.4 * aspect, 1.4 * aspect, width)
    y = np.linspace(-1.4, 1.4, height)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    smooth = np.zeros(Z.shape, dtype=np.float64)
    active = np.ones(Z.shape, dtype=bool)

    for i in range(MAX_ITER):
        Z[active] = Z[active] ** 2 + C
        escaped = active & (np.abs(Z) > 2.0)
        if escaped.any():
            log_abs = np.log(np.abs(Z[escaped]))
            smooth[escaped] = i + 1.0 - np.log(log_abs) / np.log(2.0)
        active[escaped] = False

    return smooth


def smooth_to_rgb(smooth):
    interior = smooth == 0.0
    exterior = ~interior

    # Cycle through rich palette based on smooth value
    t = np.zeros_like(smooth)
    t[exterior] = (smooth[exterior] * 0.06) % 1.0

    # Three sine waves offset by 2π/3 — produces full-spectrum cycling
    r = np.clip(np.sin(t * np.pi * 2 + 0.0) * 127.5 + 127.5, 0, 255)
    g = np.clip(np.sin(t * np.pi * 2 + 2.094) * 127.5 + 127.5, 0, 255)
    b = np.clip(np.sin(t * np.pi * 2 + 4.189) * 127.5 + 127.5, 0, 255)

    # Boost near-boundary glow: high-frequency smooth values → brighter
    glow = np.clip(np.sin(smooth * 0.8) * 0.5 + 0.5, 0, 1)
    r = np.clip(r * (0.6 + 0.4 * glow), 0, 255)
    g = np.clip(g * (0.6 + 0.4 * glow), 0, 255)
    b = np.clip(b * (0.6 + 0.4 * glow), 0, 255)

    # Deep midnight blue interior
    r[interior] = 4
    g[interior] = 6
    b[interior] = 20

    alpha = np.full(smooth.shape, 255, dtype=np.uint8)
    return np.stack([alpha, r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8)], axis=-1)


def setup():
    global pixels
    py5.size(*SIZE)
    smooth = compute_julia(SIZE[0], SIZE[1])
    pixels = smooth_to_rgb(smooth)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels
    else:
        # Retina display: buffer is 2× SIZE
        py5.np_pixels[:] = np.repeat(np.repeat(pixels, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename, save_preview_pil
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def spectral_lattice_field(rng, cols=34, rows=20):
    n = cols * rows
    xs = np.linspace(-1.0, 1.0, cols)
    ys = np.linspace(-1.0, 1.0, rows)
    gx, gy = np.meshgrid(xs, ys)
    points = np.column_stack([gx.ravel(), gy.ravel()])
    points += rng.normal(0.0, 0.018, points.shape)

    adjacency = np.zeros((n, n), dtype=np.float32)
    for y in range(rows):
        for x in range(cols):
            idx = y * cols + x
            for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
                nx = x + dx
                ny = y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    j = ny * cols + nx
                    d = np.linalg.norm(points[idx] - points[j])
                    w = np.exp(-(d * 4.8) ** 2) * rng.uniform(0.65, 1.25)
                    adjacency[idx, j] = w
                    adjacency[j, idx] = w

    degrees = np.sum(adjacency, axis=1)
    laplacian = np.diag(degrees) - adjacency
    vals, vecs = np.linalg.eigh(laplacian)

    modes = []
    for mode_idx in (3, 5, 8, 13, 21):
        v = vecs[:, min(mode_idx, vecs.shape[1] - 1)]
        v = (v - v.min()) / (v.max() - v.min() + 1e-6)
        modes.append(v.reshape(rows, cols))
    return np.array(modes, dtype=np.float32)


def bilinear_resize(field, width, height):
    src_h, src_w = field.shape
    x = np.linspace(0, src_w - 1, width, dtype=np.float32)
    y = np.linspace(0, src_h - 1, height, dtype=np.float32)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, src_w - 1)
    y1 = np.clip(y0 + 1, 0, src_h - 1)
    tx = x - x0
    ty = y - y0

    top = field[y0[:, None], x0[None, :]] * (1.0 - tx)[None, :] + field[y0[:, None], x1[None, :]] * tx[None, :]
    bottom = field[y1[:, None], x0[None, :]] * (1.0 - tx)[None, :] + field[y1[:, None], x1[None, :]] * tx[None, :]
    return top * (1.0 - ty)[:, None] + bottom * ty[:, None]


def add_color(img, mask, color, gain):
    img += np.clip(mask, 0.0, 1.0)[..., None] * np.array(color, dtype=np.float32) * gain


def render_eigenveil():
    width, height = SIZE
    rng = np.random.default_rng()
    modes = spectral_lattice_field(rng)

    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height
    radius = np.sqrt(nx * nx + ny * ny)

    field = np.zeros((height, width), dtype=np.float32)
    weights = rng.uniform(-1.25, 1.25, len(modes))
    for mode, weight in zip(modes, weights):
        field += bilinear_resize(mode, width, height) * weight

    drift = (
        0.18 * np.sin(nx * 19.0 + ny * 7.0 + rng.uniform(0, np.pi * 2))
        + 0.12 * np.sin(nx * -8.0 + ny * 29.0 + rng.uniform(0, np.pi * 2))
        + 0.08 * np.cos((nx + ny) * 41.0 + rng.uniform(0, np.pi * 2))
    )
    field += drift
    field = (field - field.min()) / (field.max() - field.min() + 1e-6)

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([5, 7, 12], dtype=np.float32)
    img += np.clip(1.08 - radius * 1.15, 0.0, 1.0)[..., None] * np.array([7, 15, 23], dtype=np.float32)

    bands = np.abs(np.mod(field * 18.0, 1.0) - 0.5) * 2.0
    thread = smoothstep(0.83, 0.98, 1.0 - bands)
    broad = smoothstep(0.58, 0.82, 1.0 - bands)

    oblique = np.sin((nx * 0.9 - ny * 1.6) * 92.0 + field * 5.5)
    weave = 0.42 + 0.58 * smoothstep(-0.35, 0.9, oblique)
    gaps = smoothstep(0.16, 0.56, np.sin(x * 0.027 + field * 9.0) * np.sin(y * 0.019 - field * 7.0))
    veil = thread * weave * (0.42 + 0.58 * gaps)

    edge_x = np.gradient(field, axis=1)
    edge_y = np.gradient(field, axis=0)
    slope = np.sqrt(edge_x * edge_x + edge_y * edge_y)
    stress = smoothstep(np.percentile(slope, 78), np.percentile(slope, 98), slope)

    add_color(img, broad * 0.28, (42, 136, 146), 0.72)
    add_color(img, veil, (85, 224, 217), 0.94)
    add_color(img, thread * (1.0 - weave) * 0.9, (134, 92, 198), 0.82)
    add_color(img, stress * thread, (235, 170, 80), 0.86)

    # Small amber pinpoints mark local spectral tensions without turning the piece into a node graph.
    candidate = (stress > 0.7) & (thread > 0.55)
    ys, xs = np.where(candidate)
    if len(xs) > 0:
        pick = rng.choice(len(xs), size=min(280, len(xs)), replace=False)
        for px, py in zip(xs[pick], ys[pick]):
            rr = rng.integers(2, 5)
            y0, y1 = max(0, py - rr), min(height, py + rr + 1)
            x0, x1 = max(0, px - rr), min(width, px + rr + 1)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            dot = np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (rr * rr * 0.7))
            img[y0:y1, x0:x1, 0] += dot * 86
            img[y0:y1, x0:x1, 1] += dot * 54
            img[y0:y1, x0:x1, 2] += dot * 14

    img += rng.normal(0.0, 2.2, img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_eigenveil()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()

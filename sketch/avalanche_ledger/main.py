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


def relax_sandpile(grid, max_steps=5200):
    heat = np.zeros_like(grid, dtype=np.float32)
    for _ in range(max_steps):
        topple = grid // 4
        if not np.any(topple):
            break
        grid = grid % 4
        heat += (topple > 0).astype(np.float32)
        grid[:-1, :] += topple[1:, :]
        grid[1:, :] += topple[:-1, :]
        grid[:, :-1] += topple[:, 1:]
        grid[:, 1:] += topple[:, :-1]
        grid[0, :] = np.minimum(grid[0, :], 3)
        grid[-1, :] = np.minimum(grid[-1, :], 3)
        grid[:, 0] = np.minimum(grid[:, 0], 3)
        grid[:, -1] = np.minimum(grid[:, -1], 3)
    while np.any(grid >= 4):
        topple = grid // 4
        grid = grid % 4
        heat += (topple > 0).astype(np.float32)
        grid[:-1, :] += topple[1:, :]
        grid[1:, :] += topple[:-1, :]
        grid[:, :-1] += topple[:, 1:]
        grid[:, 1:] += topple[:, :-1]
        grid[0, :] = np.minimum(grid[0, :], 3)
        grid[-1, :] = np.minimum(grid[-1, :], 3)
        grid[:, 0] = np.minimum(grid[:, 0], 3)
        grid[:, -1] = np.minimum(grid[:, -1], 3)
    return grid, heat


def upscale_nearest(img, width, height):
    src_h, src_w = img.shape[:2]
    y = (np.linspace(0, src_h, height, endpoint=False)).astype(np.int32)
    x = (np.linspace(0, src_w, width, endpoint=False)).astype(np.int32)
    return img[y[:, None], x[None, :]]


def render_avalanche_ledger():
    width, height = SIZE
    rng = np.random.default_rng()
    gw, gh = 480, 270
    grid = np.zeros((gh, gw), dtype=np.int32)

    cx = gw // 2 + rng.integers(-30, 31)
    cy = gh // 2 + rng.integers(-18, 19)
    grid[cy, cx] = rng.integers(260_000, 360_000)

    for _ in range(11):
        px = int(np.clip(rng.normal(cx, gw * 0.20), 16, gw - 17))
        py = int(np.clip(rng.normal(cy, gh * 0.20), 16, gh - 17))
        grid[py, px] += rng.integers(18_000, 58_000)

    residue, heat = relax_sandpile(grid)
    heat = np.log1p(heat)
    heat = heat / (heat.max() + 1e-6)

    palette = np.array(
        [
            [8, 10, 18],
            [34, 74, 92],
            [144, 73, 138],
            [234, 167, 76],
        ],
        dtype=np.float32,
    )
    img = palette[residue].astype(np.float32)

    edge_h = np.zeros_like(heat)
    edge_h[:, 1:] += residue[:, 1:] != residue[:, :-1]
    edge_h[1:, :] += residue[1:, :] != residue[:-1, :]
    edge = np.clip(edge_h, 0, 1).astype(np.float32)

    img += heat[..., None] * np.array([16, 36, 48], dtype=np.float32)
    img += edge[..., None] * np.array([48, 86, 94], dtype=np.float32)

    # Diagonal audit marks make the avalanche feel recorded rather than decorative.
    yy, xx = np.mgrid[0:gh, 0:gw]
    hatch = (((xx + yy * 2) % 17) == 0).astype(np.float32)
    hatch *= (heat > 0.26) & (residue == 0)
    img += hatch[..., None] * np.array([34, 42, 52], dtype=np.float32)

    big = upscale_nearest(np.clip(img, 0, 255).astype(np.uint8), width, height).astype(np.float32)

    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height
    vignette = np.clip(np.sqrt(nx * nx + ny * ny) * 1.16, 0.0, 1.0)
    big *= 1.0 - vignette[..., None] * 0.36
    big += rng.normal(0, 1.4, big.shape).astype(np.float32)
    return np.clip(big, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_avalanche_ledger()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()

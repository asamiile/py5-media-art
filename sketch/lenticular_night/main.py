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


def add_layer(img, mask, color, strength=1.0):
    img += np.clip(mask, 0.0, 1.0)[..., None] * np.array(color, dtype=np.float32) * strength


def render_lenticular_night():
    width, height = SIZE
    rng = np.random.default_rng()

    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height
    radius = np.sqrt(nx * nx + ny * ny)

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([4, 6, 13], dtype=np.float32)
    img += np.clip(1.15 - radius * 1.35, 0.0, 1.0)[..., None] * np.array([7, 13, 25], dtype=np.float32)

    phase = rng.uniform(0, np.pi * 2, 6)
    warp_a = 0.10 * np.sin(nx * 5.8 + ny * 2.4 + phase[0]) + 0.04 * np.sin(ny * 19.0 + phase[1])
    warp_b = 0.08 * np.cos(nx * -4.4 + ny * 7.5 + phase[2]) + 0.035 * np.sin((nx - ny) * 23.0 + phase[3])
    warp_c = 0.06 * np.sin(radius * 24.0 + nx * 4.0 + phase[4])

    stripe_pitch = rng.uniform(7.0, 10.0)
    slant = rng.uniform(-0.22, 0.22)
    carrier = x + y * slant + (warp_a + warp_b) * 180.0
    stripe_phase = np.mod(carrier / stripe_pitch, 1.0)

    masks = []
    for offset in (0.0, 1.0 / 3.0, 2.0 / 3.0):
        d = np.abs(np.mod(stripe_phase - offset + 0.5, 1.0) - 0.5)
        masks.append(smoothstep(0.21, 0.02, d))

    ghost_grid = (
        np.sin((nx + warp_a) * 31.0 + phase[0])
        * np.sin((ny + warp_b) * 21.0 + phase[1])
    )
    aperture = smoothstep(0.18, 0.88, ghost_grid)

    contour = np.abs(np.mod((nx * 2.3 - ny * 1.4 + warp_c) * 9.5, 1.0) - 0.5) * 2.0
    contour = smoothstep(0.76, 0.98, 1.0 - contour)

    diagonal = np.abs(np.sin((nx * 0.82 + ny * 1.55 + warp_a) * 58.0))
    diagonal = smoothstep(0.87, 0.995, diagonal)

    vertical = np.abs(np.sin((nx + warp_b) * 96.0 + phase[5]))
    vertical = smoothstep(0.91, 0.995, vertical)

    add_layer(img, masks[0] * aperture, (45, 218, 226), 0.74)
    add_layer(img, masks[1] * contour, (202, 92, 146), 0.68)
    add_layer(img, masks[2] * diagonal, (238, 194, 104), 0.56)
    add_layer(img, (masks[0] * vertical) ** 1.4, (156, 226, 244), 0.88)

    moire = np.abs(np.sin(carrier * 0.54 + np.sin(ny * 18.0) * 3.0))
    moire = smoothstep(0.92, 0.998, moire) * smoothstep(0.05, 0.76, radius)
    add_layer(img, moire, (42, 76, 94), 0.44)

    # Thin black separators keep the optical construction crisp.
    separator = smoothstep(0.43, 0.50, np.abs(stripe_phase - 0.5))
    img *= 0.76 + 0.24 * separator[..., None]

    for _ in range(120):
        cx = rng.integers(0, width)
        cy = rng.integers(0, height)
        length = rng.integers(24, 110)
        yy = slice(max(0, cy - 1), min(height, cy + 2))
        xx = slice(cx, min(width, cx + length))
        if xx.start < xx.stop:
            tint = rng.choice(
                np.array([[52, 225, 230], [226, 116, 156], [236, 198, 112]], dtype=np.float32)
            )
            fade = np.linspace(1.0, 0.0, xx.stop - xx.start, dtype=np.float32)
            img[yy, xx] += fade[None, :, None] * tint * rng.uniform(0.08, 0.22)

    img *= (1.0 - np.clip(radius * 1.08 - 0.18, 0.0, 1.0)[..., None] * 0.32)
    img += rng.normal(0.0, 2.1, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_lenticular_night()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()

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


def add_rgb(img, mask, color, gain=1.0):
    img += np.clip(mask, 0.0, 1.0)[..., None] * np.array(color, dtype=np.float32) * gain


def render_redaction_current():
    width, height = SIZE
    rng = np.random.default_rng()
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([6, 7, 10], dtype=np.float32)

    redacted = np.zeros((height, width), dtype=np.float32)
    edge = np.zeros_like(redacted)
    blocks = []
    for row in range(15):
        base_y = int((row + 0.55) * height / 16 + rng.normal(0, 7))
        cursor = rng.integers(-120, 80)
        while cursor < width - 40:
            w = int(rng.integers(120, 420))
            h = int(rng.integers(14, 42))
            gap = int(rng.integers(28, 120))
            x0 = max(0, cursor)
            x1 = min(width, cursor + w)
            y0 = max(0, base_y - h // 2)
            y1 = min(height, base_y + h // 2)
            if x1 > x0 and rng.random() < 0.78:
                blocks.append((x0, y0, x1, y1))
                redacted[y0:y1, x0:x1] = 1.0
                edge[max(0, y0 - 2):min(height, y0 + 2), x0:x1] = 1.0
                edge[max(0, y1 - 2):min(height, y1 + 2), x0:x1] = 1.0
                edge[y0:y1, max(0, x0 - 2):min(width, x0 + 2)] = 1.0
                edge[y0:y1, max(0, x1 - 2):min(width, x1 + 2)] = 1.0
            cursor += w + gap

    carrier = (
        np.sin((nx * 4.8 + ny * 1.7) * 18.0)
        + 0.55 * np.sin((nx * -2.1 + ny * 5.3) * 15.0)
        + 0.35 * np.sin((nx + ny) * 73.0)
    )
    field = smoothstep(0.68, 0.98, np.abs(carrier))

    scan = np.abs(np.sin(y * 0.71 + carrier * 2.3))
    scan = smoothstep(0.89, 0.995, scan)
    leak = field * (1.0 - redacted * 0.76)
    add_rgb(img, leak * scan, (54, 224, 232), 0.78)
    add_rgb(img, field * edge, (224, 94, 146), 0.68)

    # Current bends around each redaction block as a luminous wake.
    wake = np.zeros_like(redacted)
    for x0, y0, x1, y1 in blocks:
        sx = slice(max(0, x0 - 28), min(width, x1 + 84))
        sy = slice(max(0, y0 - 32), min(height, y1 + 32))
        local_x = x[sy, sx]
        local_y = y[sy, sx]
        dx = np.maximum(np.maximum(x0 - local_x, local_x - x1), 0)
        dy = np.maximum(np.maximum(y0 - local_y, local_y - y1), 0)
        dist = np.sqrt(dx * dx + dy * dy)
        downstream = smoothstep(x0 - 20, x1 + 90, local_x)
        wake[sy, sx] += np.exp(-(dist / 18.0) ** 2) * downstream
    add_rgb(img, smoothstep(0.28, 1.3, wake) * (1.0 - redacted), (226, 172, 84), 0.42)

    img *= 1.0 - redacted[..., None] * 0.82
    img += redacted[..., None] * np.array([2, 2, 3], dtype=np.float32)
    add_rgb(img, edge, (36, 42, 48), 0.34)

    # Ghost text baselines without legible text.
    for _ in range(240):
        yy = rng.integers(24, height - 24)
        xx = rng.integers(0, width - 80)
        ln = rng.integers(18, 92)
        alpha = rng.uniform(0.025, 0.11)
        img[yy:yy + 1, xx:xx + ln] += np.array([82, 102, 118], dtype=np.float32) * alpha

    radius = np.sqrt(nx * nx + ny * ny)
    img *= (1.0 - np.clip(radius * 1.08 - 0.18, 0.0, 1.0)[..., None] * 0.34)
    img += rng.normal(0.0, 2.1, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_redaction_current()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()

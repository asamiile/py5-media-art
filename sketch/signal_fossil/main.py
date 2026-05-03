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


def add_glow_rgb(img, field, color, strength):
    glow = np.clip(field, 0.0, 1.0)[..., None]
    img += glow * np.array(color, dtype=np.float32) * strength


def render_signal_fossil():
    width, height = SIZE
    rng = np.random.default_rng()

    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / height
    ny = (y - height * 0.5) / height
    radius = np.sqrt(nx * nx + ny * ny)

    img = np.zeros((height, width, 3), dtype=np.float32)
    img[:] = np.array([4, 6, 12], dtype=np.float32)

    vignette = np.clip(1.15 - radius * 1.25, 0.0, 1.0)
    img += vignette[..., None] * np.array([9, 14, 26], dtype=np.float32)

    carrier = np.zeros((height, width), dtype=np.float32)
    fracture = np.zeros_like(carrier)
    phase_base = rng.uniform(0.0, np.pi * 2.0, 12)

    for i in range(12):
        angle = rng.uniform(-0.85, 0.85) + (i - 5.5) * 0.035
        ca, sa = np.cos(angle), np.sin(angle)
        rx = nx * ca + ny * sa
        ry = -nx * sa + ny * ca
        cx = rng.uniform(-0.42, 0.42)
        cy = rng.uniform(-0.22, 0.22)
        sx = rng.uniform(0.13, 0.36)
        sy = rng.uniform(0.03, 0.12)
        freq = rng.uniform(58.0, 128.0)
        envelope = np.exp(-(((rx - cx) / sx) ** 2 + ((ry - cy) / sy) ** 2))
        wave = np.cos(freq * rx + phase_base[i])
        carrier += envelope * wave * rng.uniform(0.65, 1.15)

        crack_freq = rng.uniform(12.0, 26.0)
        fracture += envelope * np.sin(crack_freq * (rx * 0.65 + ry * 1.35) + phase_base[i] * 0.7)

    fault = (
        np.sin(nx * 42.0 + ny * 8.0 + phase_base[0])
        + 0.55 * np.sin(nx * -18.0 + ny * 37.0 + phase_base[1])
        + 0.35 * np.sin((nx + ny) * 71.0 + phase_base[2])
    )
    packet = np.abs(carrier)
    contour = smoothstep(0.74, 0.96, 1.0 - np.abs(np.mod(packet * 5.6 + fault * 0.18, 1.0) - 0.5) * 2.0)
    contour *= smoothstep(0.04, 0.58, packet)

    # Erase the smooth signal into broken technological strata.
    tile_x = (x // rng.integers(18, 34)).astype(np.int32)
    tile_y = (y // rng.integers(10, 22)).astype(np.int32)
    packet_dropout = ((tile_x * 37 + tile_y * 71 + rng.integers(0, 1000)) % 11) / 11.0
    dropout = smoothstep(0.18, 0.78, packet_dropout + 0.18 * np.sin(fault * 2.4))
    contour *= dropout

    edge = smoothstep(0.62, 0.94, np.abs(fracture + fault * 0.42))
    edge *= smoothstep(0.08, 0.7, packet)
    scan = (0.35 + 0.65 * smoothstep(-0.2, 0.75, np.sin(y * 0.73 + fault * 1.8)))
    contour *= scan

    amber = (255, 178, 72)
    cyan = (47, 220, 235)
    violet = (166, 86, 255)
    rose = (255, 78, 145)

    add_glow_rgb(img, contour ** 1.8, cyan, 0.92)
    add_glow_rgb(img, np.clip(contour * edge, 0.0, 1.0), amber, 1.22)
    add_glow_rgb(img, smoothstep(0.66, 1.0, packet) * (1.0 - dropout) * 0.78, violet, 0.58)

    hot = smoothstep(0.90, 1.0, contour + edge * 0.28)
    add_glow_rgb(img, hot, rose, 1.08)

    # Thin vertical recovery ticks suggest a damaged broadcast being reconstructed.
    columns = rng.choice(width, size=46, replace=False)
    for col in columns:
        col_w = rng.integers(1, 4)
        start = rng.integers(int(height * 0.06), int(height * 0.76))
        length = rng.integers(int(height * 0.10), int(height * 0.45))
        sl = slice(max(0, col - col_w), min(width, col + col_w + 1))
        ys = slice(start, min(height, start + length))
        pulse = np.linspace(1.0, 0.0, ys.stop - ys.start, dtype=np.float32)[:, None]
        img[ys, sl, 0] += pulse * rng.uniform(40, 90)
        img[ys, sl, 1] += pulse * rng.uniform(120, 230)
        img[ys, sl, 2] += pulse * rng.uniform(150, 255)

    grain = rng.normal(0.0, 3.0, img.shape).astype(np.float32)
    img += grain
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    img = render_signal_fossil()
    save_preview_pil(img, SKETCH_DIR, filename=PREVIEW_FILENAME)
    py5.exit_sketch()


if __name__ == "__main__":
    py5.run_sketch()

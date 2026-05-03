from pathlib import Path
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 1
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

CENTERS = []


def setup():
    global CENTERS
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.smooth(8)
    py5.background(5, 7, 14)
    py5.no_loop()

    rng = np.random.default_rng()
    CENTERS = [
        (
            rng.uniform(-0.78, 0.78),
            rng.uniform(-0.42, 0.42),
            rng.uniform(-0.18, 0.22),
            rng.uniform(0.08, 0.26),
            rng.uniform(-1.0, 1.0),
        )
        for _ in range(7)
    ]


def warp_point(x, y):
    wx = x
    wy = y
    for cx, cy, amp, sigma, twist in CENTERS:
        dx = x - cx
        dy = y - cy
        r2 = dx * dx + dy * dy
        g = np.exp(-r2 / (2.0 * sigma * sigma))
        wx += amp * g * (-dy * twist + dx * 0.35)
        wy += amp * g * (dx * twist + dy * 0.35)
    wx += 0.035 * np.sin(9.0 * y + 3.5 * np.sin(4.0 * x))
    wy += 0.028 * np.sin(8.0 * x - 2.5 * np.cos(5.0 * y))
    return wx, wy


def jacobian(x, y, eps=0.003):
    x1, y1 = warp_point(x + eps, y)
    x2, y2 = warp_point(x - eps, y)
    x3, y3 = warp_point(x, y + eps)
    x4, y4 = warp_point(x, y - eps)
    return np.array(
        [
            [(x1 - x2) / (2 * eps), (x3 - x4) / (2 * eps)],
            [(y1 - y2) / (2 * eps), (y3 - y4) / (2 * eps)],
        ],
        dtype=np.float32,
    )


def screen_xy(x, y):
    width, height = SIZE
    return width * (0.5 + y * 0.0 + x * height / width), height * (0.5 + y)


def color_mix(a, b, t):
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def draw_background():
    width, height = SIZE
    for yy in range(0, height, 3):
        t = yy / height
        r = 5 + 10 * t
        g = 7 + 11 * t
        b = 14 + 24 * t
        py5.stroke(r, g, b)
        py5.line(0, yy, width, yy)


def draw_warped_family(horizontal=True):
    base_color = (88, 152, 188) if horizontal else (82, 106, 162)
    accent = (246, 140, 108) if horizontal else (222, 190, 112)
    count = 38 if horizontal else 60
    span = np.linspace(-0.58, 0.58, count) if horizontal else np.linspace(-1.05, 1.05, count)
    py5.no_fill()
    for i, c in enumerate(span):
        points = []
        for t in np.linspace(-1.05, 1.05, 150):
            x, y = (t, c) if horizontal else (c, t * 0.58)
            wx, wy = warp_point(x, y)
            sx, sy = screen_xy(wx, wy)
            points.append((sx, sy))

        intensity = 0.25 + 0.75 * (i / max(1, count - 1))
        col = color_mix(base_color, accent, 0.18 + 0.26 * np.sin(i * 0.67) ** 2)
        py5.stroke(*col, 46 + 62 * intensity)
        py5.stroke_weight(1.15 if horizontal else 0.85)
        py5.begin_shape()
        for sx, sy in points:
            py5.curve_vertex(sx, sy)
        py5.end_shape()


def draw_tensor_glyphs():
    xs = np.linspace(-0.94, 0.94, 48)
    ys = np.linspace(-0.50, 0.50, 27)
    for y in ys:
        for x in xs:
            wx, wy = warp_point(x, y)
            sx, sy = screen_xy(wx, wy)
            if sx < -40 or sx > py5.width + 40 or sy < -40 or sy > py5.height + 40:
                continue

            j = jacobian(x, y)
            metric = j.T @ j
            vals, vecs = np.linalg.eigh(metric)
            stretch = float(np.sqrt(max(vals[1], 0.0)))
            squeeze = float(np.sqrt(max(vals[0], 0.0)))
            anisotropy = np.clip((stretch - squeeze) * 2.8, 0.0, 1.0)
            angle = float(np.arctan2(vecs[1, 1], vecs[0, 1]))

            major = 5.0 + 18.0 * anisotropy
            minor = 2.1 + 5.5 * (1.0 - anisotropy)
            alpha = 18 + 90 * anisotropy
            col = color_mix((105, 210, 226), (247, 126, 94), anisotropy)

            py5.push_matrix()
            py5.translate(sx, sy)
            py5.rotate(angle)
            py5.no_fill()
            py5.stroke(*col, alpha)
            py5.stroke_weight(0.65 + 1.1 * anisotropy)
            py5.ellipse(0, 0, major, minor)
            if anisotropy > 0.68:
                py5.stroke(247, 218, 145, 105)
                py5.line(-major * 0.45, 0, major * 0.45, 0)
            if anisotropy > 0.82:
                py5.no_stroke()
                py5.fill(105, 220, 236, 18)
                py5.ellipse(0, 0, major * 2.0, minor * 2.4)
            py5.pop_matrix()


def draw_pressure_bands():
    py5.no_fill()
    for cx, cy, amp, sigma, twist in CENTERS:
        sx, sy = screen_xy(cx, cy)
        hue = (235, 156, 108) if amp > 0 else (94, 216, 226)
        for k in range(5):
            py5.stroke(*hue, 26 - k * 3)
            py5.stroke_weight(1.4 - k * 0.12)
            w = sigma * py5.height * (2.2 + k * 0.62)
            h = sigma * py5.height * (1.1 + k * 0.44)
            py5.push_matrix()
            py5.translate(sx, sy)
            py5.rotate(twist * 0.9)
            py5.ellipse(0, 0, w, h)
            py5.pop_matrix()


def draw():
    py5.blend_mode(py5.BLEND)
    draw_background()
    py5.blend_mode(py5.SCREEN)
    draw_pressure_bands()
    draw_warped_family(horizontal=True)
    draw_warped_family(horizontal=False)
    draw_tensor_glyphs()

    py5.blend_mode(py5.BLEND)
    py5.no_fill()
    py5.stroke(230, 240, 250, 26)
    py5.stroke_weight(1.2)
    py5.rect(32, 32, py5.width - 64, py5.height - 64)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()

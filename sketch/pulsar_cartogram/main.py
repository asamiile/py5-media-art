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

PULSARS = []


def setup():
    global PULSARS
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.smooth(8)
    py5.no_loop()

    rng = np.random.default_rng()
    PULSARS = []
    for _ in range(28):
        angle = rng.uniform(0, py5.TWO_PI)
        radius = rng.uniform(0.18, 1.16)
        period = rng.uniform(0.035, 0.19)
        drift = rng.uniform(-0.16, 0.16)
        strength = rng.uniform(0.45, 1.0)
        PULSARS.append((angle, radius, period, drift, strength))


def screen_from_polar(angle, radius):
    w, h = SIZE
    x = w * 0.5 + np.cos(angle) * radius * h * 0.48
    y = h * 0.5 + np.sin(angle) * radius * h * 0.48
    return x, y


def draw_arc(cx, cy, r, a0, a1, color, alpha, weight):
    py5.no_fill()
    py5.stroke(*color, alpha)
    py5.stroke_weight(weight)
    py5.arc(cx, cy, r * 2, r * 2, a0, a1)


def draw_pulse_train(angle, radius, period, drift, strength, idx):
    w, h = SIZE
    cx, cy = screen_from_polar(angle, radius)
    origin_x, origin_y = w * 0.5, h * 0.5
    dx = cx - origin_x
    dy = cy - origin_y
    length = np.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    py5.stroke(80, 122, 150, 38 + 28 * strength)
    py5.stroke_weight(0.8)
    py5.line(origin_x, origin_y, cx, cy)

    ticks = int(120 + radius * 160)
    phase = idx * 0.21
    for i in range(ticks):
        t = i / max(1, ticks - 1)
        pulse = np.sin((t / period + phase + drift * t * t) * py5.TWO_PI)
        if pulse < 0.72:
            continue
        amp = (pulse - 0.72) / 0.28
        px = origin_x + dx * t
        py = origin_y + dy * t
        l = (4.0 + 23.0 * amp) * (0.35 + strength)
        py5.stroke(102, 225, 235, 40 + 120 * amp * strength)
        py5.stroke_weight(0.6 + 1.2 * amp)
        py5.line(px - nx * l * 0.5, py - ny * l * 0.5, px + nx * l * 0.5, py + ny * l * 0.5)

    py5.no_fill()
    py5.stroke(231, 188, 116, 80 + 60 * strength)
    py5.stroke_weight(1.2)
    py5.circle(cx, cy, 6 + 12 * strength)
    py5.stroke(205, 92, 132, 45)
    py5.circle(cx, cy, 18 + 26 * strength)


def draw():
    w, h = SIZE
    py5.background(4, 6, 12)
    py5.blend_mode(py5.SCREEN)

    # Faint chart paper and barycentric rings.
    for y in range(0, h, 18):
        py5.stroke(28, 42, 56, 18)
        py5.stroke_weight(0.45)
        py5.line(0, y, w, y)
    for x in range(0, w, 24):
        py5.stroke(24, 36, 50, 14)
        py5.line(x, 0, x, h)

    cx, cy = w * 0.5, h * 0.5
    for k in range(1, 15):
        r = h * 0.043 * k
        draw_arc(cx, cy, r, 0, py5.TWO_PI, (55, 80, 104), 20, 0.65)

    for i, (angle, radius, period, drift, strength) in enumerate(PULSARS):
        draw_pulse_train(angle, radius, period, drift, strength, i)

    for lane in np.linspace(-0.42, 0.42, 9):
        py5.no_fill()
        py5.stroke(62, 104, 132, 22)
        py5.stroke_weight(0.75)
        py5.begin_shape()
        for t in np.linspace(-0.98, 0.98, 150):
            x = w * (0.5 + t * 0.48)
            y = h * (0.5 + lane + 0.035 * np.sin(t * 9.0 + lane * 8.0))
            py5.curve_vertex(x, y)
        py5.end_shape()

    for i, (angle, radius, period, drift, strength) in enumerate(PULSARS):
        cxp, cyp = screen_from_polar(angle, radius)
        for band in range(3):
            rr = h * (0.035 + period * 0.65 + band * 0.014)
            offset = drift * band
            draw_arc(
                cxp,
                cyp,
                rr,
                angle + np.pi * 0.52 + offset,
                angle + np.pi * (0.88 + 0.12 * strength) + offset,
                (86, 134, 166) if band != 1 else (232, 180, 102),
                26 + 26 * strength,
                0.75,
            )

    # Central reference object, intentionally understated.
    py5.no_fill()
    py5.stroke(235, 244, 238, 90)
    py5.stroke_weight(1.5)
    py5.circle(w * 0.5, h * 0.5, 18)
    py5.stroke(104, 226, 236, 52)
    py5.line(w * 0.5 - 42, h * 0.5, w * 0.5 + 42, h * 0.5)
    py5.line(w * 0.5, h * 0.5 - 42, w * 0.5, h * 0.5 + 42)

    # A few small background stars keep the chart from feeling empty.
    rng = np.random.default_rng()
    for _ in range(520):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        a = rng.uniform(10, 58)
        py5.stroke(160, 190, 210, a)
        py5.stroke_weight(rng.uniform(0.45, 1.2))
        py5.point(x, y)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()

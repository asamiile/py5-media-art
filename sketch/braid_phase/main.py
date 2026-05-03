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

STRANDS = []


def setup():
    global STRANDS
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.smooth(8)
    py5.no_loop()
    rng = np.random.default_rng()
    STRANDS = []
    for i in range(11):
        STRANDS.append(
            {
                "phase": rng.uniform(0, py5.TWO_PI),
                "amp": rng.uniform(0.13, 0.32),
                "freq": rng.choice([2, 3, 4, 5]),
                "drift": rng.uniform(-0.32, 0.32),
                "color": rng.choice(["teal", "violet", "copper"]),
            }
        )


def draw_background():
    w, h = SIZE
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (x - w * 0.5) / h
    ny = (y - h * 0.5) / h
    field = (
        np.sin((nx * 2.8 + ny * 1.2) * 26.0)
        + np.sin((nx * -1.1 + ny * 3.4) * 19.0)
        + 0.55 * np.sin((nx + ny) * 71.0)
    )
    band = np.abs(np.mod(field * 1.7, 1.0) - 0.5) * 2.0
    line = np.clip((0.18 - band) / 0.18, 0, 1) ** 2
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = np.array([5, 7, 12], dtype=np.uint8)
    img[..., 1] = np.clip(img[..., 1] + line * 18, 0, 255)
    img[..., 2] = np.clip(img[..., 2] + line * 26, 0, 255)
    py5.set_np_pixels(img, bands="RGB")


def strand_points(s):
    w, h = SIZE
    pts = []
    for t in np.linspace(-1.06, 1.06, 280):
        envelope = np.sin((t + 1.06) / 2.12 * np.pi)
        x = w * (0.5 + t * 0.43)
        y = h * (
            0.5
            + s["amp"] * np.sin(s["freq"] * np.pi * t + s["phase"]) * envelope
            + 0.045 * np.sin(9.0 * t + s["phase"] * 0.7)
            + s["drift"] * 0.16 * t
        )
        z = np.sin(s["freq"] * np.pi * t + s["phase"])
        pts.append((x, y, z))
    return pts


def color_for(name):
    if name == "teal":
        return (72, 220, 210)
    if name == "violet":
        return (138, 104, 204)
    return (205, 142, 82)


def draw_strand(pts, color, pass_front=True):
    for i in range(len(pts) - 1):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[i + 1]
        z = (z0 + z1) * 0.5
        if pass_front and z < -0.05:
            continue
        if not pass_front and z >= -0.05:
            continue
        alpha = 48 + 112 * (0.5 + 0.5 * z)
        weight = 3.2 + 6.8 * (0.5 + 0.5 * z)
        py5.stroke(0, 0, 0, 45)
        py5.stroke_weight(weight + 5)
        py5.line(x0, y0, x1, y1)
        py5.stroke(*color, alpha)
        py5.stroke_weight(weight)
        py5.line(x0, y0, x1, y1)
        if z > 0.45:
            py5.stroke(232, 244, 224, 45)
            py5.stroke_weight(1.0)
            py5.line(x0, y0 - weight * 0.28, x1, y1 - weight * 0.28)


def draw():
    draw_background()
    py5.blend_mode(py5.SCREEN)
    all_pts = [(strand_points(s), color_for(s["color"])) for s in STRANDS]
    for pts, color in all_pts:
        draw_strand(pts, color, pass_front=False)
    for pts, color in all_pts:
        draw_strand(pts, color, pass_front=True)

    py5.no_fill()
    py5.stroke(226, 184, 98, 42)
    py5.stroke_weight(1.0)
    for x in np.linspace(py5.width * 0.12, py5.width * 0.88, 8):
        py5.line(x, py5.height * 0.12, x + 80, py5.height * 0.88)

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename=PREVIEW_FILENAME)


if __name__ == "__main__":
    py5.run_sketch()

from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N_CURVES = 24
N_PTS = 5000

# Frequency pairs for rich variety of figures
FREQ_PAIRS = [
    (1, 2), (1, 3), (2, 3), (1, 4), (3, 4), (2, 5), (3, 5), (4, 5),
    (1, 6), (5, 6), (3, 7), (4, 7), (5, 7), (2, 7), (3, 8), (5, 8),
    (7, 8), (4, 9), (5, 9), (7, 9), (2, 9), (5, 11), (4, 11), (7, 11),
]


def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 12)
    py5.no_fill()
    py5.stroke_weight(0.9)

    margin = 0.06
    rx = SIZE[0] * (1 - 2 * margin) / 2
    ry = SIZE[1] * (1 - 2 * margin) / 2
    cx, cy = SIZE[0] / 2, SIZE[1] / 2

    t = np.linspace(0, 2 * np.pi, N_PTS, endpoint=False)

    for i, (a, b) in enumerate(FREQ_PAIRS[:N_CURVES]):
        delta = np.random.uniform(0, 2 * np.pi)

        xs = np.sin(a * t + delta) * rx + cx
        ys = np.sin(b * t) * ry + cy

        # Hue spread evenly across curves; saturation/brightness high
        hue = (i / N_CURVES * 360 + 20) % 360
        alpha = np.random.randint(55, 80)
        py5.stroke(hue, 82, 95, alpha)

        py5.begin_shape()
        for x, y in zip(xs, ys):
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

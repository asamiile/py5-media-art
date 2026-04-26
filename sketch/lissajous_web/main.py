from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N_PTS = 8000

# Curated pairs: forms that abstractly suggest organic silhouettes
FREQ_PAIRS = [
    (1, 2), (2, 3), (3, 4), (3, 5), (4, 5),
    (5, 7), (1, 4), (2, 5), (5, 8), (7, 9),
]

# Palette — warm gold, steel blue, off-white accent
GOLD  = (200, 169, 110)   # #c8a96e
STEEL = (126, 155, 181)   # #7e9bb5
WHITE = (255, 244, 224)   # #fff4e0


def setup():
    py5.size(*SIZE)
    py5.background(9, 9, 15)   # #09090f near-black
    py5.no_fill()

    margin = 0.05
    rx = SIZE[0] * (1 - 2 * margin) / 2
    ry = SIZE[1] * (1 - 2 * margin) / 2
    cx, cy = SIZE[0] / 2, SIZE[1] / 2

    t = np.linspace(0, 2 * np.pi, N_PTS, endpoint=False)

    # Draw each curve twice — thin+faint base then slightly thicker mid
    for i, (a, b) in enumerate(FREQ_PAIRS):
        # Deterministic phase spread so the canvas fills consistently each run
        delta = np.pi * 0.37 * i

        xs = np.sin(a * t + delta) * rx + cx
        ys = np.sin(b * t) * ry + cy
        pts = list(zip(xs.tolist(), ys.tolist()))

        col = GOLD if i % 2 == 0 else STEEL

        # Main layer — weight 2.5 so strokes render at ≥5px in Retina save
        py5.stroke(*col, 50)
        py5.stroke_weight(2.5)
        py5.begin_shape()
        for x, y in pts:
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

    # Off-white accent to lift dense intersection zones
    py5.stroke(*WHITE, 30)
    py5.stroke_weight(1.2)
    for i, (a, b) in enumerate(FREQ_PAIRS[:6]):
        delta = np.pi * 0.37 * i
        xs = np.sin(a * t + delta) * rx + cx
        ys = np.sin(b * t) * ry + cy
        py5.begin_shape()
        for x, y in zip(xs.tolist(), ys.tolist()):
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

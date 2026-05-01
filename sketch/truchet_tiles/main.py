from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

TILE = 40   # smaller tile → denser weave

# 4-orientation Smith Truchet; orientation determines arc/line variant
# 0: arc TL+BR   1: arc TR+BL   2: diagonal /   3: diagonal \
# Palette: linen / espresso — monochrome, structure from geometry not color
BG      = (214, 207, 196)   # #d6cfc4 warm linen
COL_ARC = (61, 53, 48)      # #3d3530 deep espresso (arcs)
COL_LIN = (138, 127, 116)   # #8a7f74 mid gray-beige (diagonal lines)


def setup():
    py5.size(*SIZE)
    py5.background(*BG)
    py5.no_fill()

    cols = SIZE[0] // TILE + 1
    rows = SIZE[1] // TILE + 1
    r = TILE / 2

    variants = np.random.randint(0, 4, (rows, cols))

    for row in range(rows):
        for col in range(cols):
            tx = col * TILE
            ty = row * TILE
            v = int(variants[row, col])

            if v == 0:
                # Arc TL corner + BR corner (connects adjacent midpoints)
                py5.stroke(*COL_ARC, 230)
                py5.stroke_weight(2.5)
                py5.arc(tx,        ty,        TILE, TILE, 0,           py5.HALF_PI,       py5.OPEN)
                py5.arc(tx + TILE, ty + TILE, TILE, TILE, py5.PI,      3*py5.HALF_PI,     py5.OPEN)

            elif v == 1:
                # Arc TR corner + BL corner
                py5.stroke(*COL_ARC, 230)
                py5.stroke_weight(2.5)
                py5.arc(tx + TILE, ty,        TILE, TILE, py5.HALF_PI, py5.PI,            py5.OPEN)
                py5.arc(tx,        ty + TILE, TILE, TILE, 3*py5.HALF_PI, py5.TWO_PI,     py5.OPEN)

            elif v == 2:
                # Diagonal line: bottom-left → top-right  (/)
                py5.stroke(*COL_LIN, 200)
                py5.stroke_weight(1.8)
                py5.line(tx, ty + TILE, tx + TILE, ty)

            else:
                # Diagonal line: top-left → bottom-right  (\)
                py5.stroke(*COL_LIN, 200)
                py5.stroke_weight(1.8)
                py5.line(tx, ty, tx + TILE, ty + TILE)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

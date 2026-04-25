from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

TILE = 60   # pixels per tile (32 × 18 = 576 tiles)

# Two complementary stroke colors (RGBA) for the two tile orientations
COLOR_A = (255, 90, 130)    # rose-coral  → variant 0
COLOR_B = (55, 210, 220)    # cyan-teal   → variant 1
BG = (10, 8, 14)            # near-black background


def setup():
    py5.size(*SIZE)
    py5.background(*BG)
    py5.no_fill()

    cols = SIZE[0] // TILE + 1
    rows = SIZE[1] // TILE + 1
    r = TILE / 2   # arc radius = half tile size

    variants = np.random.randint(0, 2, (rows, cols))

    for row in range(rows):
        for col in range(cols):
            tx = col * TILE
            ty = row * TILE
            v = variants[row, col]

            if v == 0:
                # Variant 0: arcs at top-left and bottom-right corners
                # Top-left arc: connects top-midpoint to left-midpoint
                py5.stroke(*COLOR_A, 210)
                py5.stroke_weight(2.8)
                py5.arc(tx, ty, TILE, TILE, 0, py5.HALF_PI, py5.OPEN)
                # Bottom-right arc: connects bottom-midpoint to right-midpoint
                py5.arc(tx + TILE, ty + TILE, TILE, TILE,
                        py5.PI, 3 * py5.HALF_PI, py5.OPEN)
            else:
                # Variant 1: arcs at top-right and bottom-left corners
                # Top-right arc: connects right-midpoint to top-midpoint
                py5.stroke(*COLOR_B, 210)
                py5.stroke_weight(2.8)
                py5.arc(tx + TILE, ty, TILE, TILE,
                        py5.HALF_PI, py5.PI, py5.OPEN)
                # Bottom-left arc: connects left-midpoint to bottom-midpoint
                py5.arc(tx, ty + TILE, TILE, TILE,
                        3 * py5.HALF_PI, py5.TWO_PI, py5.OPEN)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

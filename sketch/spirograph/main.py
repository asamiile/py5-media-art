from pathlib import Path
import math
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Machine botany" — eight hypotrochoid curves overlaid at the canvas center,
# each driven by a different gear ratio (R, r, d), producing interlocking petal rosettes.
# Technique: parametric hypotrochoid equations, normalized to canvas radius,
# semi-transparent strokes reveal overlapping layer structure.

BG_COL = (6, 6, 14)   # near-black with slight blue tint

# Each entry: (R, r, d, R_stroke, G_stroke, B_stroke)
# R/gcd(R,r) determines petal count; r/gcd(R,r) determines how many full gear revolutions

# All curves use d = R - r (classic rose hypotrochoid): clean petal shapes, no inner loops.
# Petal count = R / gcd(R,r); curve closes after r/gcd(R,r) full inner-gear revolutions.
CURVES = [
    ( 5,  3,  2, 210,  55,  70),   # crimson    — 5-petal
    ( 7,  3,  4, 225, 188,  55),   # gold       — 7-petal
    ( 9,  4,  5,  55, 190, 190),   # teal       — 9-petal
    ( 4,  1,  3, 170,  55, 225),   # violet     — 4-petal clover
    (11,  4,  7, 225, 128,  85),   # coral      — 11-petal
    (12,  5,  7, 128, 208, 128),   # sage green — 12-petal
    ( 8,  3,  5,  85, 148, 228),   # steel blue — 8-petal
    ( 6,  1,  5, 228,  85, 170),   # rose       — 6-petal wide
]

RADIUS    = min(SIZE) * 0.46   # maximum curve extent in pixels
N_PTS     = 6000               # curve resolution
ALPHA     = 185                # stroke alpha (0-255)
SW        = 2.2                # stroke weight


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    CX, CY = SIZE[0] / 2, SIZE[1] / 2

    py5.no_fill()
    py5.stroke_weight(SW)

    for R, r, d, sr, sg, sb in CURVES:
        gcd_val = math.gcd(R, r)
        n_revs = r // gcd_val          # full inner-gear rotations for curve closure
        t = np.linspace(0, 2 * np.pi * n_revs, N_PTS, dtype=np.float64)

        # Hypotrochoid: inner gear of radius r rolling inside outer gear of radius R
        x = (R - r) * np.cos(t) + d * np.cos((R - r) / r * t)
        y = (R - r) * np.sin(t) - d * np.sin((R - r) / r * t)

        # Normalize so max radial extent = RADIUS
        max_r = np.max(np.sqrt(x ** 2 + y ** 2))
        scale = RADIUS / (max_r + 1e-8)
        x = CX + x * scale
        y = CY + y * scale

        py5.stroke(sr, sg, sb, ALPHA)
        py5.begin_shape()
        for xi, yi in zip(x.tolist(), y.tolist()):
            py5.vertex(xi, yi)
        py5.end_shape(py5.CLOSE)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

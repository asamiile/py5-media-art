from pathlib import Path
import cmath
import math
from collections import deque
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Recursive tangency" — Apollonian gasket from the (-1,2,2,3) starting
# quadruple; every gap between three mutually tangent circles is filled by a
# unique inscribed circle computed via Descartes' theorem; the fractal pattern
# never repeats as circles shrink to a dust of infinite depth.

MIN_RADIUS = 0.004   # stop recursing below this radius (unit-circle coords)
BG_COL     = (5, 8, 15)

# 6-stop curvature-octave palette (blends across log₂(k) levels)
PALETTE = [
    (218, 162,  28),   # warm gold    (k≈2–4)
    (215,  85,  40),   # coral        (k≈4–8)
    (175,  45, 165),   # magenta      (k≈8–16)
    ( 70,  40, 210),   # deep violet  (k≈16–32)
    ( 25, 132, 215),   # cerulean     (k≈32–64)
    ( 28, 190, 148),   # teal         (k≈64+)
]


def palette_col(k):
    level = max(0.0, math.log2(max(k, 2.0) / 2.0))
    idx = int(level) % len(PALETTE)
    frac = level - int(level)
    c0 = PALETTE[idx]
    c1 = PALETTE[(idx + 1) % len(PALETTE)]
    return tuple(int(c0[i] * (1 - frac) + c1[i] * frac) for i in range(3))


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    # Initial (-1, 2, 2, 3) quadruple
    circles = [
        (-1.0, 0 + 0j),       # outer (k<0 → contains all others)
        ( 2.0, 0.5 + 0j),     # circle A  (r=1/2, center (½,0))
        ( 2.0, -0.5 + 0j),    # circle B  (r=1/2, center (-½,0))
        ( 3.0, 0 + 2j / 3),   # circle C  (r=1/3, center (0,⅔))
    ]

    # Queue: ((i,j,k), excluded_index) — no sqrt needed!
    # k_new = 2(ki+kj+kk) - k_excl   z_new = (2(ki·zi+kj·zj+kk·zk) - k_excl·z_excl) / k_new
    queue = deque([
        ((0, 1, 2), 3),
        ((0, 1, 3), 2),
        ((0, 2, 3), 1),
        ((1, 2, 3), 0),
    ])

    while queue:
        (i, j, k), excl = queue.popleft()
        ki, zi = circles[i]
        kj, zj = circles[j]
        kk, zk = circles[k]
        ke, ze = circles[excl]

        k_new = 2 * (ki + kj + kk) - ke
        if k_new <= 0:
            continue
        r_new = 1.0 / k_new
        if r_new < MIN_RADIUS:
            continue

        z_new = (2 * (ki * zi + kj * zj + kk * zk) - ke * ze) / k_new

        n = len(circles)
        circles.append((k_new, z_new))
        queue.extend([
            ((i, j, n), k),
            ((i, k, n), j),
            ((j, k, n), i),
        ])

    # Map unit coords → screen coords
    scale = min(W, H) * 0.88 / 2.0
    ox, oy = W / 2.0, H / 2.0

    py5.background(*BG_COL)
    py5.no_stroke()

    # Draw outer circle rim
    py5.fill(14, 12, 25)
    py5.ellipse(ox, oy, 2 * scale, 2 * scale)

    # Sort: large circles first so small ones draw on top
    inner = sorted(((k, z) for k, z in circles if k > 0), key=lambda c: c[0])

    py5.stroke_weight(0.5)

    for kc, z in inner:
        r  = 1.0 / kc
        sx = z.real * scale + ox
        sy = z.imag * scale + oy
        sr = r * scale
        col = palette_col(kc)
        # fade brightness for tiny circles
        t = min(1.0, (math.log(r) - math.log(MIN_RADIUS)) / (math.log(0.5) - math.log(MIN_RADIUS) + 1e-8))
        alpha = int(180 + 75 * t)
        py5.stroke(col[0] // 4, col[1] // 4, col[2] // 4, 180)
        py5.fill(*col, alpha)
        py5.ellipse(sx, sy, sr * 2, sr * 2)


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

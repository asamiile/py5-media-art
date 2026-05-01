from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import exit_after_preview_py5
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

RNG = np.random.default_rng()


def setup():
    py5.size(*SIZE)
    py5.background(4, 7, 14)
    py5.no_loop()


def draw():
    W, H = SIZE

    # Web centre: slightly off-centre for natural asymmetry
    cx = W * RNG.uniform(0.44, 0.56)
    cy = H * RNG.uniform(0.40, 0.58)

    # Web geometry
    n_radii  = int(RNG.uniform(30, 40))    # number of radial threads
    n_spiral = int(RNG.uniform(22, 30))    # number of spiral rows
    max_r    = min(W * 0.46, H * 0.44)
    r_hub    = max_r * RNG.uniform(0.07, 0.11)
    r_start  = max_r * 0.12               # innermost spiral row

    # Radii angles: nearly evenly spaced with tiny jitter for naturalism
    base_angles = 2.0 * np.pi * np.arange(n_radii) / n_radii
    jitter  = RNG.uniform(-0.025, 0.025, size=n_radii)
    angles  = base_angles + jitter

    # Radial length varies slightly (some radii reach a bit less far)
    r_len = RNG.uniform(0.88, 1.0, size=n_radii) * max_r

    endpoints = np.column_stack([
        cx + r_len * np.cos(angles),
        cy + r_len * np.sin(angles),
    ])

    # Spiral rows: logarithmically spaced from hub to frame
    spiral_r = r_start * (max_r / r_start) ** (np.arange(n_spiral) / (n_spiral - 1))

    # Pre-compute all intersection points:  intersections[row, radius] = (x, y)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)
    intersections = np.empty((n_spiral, n_radii, 2))
    for j in range(n_spiral):
        intersections[j, :, 0] = cx + spiral_r[j] * cos_a
        intersections[j, :, 1] = cy + spiral_r[j] * sin_a

    # ── Radial threads ──────────────────────────────────────────────────────
    for i in range(n_radii):
        alpha = int(RNG.uniform(55, 100))
        py5.stroke(185, 198, 220, alpha)
        py5.stroke_weight(RNG.uniform(0.5, 0.9))
        py5.line(cx, cy, endpoints[i, 0], endpoints[i, 1])

    # ── Outer frame (polygon connecting all endpoints) ──────────────────────
    py5.stroke(170, 188, 215, 60)
    py5.stroke_weight(0.8)
    py5.no_fill()
    for i in range(n_radii):
        p1 = endpoints[i]
        p2 = endpoints[(i + 1) % n_radii]
        py5.line(p1[0], p1[1], p2[0], p2[1])

    # ── Spiral (capture) threads ────────────────────────────────────────────
    py5.no_fill()
    for j in range(n_spiral):
        row   = intersections[j]
        frac  = j / (n_spiral - 1)
        wt    = 0.45 + 0.65 * frac          # thicker toward outside
        alpha = int(48 + 32 * frac)
        py5.stroke_weight(wt)
        py5.stroke(195, 210, 232, alpha)

        for i in range(n_radii):
            p1 = row[i]
            p2 = row[(i + 1) % n_radii]
            # Sag control point slightly toward centre
            mx = (p1[0] + p2[0]) * 0.5
            my = (p1[1] + p2[1]) * 0.5
            sag = 0.962 + 0.025 * frac      # more sag at outer rows
            ctrl_x = cx + sag * (mx - cx)
            ctrl_y = cy + sag * (my - cy)
            py5.begin_shape()
            py5.vertex(p1[0], p1[1])
            py5.quadratic_vertex(ctrl_x, ctrl_y, p2[0], p2[1])
            py5.end_shape()

    # ── Hub ─────────────────────────────────────────────────────────────────
    py5.no_stroke()
    for r_scale, alpha in [(2.0, 20), (1.4, 55), (1.0, 110), (0.5, 180)]:
        py5.fill(195, 210, 235, alpha)
        py5.circle(cx, cy, r_hub * r_scale * 2)

    # ── Dew drops ───────────────────────────────────────────────────────────
    py5.no_stroke()
    for j in range(n_spiral):
        row   = intersections[j]
        frac  = j / (n_spiral - 1)

        for i in range(n_radii):
            # Skip ~20 % of intersections randomly (gaps in dew coverage)
            if RNG.random() < 0.20:
                continue

            px, py_ = row[i]

            # Drop size: grows toward the outside (more silk surface area)
            base_r = RNG.uniform(1.5, 2.8) * (0.4 + 0.9 * frac)

            # Outer halo glow
            py5.fill(140, 185, 230, 18)
            py5.circle(px, py_, base_r * 6.0)

            # Drop body (layered for volume illusion)
            py5.fill(165, 205, 242, 45)
            py5.circle(px, py_, base_r * 2.8)

            py5.fill(195, 220, 248, 90)
            py5.circle(px, py_, base_r * 1.9)

            py5.fill(220, 238, 255, 150)
            py5.circle(px, py_, base_r * 1.2)

            # Specular highlight (bright, offset)
            hl_x = px - base_r * 0.30
            hl_y = py_ - base_r * 0.35
            py5.fill(255, 255, 255, 210)
            py5.circle(hl_x, hl_y, base_r * 0.42)

            # Occasional golden-tinted drop for warmth
            if RNG.random() < 0.06:
                py5.fill(255, 235, 180, 60)
                py5.circle(px, py_, base_r * 1.5)

    # ── Save ─────────────────────────────────────────────────────────────────
    exit_after_preview_py5(SKETCH_DIR, filename="preview.png")


py5.run_sketch()

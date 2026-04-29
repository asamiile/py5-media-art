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

# Theme: "Invisible geometry" — magnetic dipole field lines made visible
# Two magnetic poles (N and S) generate a dipole; streamlines trace the field

# Pole positions in normalized canvas coords (−1..1 range mapped to canvas)
POLE_SEP = 0.28   # half-distance between poles

N_LINES   = 72    # field lines per pole
STEP_SIZE = 0.006  # integration step (normalized units)
MAX_STEPS = 3000   # max steps per streamline
MIN_DIST  = 0.018  # stop integrating if within this dist of a pole

# Color encoding: lines that close near N pole → warm red; S pole → cold blue
# Mid-field lines → neutral gray
N_COL = np.array([200,  80,  50])   # #c85032 warm iron-red
S_COL = np.array([ 50,  90, 200])   # #325ac8 cold blue
BG_COL = (12, 10, 14)               # near-black with warm undertone


def dipole_field(px, py, pole_x, pole_y, charge):
    """B-field contribution from one pole at (pole_x, pole_y) with charge ±1."""
    dx = px - pole_x
    dy = py - pole_y
    r2 = dx * dx + dy * dy + 1e-9
    r3 = r2 ** 1.5
    bx = charge * dx / r3
    by = charge * dy / r3
    return bx, by


def trace_line(start_x, start_y, pole_n, pole_s):
    """Integrate a streamline from start, return list of (x,y) and end-pole."""
    x, y = start_x, start_y
    pts = [(x, y)]
    end_pole = None

    for _ in range(MAX_STEPS):
        bx_n, by_n = dipole_field(x, y, pole_n[0], pole_n[1], +1)
        bx_s, by_s = dipole_field(x, y, pole_s[0], pole_s[1], -1)
        bx = bx_n + bx_s
        by = by_n + by_s
        mag = np.sqrt(bx * bx + by * by) + 1e-12
        bx /= mag
        by /= mag

        x += STEP_SIZE * bx
        y += STEP_SIZE * by

        # Stop if out of bounds
        if abs(x) > 1.2 or abs(y) > 0.8:
            break

        # Stop if close to a pole
        dn = np.sqrt((x - pole_n[0])**2 + (y - pole_n[1])**2)
        ds = np.sqrt((x - pole_s[0])**2 + (y - pole_s[1])**2)
        if dn < MIN_DIST:
            end_pole = 'N'
            break
        if ds < MIN_DIST:
            end_pole = 'S'
            break

        pts.append((x, y))

    return pts, end_pole


def norm_to_canvas(x, y, w, h):
    """Convert normalized coords (−1..1 x, −0.56..0.56 y) to pixel coords."""
    px = int((x + 1.0) / 2.0 * w)
    py = int((0.5625 - y) / 1.125 * h)
    return np.clip(px, 0, w - 1), np.clip(py, 0, h - 1)


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    W, H = SIZE[0], SIZE[1]

    pole_n = (-POLE_SEP, 0.0)   # N pole (left)
    pole_s = ( POLE_SEP, 0.0)   # S pole (right)

    # Draw pole markers
    for (px_n, py_n), col in [
        (norm_to_canvas(*pole_n, W, H), N_COL),
        (norm_to_canvas(*pole_s, W, H), S_COL),
    ]:
        py5.no_stroke()
        py5.fill(*col, 200)
        py5.ellipse(px_n, py_n, 22, 22)
        py5.fill(*col, 60)
        py5.ellipse(px_n, py_n, 44, 44)

    # Seed field lines radiating from N pole at regular angles
    angles = np.linspace(0, 2 * np.pi, N_LINES, endpoint=False)

    py5.no_fill()
    for i, angle in enumerate(angles):
        # Start just outside the N pole
        sx = pole_n[0] + MIN_DIST * 1.8 * np.cos(angle)
        sy = pole_n[1] + MIN_DIST * 1.8 * np.sin(angle)

        pts, end_pole = trace_line(sx, sy, pole_n, pole_s)

        if len(pts) < 3:
            continue

        # Color: lines that return to N pole (closed loops) → gray;
        # lines ending at S pole → gradient N→S col;
        # lines escaping → dim gray
        if end_pole == 'S':
            # Warm red near N → neutral mid → cold blue near S
            n_pts = len(pts)
            for j in range(1, n_pts):
                t = j / n_pts
                r = int(N_COL[0] * (1 - t) + S_COL[0] * t)
                g = int(N_COL[1] * (1 - t) + S_COL[1] * t)
                b = int(N_COL[2] * (1 - t) + S_COL[2] * t)
                alpha = 180
                py5.stroke(r, g, b, alpha)
                py5.stroke_weight(1.6)
                x1, y1 = norm_to_canvas(*pts[j-1], W, H)
                x2, y2 = norm_to_canvas(*pts[j], W, H)
                py5.line(x1, y1, x2, y2)
        else:
            # Open/escaping lines — draw dimly
            py5.stroke(80, 80, 100, 60)
            py5.stroke_weight(0.8)
            for j in range(1, len(pts)):
                x1, y1 = norm_to_canvas(*pts[j-1], W, H)
                x2, y2 = norm_to_canvas(*pts[j], W, H)
                py5.line(x1, y1, x2, y2)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

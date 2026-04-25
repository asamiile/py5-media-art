from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N = 300   # points on the circle — finer envelope at higher N

CX = SIZE[0] / 2
CY = SIZE[1] / 2
RADIUS = SIZE[1] * 0.44

# Each entry: (multiplier, hue, alpha)
# M=2→cardioid, M=3→nephroid; higher M→more-pointed star envelopes
LAYERS = [
    (2,    0,   60),   # cardioid — warm red
    (3,   50,   55),   # nephroid — amber
    (5,  120,   50),   # 5-fold   — green
    (7,  190,   50),   # 7-fold   — cyan
    (13, 260,   45),   # 13-fold  — violet
    (51, 310,   40),   # complex  — magenta
]

# Precompute point positions
angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
px = CX + RADIUS * np.cos(angles)
py_pts = CY + RADIUS * np.sin(angles)


def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(8, 8, 10)
    py5.no_fill()
    py5.stroke_weight(0.7)

    for m, hue, alpha in LAYERS:
        py5.stroke(hue, 80, 95, alpha)
        for i in range(N):
            j = int(i * m) % N
            py5.line(px[i], py_pts[i], px[j], py_pts[j])


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

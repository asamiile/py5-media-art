from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N = 300   # points on the circle

CX = SIZE[0] / 2
CY = SIZE[1] / 2
RADIUS = SIZE[1] * 0.44

# Theme: "Resonance frequencies" — 3 harmonic families in complementary tones
# Low M (2,3): burnt sienna/rust  Mid M (5,7): steel blue  High M (13,51): sage green
# Each at low alpha so density accumulates naturally
LAYERS = [
    # (multiplier, R, G, B, alpha, weight)
    (2,  196, 120,  90, 45, 1.2),   # cardioid — burnt sienna
    (3,  196, 120,  90, 40, 1.2),   # nephroid — rust
    (5,   90, 140, 168, 40, 0.8),   # 5-fold   — steel blue
    (7,   90, 140, 168, 35, 0.8),   # 7-fold   — steel blue
    (13, 168, 200, 122, 32, 0.4),   # 13-fold  — sage green
    (51, 168, 200, 122, 28, 0.4),   # complex  — sage green
]

# Outer ring color: dark charcoal frame
RING_COL = (55, 55, 60)

# Precompute point positions
angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
px = CX + RADIUS * np.cos(angles)
py_pts = CY + RADIUS * np.sin(angles)


def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.RGB, 255, 255, 255, 255)
    py5.background(10, 10, 18)   # #0a0a12 near-black
    py5.no_fill()

    # Faint outer ring to frame the composition
    py5.stroke(*RING_COL, 160)
    py5.stroke_weight(1.5)
    py5.ellipse(CX, CY, RADIUS * 2, RADIUS * 2)

    for m, r, g, b, alpha, weight in LAYERS:
        py5.stroke(r, g, b, alpha)
        py5.stroke_weight(weight)
        for i in range(N):
            j = int(i * m) % N
            py5.line(px[i], py_pts[i], px[j], py_pts[j])


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

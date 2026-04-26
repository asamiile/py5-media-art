from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Folded infinity" — the Harter-Heighway dragon curve; 15 iterations of
# folding a paper strip in half produces 32,768 right-angle segments that never
# cross, yet tile the plane — a fractal from pure repetition.

N_ITER    = 15      # iterations → 2^N segments
N_GROUPS  = 16      # colour groups along the path (cyclic palette)
SW        = 1.6     # stroke weight

BG_COL = (6, 5, 10)  # near-black

# 4-stop cyclic palette (repeats N_GROUPS/4 = 4 times)
PALETTE = [
    (30,  18, 100),   # deep indigo
    (210,  75,  55),  # coral
    ( 28, 150, 140),  # teal
    (215, 168,  28),  # warm gold
]


def dragon_turns(n):
    """Return the turn sequence (1=right, -1=left) for dragon curve at iteration n."""
    turns = np.array([1], dtype=np.int8)
    for _ in range(n - 1):
        turns = np.concatenate([turns, [1], (-turns)[::-1]])
    return turns


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    W, H = SIZE
    turns = dragon_turns(N_ITER)      # length = 2^N_ITER - 1

    # Build angle sequence (mod 4)
    deltas = np.where(turns > 0, 1, 3).astype(np.int32)      # right=+1, left=+3≡-1
    cum    = np.cumsum(np.concatenate([[0], deltas])) % 4     # angles for each segment start

    dx_map = np.array([1, 0, -1,  0], dtype=np.int32)
    dy_map = np.array([0, 1,  0, -1], dtype=np.int32)
    dx = dx_map[cum]
    dy = dy_map[cum]

    xs = np.concatenate([[0], np.cumsum(dx)]).astype(np.float32)
    ys = np.concatenate([[0], np.cumsum(dy)]).astype(np.float32)

    # Scale and centre
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    x_range = x_max - x_min
    y_range = y_max - y_min

    scale = min(W * 0.90 / (x_range + 1e-8),
                H * 0.90 / (y_range + 1e-8))

    cx = W / 2 - (x_min + x_max) / 2 * scale
    cy = H / 2 - (y_min + y_max) / 2 * scale

    xs_px = xs * scale + cx
    ys_px = ys * scale + cy

    # Draw in N_GROUPS colour bands
    n_seg   = len(turns)          # = 2^N_ITER - 1 ≈ 32767
    seg_per = n_seg // N_GROUPS

    py5.no_fill()
    py5.stroke_weight(SW)

    for g in range(N_GROUPS):
        t = (g % 4) / 4.0                    # position in cyclic palette [0,1)
        t2 = t * 4.0
        ci = int(t2) % 4
        ci1 = (ci + 1) % 4
        frac = t2 - int(t2)
        col = tuple(int(PALETTE[ci][k] * (1 - frac) + PALETTE[ci1][k] * frac)
                    for k in range(3))
        alpha = 220
        py5.stroke(*col, alpha)

        s0 = g * seg_per
        s1 = (g + 1) * seg_per if g < N_GROUPS - 1 else n_seg

        py5.begin_shape()
        py5.vertex(float(xs_px[s0]), float(ys_px[s0]))
        for s in range(s0, s1 + 1):
            py5.vertex(float(xs_px[s]), float(ys_px[s]))
        py5.end_shape()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

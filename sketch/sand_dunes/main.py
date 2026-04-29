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

# Theme: "Eroded silence" — desert dunes at last light; wind geometry in sand
# Layered ridge silhouettes painted back-to-front, each layer lighter/more detailed

N_LAYERS = 14     # number of dune ridge layers
N_PTS    = 400    # x-resolution per ridge

# Dune layer color palette (back-to-front: dark → light)
# Sky portion: burnt sienna → amber → warm gold
# Dune silhouettes: dark brown → rust → warm ochre → pale sand

# Sky gradient top/bottom
SKY_TOP = np.array([40,  28,  18], dtype=np.float32)   # #281c12 burnt sienna-black
SKY_BOT = np.array([180, 120,  60], dtype=np.float32)  # #b4783c amber horizon

# Layer colors back→front
LAYER_COLS = np.array([
    [50,  32,  18],   # #321e12 darkest back dune
    [68,  44,  22],   # #442c16
    [90,  58,  28],   # #5a3a1c
    [115,  76,  38],  # #734c26
    [140,  95,  48],  # #8c5f30
    [162, 115,  60],  # #a2733c
    [180, 135,  72],  # #b48748
    [196, 155,  85],  # #c49b55
    [210, 172, 100],  # #d2ac64
    [220, 188, 118],  # #dcbc76
    [228, 200, 135],  # #e4c887
    [234, 210, 155],  # #ead29b
    [240, 220, 170],  # #f0dcaa
    [245, 232, 192],  # #f5e8c0 lightest front dune
], dtype=np.float32)


def smooth_noise_1d(n_pts, seed, octaves=4, roughness=0.55):
    """Generate a smooth 1D noise profile using summed cosines."""
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n_pts, dtype=np.float32)
    signal = np.zeros(n_pts, dtype=np.float32)
    freq = 2.0
    amp = 1.0
    for _ in range(octaves):
        phase = rng.uniform(0, 2 * np.pi)
        signal += amp * np.cos(freq * np.pi * 2 * x + phase)
        freq *= 2.1
        amp  *= roughness
    # Normalize to [0, 1]
    signal -= signal.min()
    signal /= signal.max() + 1e-8
    return signal


def setup():
    py5.size(*SIZE)
    W, H = SIZE[0], SIZE[1]

    # Build pixel array for sky gradient background
    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    # Sky gradient
    rows = np.arange(h_buf, dtype=np.float32)
    t = rows / h_buf
    r_sky = (SKY_TOP[0] * (1 - t) + SKY_BOT[0] * t)[:, np.newaxis]
    g_sky = (SKY_TOP[1] * (1 - t) + SKY_BOT[1] * t)[:, np.newaxis]
    b_sky = (SKY_TOP[2] * (1 - t) + SKY_BOT[2] * t)[:, np.newaxis]

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = np.broadcast_to(r_sky, (h_buf, w_buf)).astype(np.uint8)
    py5.np_pixels[:, :, 2] = np.broadcast_to(g_sky, (h_buf, w_buf)).astype(np.uint8)
    py5.np_pixels[:, :, 3] = np.broadcast_to(b_sky, (h_buf, w_buf)).astype(np.uint8)
    py5.update_np_pixels()

    # Draw dune layers back-to-front using py5 drawing primitives
    # Each layer is a filled polygon: top = ridge profile, bottom = bottom of canvas
    py5.no_stroke()

    for li in range(N_LAYERS):
        t_layer = li / (N_LAYERS - 1)   # 0 = back, 1 = front

        col = LAYER_COLS[li]
        py5.fill(*col.astype(int))

        # Ridge height: back layers are higher (closer to horizon)
        # Front layers are lower (covering more of foreground)
        ridge_y_min = H * (0.30 + t_layer * 0.25)   # 30%–55% from top
        ridge_y_range = H * (0.08 + t_layer * 0.15)  # amplitude: small back, large front

        # 3–5 octaves; more detail in front layers
        octaves = 2 + int(t_layer * 3)
        profile = smooth_noise_1d(N_PTS, seed=li * 7 + 13, octaves=octaves)

        # Y positions for ridge (note: y increases downward)
        ys = (ridge_y_min + profile * ridge_y_range).astype(int)
        xs = np.linspace(0, W, N_PTS).astype(int)

        py5.begin_shape()
        # Start at bottom-left corner
        py5.vertex(0, H)
        # Ridge profile left to right
        for i in range(N_PTS):
            py5.vertex(xs[i], ys[i])
        # End at bottom-right corner
        py5.vertex(W, H)
        py5.end_shape(py5.CLOSE)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

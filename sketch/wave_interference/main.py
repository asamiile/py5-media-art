from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Sources spread across the full canvas so waves reach every corner
SOURCES = [
    (-0.85,  0.45), ( 0.85,  0.45), ( 0.00, -0.50),
    (-0.50,  0.00), ( 0.55,  0.10), ( 0.10,  0.48),
    (-0.20, -0.42), ( 0.72, -0.38), (-0.78, -0.30),
]
WAVELENGTH = 0.16


def setup():
    py5.size(*SIZE)

    h_sim, w_sim = PREVIEW_SIZE[1], PREVIEW_SIZE[0]
    x = np.linspace(-1.0,    1.0,    w_sim, dtype=np.float32)
    y = np.linspace(-0.5625, 0.5625, h_sim, dtype=np.float32)
    X, Y = np.meshgrid(x, y)

    wave = np.zeros((h_sim, w_sim), dtype=np.float32)
    for sx, sy in SOURCES:
        r = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)
        wave += np.sin(2 * np.pi * r / WAVELENGTH)

    d = (wave - wave.min()) / (wave.max() - wave.min())

    # Wide palette: dark purple → electric blue → bright yellow-white
    r_ch = (d ** 1.2 * 220 + d ** 3 * 35).clip(0, 255).astype(np.uint8)
    g_ch = (d ** 0.6 * 180 + d ** 3 * 75).clip(0, 255).astype(np.uint8)
    b_ch = (np.sin(d * np.pi) * 255).clip(0, 255).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != h_sim or w_buf != w_sim:
        sy_sc = h_buf // h_sim
        sx_sc = w_buf // w_sim
        r_ch = np.repeat(np.repeat(r_ch, sy_sc, axis=0), sx_sc, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, sy_sc, axis=0), sx_sc, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, sy_sc, axis=0), sx_sc, axis=1)

    alpha = np.full((h_buf, w_buf), 255, dtype=np.uint8)
    py5.np_pixels[:, :, 0] = alpha
    py5.np_pixels[:, :, 1] = r_ch
    py5.np_pixels[:, :, 2] = g_ch
    py5.np_pixels[:, :, 3] = b_ch
    py5.update_np_pixels()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

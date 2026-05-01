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
PREVIEW_FRAME = 120

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Theme: "Precision instrument" — hard-threshold binary render, 5 sources
# Near-black / dark teal / cold near-white — like an oscilloscope or X-ray
SOURCES = [
    (-0.60,  0.35), ( 0.60,  0.35),
    ( 0.00, -0.45), (-0.38, -0.10), ( 0.42,  0.05),
]
WAVELENGTH = 0.14

# Three-level threshold rendering
BG_COL   = np.array([3,   5,  10], dtype=np.uint8)    # #03050a near-black
MID_COL  = np.array([26, 58,  74], dtype=np.uint8)    # #1a3a4a dark teal
PEAK_COL = np.array([224, 240, 255], dtype=np.uint8)  # #e0f0ff cold near-white

THRESHOLD_PEAK = 0.78   # above → bright peak
THRESHOLD_MID  = 0.52   # above → dark teal


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

    # Normalize to 0–1
    d = (wave - wave.min()) / (wave.max() - wave.min())

    # Hard threshold: 3 levels only — no gradient
    r_ch = np.where(d >= THRESHOLD_PEAK, PEAK_COL[0],
           np.where(d >= THRESHOLD_MID,  MID_COL[0], BG_COL[0])).astype(np.uint8)
    g_ch = np.where(d >= THRESHOLD_PEAK, PEAK_COL[1],
           np.where(d >= THRESHOLD_MID,  MID_COL[1], BG_COL[1])).astype(np.uint8)
    b_ch = np.where(d >= THRESHOLD_PEAK, PEAK_COL[2],
           np.where(d >= THRESHOLD_MID,  MID_COL[2], BG_COL[2])).astype(np.uint8)

    # Faint grid overlay at low alpha to reinforce "measurement" aesthetic
    grid_spacing = 80
    grid_mask = ((np.arange(h_sim)[:, np.newaxis] % grid_spacing == 0) |
                 (np.arange(w_sim)[np.newaxis, :] % grid_spacing == 0))
    grid_alpha = 18
    r_ch = np.where(grid_mask, np.clip(r_ch.astype(int) + grid_alpha, 0, 255), r_ch).astype(np.uint8)
    g_ch = np.where(grid_mask, np.clip(g_ch.astype(int) + grid_alpha, 0, 255), g_ch).astype(np.uint8)
    b_ch = np.where(grid_mask, np.clip(b_ch.astype(int) + grid_alpha, 0, 255), b_ch).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != h_sim or w_buf != w_sim:
        scale_y = h_buf // h_sim
        scale_x = w_buf // w_sim
        r_ch = np.repeat(np.repeat(r_ch, scale_y, axis=0), scale_x, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, scale_y, axis=0), scale_x, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, scale_y, axis=0), scale_x, axis=1)

    alpha = np.full((h_buf, w_buf), 255, dtype=np.uint8)
    py5.np_pixels[:, :, 0] = alpha
    py5.np_pixels[:, :, 1] = r_ch
    py5.np_pixels[:, :, 2] = g_ch
    py5.np_pixels[:, :, 3] = b_ch
    py5.update_np_pixels()


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

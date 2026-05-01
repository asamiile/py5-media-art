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

pixels_arr = None

# Random warp parameters — unique every run
rng = np.random.default_rng()
P = rng.uniform(0, np.pi * 2, (6, 4))   # phase offsets (6 layers × 4 params)
F = rng.uniform(1.5, 5.5, (6, 2))       # frequencies


def warp(u, v, freq, phases, amp):
    """One domain-warp step: distort coordinates using sine/cosine fields."""
    wu = u + np.sin(v * freq[0] + phases[0]) * amp + np.cos(u * freq[1] + phases[1]) * amp * 0.6
    wv = v + np.cos(u * freq[0] + phases[2]) * amp + np.sin(v * freq[1] + phases[3]) * amp * 0.6
    return wu, wv


def build_image(width, height):
    # Normalized coordinates [-1.5, 1.5] × [-1.5, 1.5]
    x = np.linspace(-1.5, 1.5, width, dtype=np.float32)
    y = np.linspace(-1.5 / (width / height), 1.5 / (width / height), height, dtype=np.float32)
    U, V = np.meshgrid(x, y)

    # Three independent warp chains → sampled at different phases → RGB channels
    results = []
    for ch in range(3):
        u, v = U.copy(), V.copy()
        base = ch * 2  # use different parameter rows per channel

        # Warp layer 1 — large-scale distortion
        u, v = warp(u, v, F[base], P[base], amp=0.55)
        # Warp layer 2 — medium-scale
        u, v = warp(u, v, F[base + 1], P[base + 1], amp=0.30)
        # Warp layer 3 — fine detail (shared fine frequency)
        u, v = warp(u, v, F[4], P[4], amp=0.15)

        # Sample a harmonic function of the warped coords
        val = (
            np.sin(u * 3.5 + v * 2.1 + P[5, ch])
            + np.sin(np.sqrt(u ** 2 + v ** 2) * 4.8 + P[5, ch + 1])
        ) * 0.5  # range approx [-1, 1]

        results.append(val)

    r_raw, g_raw, b_raw = results

    # Palette: map each channel's field through a rich color transform
    # Hue rotation: mix channels for cross-contamination → avoids flat single-hue look
    r = np.clip((r_raw * 0.7 + g_raw * 0.3 + 1.0) / 2.0 * 255, 0, 255).astype(np.uint8)
    g = np.clip((g_raw * 0.5 + b_raw * 0.5 + 1.0) / 2.0 * 255, 0, 255).astype(np.uint8)
    b = np.clip((b_raw * 0.7 + r_raw * 0.3 + 1.0) / 2.0 * 255, 0, 255).astype(np.uint8)

    alpha = np.full((height, width), 255, dtype=np.uint8)
    return np.stack([alpha, r, g, b], axis=-1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    pixels_arr = build_image(SIZE[0], SIZE[1])


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

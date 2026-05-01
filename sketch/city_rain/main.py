from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import save_preview_pil
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

RNG = np.random.default_rng()

# ── Palette ───────────────────────────────────────────────────────────────────
WIN_COLORS = [
    (0.90, 0.74, 0.28),   # warm amber
    (0.52, 0.72, 0.94),   # cool blue-white
    (0.92, 0.48, 0.10),   # orange
    (0.84, 0.84, 0.78),   # neutral white
    (0.78, 0.90, 0.55),   # pale green (fluorescent office)
]
NEON_COLORS = [
    (1.00, 0.05, 0.45),   # hot pink
    (0.04, 0.85, 1.00),   # electric cyan
    (1.00, 0.58, 0.04),   # amber neon
    (0.60, 0.10, 1.00),   # ultraviolet purple
    (0.10, 1.00, 0.50),   # neon green
]

# Building depth layers: (body_brightness, lit_fraction, height_fraction_max)
LAYERS = [
    (0.032, 0.10, 0.50),   # far back, dim, middling
    (0.052, 0.18, 0.70),
    (0.068, 0.26, 0.85),
    (0.085, 0.35, 0.96),   # front, brighter, tallest
]


def make_scene(W, H):
    scene = np.zeros((H, W, 3), dtype=np.float32)

    sky_h = int(H * 0.60)       # horizon y-position
    pave_h = H - sky_h

    # ── Sky ──────────────────────────────────────────────────────────────────
    ys = (np.arange(sky_h) / sky_h)[:, np.newaxis]
    scene[:sky_h, :, 0] = 0.006 + ys * 0.018
    scene[:sky_h, :, 1] = 0.010 + ys * 0.026
    scene[:sky_h, :, 2] = 0.022 + ys * 0.055

    # ── Buildings (4 depth layers, back→front) ────────────────────────────
    all_buildings = []
    for layer_idx, (bright, lit_frac, h_max) in enumerate(LAYERS):
        x = int(RNG.integers(0, 30))
        while x < W:
            bw = int(RNG.uniform(50, 190))
            bh = int(sky_h * RNG.uniform(0.22, h_max))
            by = sky_h - bh
            bx = x
            bx2 = min(bx + bw, W)

            # Body fill with slight per-building brightness variation
            dr = RNG.uniform(-0.006, 0.012)
            cr = bright + dr * 0.85
            cg = bright + dr * 0.90
            cb = bright + dr * 1.00
            scene[by:sky_h, bx:bx2, 0] = cr
            scene[by:sky_h, bx:bx2, 1] = cg
            scene[by:sky_h, bx:bx2, 2] = cb

            # Subtle top-edge highlight (parapet)
            ph = min(3, bh)
            hl = bright * 1.6
            scene[by:by+ph, bx:bx2] = [hl*0.9, hl*0.92, hl]

            all_buildings.append((bx, by, bx2, sky_h, lit_frac))
            x += bw + int(RNG.uniform(0, 18))

    # ── Windows ──────────────────────────────────────────────────────────────
    for (bx, by, bx2, bottom, lit_frac) in all_buildings:
        for wy in range(by + 8, bottom - 4, 11):
            for wx in range(bx + 5, bx2 - 5, 9):
                if RNG.random() < lit_frac:
                    wc = WIN_COLORS[RNG.integers(len(WIN_COLORS))]
                    br = float(RNG.uniform(0.55, 1.0))
                    x1 = wx;  x2 = min(wx + 5, bx2 - 2)
                    y1 = wy;  y2 = min(wy + 7, bottom - 2)
                    scene[y1:y2, x1:x2, 0] = wc[0] * br
                    scene[y1:y2, x1:x2, 1] = wc[1] * br
                    scene[y1:y2, x1:x2, 2] = wc[2] * br

    # ── Neon signs ────────────────────────────────────────────────────────────
    for _ in range(int(RNG.integers(5, 9))):
        nc = NEON_COLORS[RNG.integers(len(NEON_COLORS))]
        nx  = int(RNG.uniform(30, W - 160))
        ny  = int(RNG.uniform(sky_h * 0.30, sky_h * 0.85))
        nw  = int(RNG.uniform(30, 120))
        nh  = int(RNG.uniform(5, 12))
        x1, x2 = nx, min(nx + nw, W)
        y1, y2 = ny, min(ny + nh, sky_h)
        scene[y1:y2, x1:x2, 0] = nc[0]
        scene[y1:y2, x1:x2, 1] = nc[1]
        scene[y1:y2, x1:x2, 2] = nc[2]

    # ── Pavement (dark wet asphalt) ───────────────────────────────────────────
    ys_p = (np.arange(pave_h) / pave_h)[:, np.newaxis]
    scene[sky_h:, :, 0] = 0.018 - ys_p * 0.010
    scene[sky_h:, :, 1] = 0.022 - ys_p * 0.012
    scene[sky_h:, :, 2] = 0.040 - ys_p * 0.020

    # ── Wet pavement reflection ───────────────────────────────────────────────
    # Flip sky section vertically; blur asymmetrically; add ripple distortion
    sky_copy = scene[:sky_h, :, :].copy()
    refl     = sky_copy[::-1, :, :]                     # vertical flip

    # Asymmetric blur: much wider horizontally (ripple spread)
    refl_blur = gaussian_filter(refl, sigma=[1.0, 5.5, 0])

    # Horizontal ripple warp
    ys_d    = np.arange(pave_h, dtype=np.float32)
    shift_px = (
        6.0 * np.sin(ys_d * 0.14 + RNG.uniform(0, np.pi))
        * np.sin(ys_d * 0.053 + RNG.uniform(0, np.pi))
    ).astype(np.float32)

    refl_h = min(pave_h, sky_h)
    for y in range(refl_h):
        fade  = np.exp(-y * 4.5 / refl_h)            # rapid fade toward bottom
        src_y = min(y, sky_h - 1)
        d     = int(shift_px[y])
        row   = np.roll(refl_blur[src_y], d, axis=0)
        scene[sky_h + y] = np.maximum(scene[sky_h + y], row * fade * 0.62)

    # Narrow horizon reflection strip (very bright for neon puddles)
    horizon_refl = sky_copy[-6:, :, :].mean(axis=0)   # average last 6 rows of sky
    blur_hr = gaussian_filter(horizon_refl, sigma=[8, 0])
    scene[sky_h:sky_h+3, :] = np.maximum(scene[sky_h:sky_h+3, :], blur_hr * 0.85)

    # ── Rain streaks ─────────────────────────────────────────────────────────
    # Exponential field + directional gaussian → natural vertical streaks
    rain = RNG.exponential(0.006, size=(H, W)).astype(np.float32)
    rain = gaussian_filter(rain, sigma=[14, 0.35])
    rain = rain.clip(0, 0.14)
    # Slight diagonal angle: shift upper part right by a few px
    rain = np.roll(rain, -4, axis=1)   # approximate slant
    scene[:, :, 0] += rain * 0.50
    scene[:, :, 1] += rain * 0.62
    scene[:, :, 2] += rain * 0.88

    # ── Bloom (light halos from bright sources) ───────────────────────────────
    bright_mask = (scene - 0.18).clip(0, None)
    bloom       = gaussian_filter(bright_mask, sigma=14)
    scene       = (scene + bloom * 0.55).clip(0, None)

    # ── Horizon atmospheric glow ──────────────────────────────────────────────
    glow_y = np.exp(-((np.arange(sky_h) - sky_h * 0.92) ** 2) / (sky_h * 40))[:, np.newaxis]
    scene[:sky_h, :, 0] += glow_y * 0.030
    scene[:sky_h, :, 1] += glow_y * 0.020
    scene[:sky_h, :, 2] += glow_y * 0.010

    # ── Vignette ─────────────────────────────────────────────────────────────
    xs_n = np.linspace(-1, 1, W)
    ys_n = np.linspace(-1, 1, H)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.38 * (xg ** 2 + yg ** 2)).clip(0.50, 1.0)[:, :, np.newaxis]
    scene *= vignette

    # ── Final tone map ────────────────────────────────────────────────────────
    scene = np.power(scene.clip(0, 1), 0.86)
    return scene


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    scene = make_scene(W, H)
    result_u8 = (scene * 255).astype(np.uint8)
    save_preview_pil(result_u8, SKETCH_DIR, filename="preview.png", mode="RGB")
    py5.exit_sketch()


py5.run_sketch()

"""
bonfire — The hypnotic beauty of fire: chaos organized by rising heat.

Fractal noise domain-warping creates organic flame tongues: a base heat
field is horizontally distorted by a second noise layer (simulating turbulent
air currents), then vertically tapered so fire fades to black at its tips.
Palette runs black → deep crimson → orange → amber → white-hot core.
"""

from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.sizes import get_sizes
from lib.paths import sketch_dir
from lib.preview import save_preview_pil, exit_sketch

SKETCH_DIR = sketch_dir(__file__)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

RNG = np.random.default_rng()


def build_fire_palette():
    """Map 0-255 → fire RGB: black → crimson → orange → amber → white-hot."""
    pal = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        t = i / 255.0
        if t < 0.22:
            s = t / 0.22
            r, g, b = int(s * 160), 0, 0
        elif t < 0.45:
            s = (t - 0.22) / 0.23
            r, g, b = int(160 + s * 95), int(s * 80), 0
        elif t < 0.68:
            s = (t - 0.45) / 0.23
            r, g, b = 255, int(80 + s * 145), 0
        else:
            s = (t - 0.68) / 0.32
            r, g, b = 255, int(225 + s * 30), int(s * 210)
        pal[i] = [r, g, b]
    return pal


PALETTE = build_fire_palette()


def fbm(coords_y, coords_x, octaves=5, persistence=0.5, lacunarity=2.0):
    """Smooth fractal noise via superposed sine/cosine harmonics (no scipy dep)."""
    # Determine broadcast shape before accumulating
    shape = np.broadcast(coords_y, coords_x).shape
    result = np.zeros(shape, dtype=np.float64)
    amp, freq = 1.0, 1.0
    for _ in range(octaves):
        phase_x = RNG.uniform(0, 2 * np.pi)
        phase_y = RNG.uniform(0, 2 * np.pi)
        result += amp * (
            np.sin(coords_x * freq + phase_x) *
            np.cos(coords_y * freq + phase_y)
        )
        amp  *= persistence
        freq *= lacunarity
    # Normalise to [0, 1]
    result -= result.min()
    mx = result.max()
    if mx > 0:
        result /= mx
    return result


def make_bonfire(W, H):
    # Coordinate grids (normalised)
    xs = np.linspace(0, 5 * np.pi, W)[np.newaxis, :]
    ys = np.linspace(0, 5 * np.pi, H)[:, np.newaxis]

    # ── Warp field: horizontal distortion → organic flame tongues ─────────────
    warp1 = fbm(ys * 1.0, xs * 0.8, octaves=4) * 2.8
    warp2 = fbm(ys * 1.8 + 5.0, xs * 0.6 + 3.0, octaves=3) * 1.4

    xs_warped = xs + warp1 + warp2

    # ── Base heat field ────────────────────────────────────────────────────────
    heat_raw = fbm(ys * 1.2, xs_warped * 1.0, octaves=5, persistence=0.55)

    # ── Vertical taper: 0=top(cold), 1=bottom(hot) ────────────────────────────
    ys_norm = np.linspace(0.0, 1.0, H)[:, np.newaxis]
    taper = ys_norm ** 0.45   # very gentle → flames reach ~75% up canvas
    heat_field = heat_raw * taper

    # ── Horizontal focus: bonfire column ─────────────────────────────────────
    xs_norm = np.linspace(-1.0, 1.0, W)[np.newaxis, :]
    sigma = 0.55 * ys_norm + 0.18   # wide at base, narrower at top
    h_focus = np.exp(-0.5 * (xs_norm / sigma) ** 2)
    heat_field *= h_focus

    # ── Contrast stretch ───────────────────────────────────────────────────────
    heat_field = np.clip((heat_field - 0.08) / 0.92, 0.0, 1.0)
    heat_field **= 1.15

    # ── Render via palette ─────────────────────────────────────────────────────
    heat_u8 = (heat_field * 255).astype(np.uint8)
    rgb = PALETTE[heat_u8]    # (H, W, 3)

    return rgb


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    result = make_bonfire(W, H)
    save_preview_pil(result, SKETCH_DIR, filename="preview.png", mode="RGB")
    exit_sketch()


py5.run_sketch()

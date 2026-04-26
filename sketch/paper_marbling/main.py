from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
import py5

SKETCH_DIR = Path(__file__).parent

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

RNG = np.random.default_rng()

# ── Peacock / Byzantine palette ───────────────────────────────────────────────
# Rich jewel tones evocative of illuminated manuscripts and Ottoman ebru
PALETTE = np.array([
    [0.04, 0.33, 0.54],   # peacock blue
    [0.92, 0.88, 0.76],   # warm cream
    [0.08, 0.52, 0.34],   # emerald green
    [0.82, 0.62, 0.16],   # antique gold
    [0.46, 0.08, 0.20],   # deep burgundy
    [0.02, 0.18, 0.38],   # midnight navy
], dtype=np.float32)


def drop_expand(wx, wy, cx, cy, r):
    """
    Ink-drop expansion: circular push of existing ink outward.
    Formula: new_d = sqrt(d² + r²)  →  scale = new_d / d
    """
    dx  = wx - cx
    dy  = wy - cy
    d2  = dx * dx + dy * dy
    d   = np.sqrt(d2 + 1e-12)
    new_d = np.sqrt(d2 + r * r)
    s   = new_d / d
    return cx + dx * s, cy + dy * s


def make_marbling(W, H):
    # Normalised coordinate grid [0, 1]
    xs = np.linspace(0.0, 1.0, W, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, H, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    wx, wy = xx.copy(), yy.copy()

    # ── Step 1: ink-drop additions (7–11 drops) ───────────────────────────────
    n_drops = int(RNG.integers(7, 12))
    for k in range(n_drops):
        cx = RNG.uniform(0.05, 0.95)
        cy = RNG.uniform(0.05, 0.95)
        r  = RNG.uniform(0.04, 0.14)
        wx, wy = drop_expand(wx, wy, cx, cy, r)

    # ── Step 2: comb strokes (alternating x / y) ─────────────────────────────
    # Each stroke: sinusoidal displacement of the coordinate perpendicular to
    # the stroke direction, creating the characteristic ebru wave pattern.
    n_strokes = int(RNG.integers(5, 9))
    amp_base  = RNG.uniform(0.030, 0.075)

    for i in range(n_strokes):
        decay = 0.82 ** i                        # amplitude decreases each pass
        A     = amp_base * decay * RNG.uniform(0.7, 1.3)
        lam   = RNG.uniform(0.07, 0.22)          # spatial wavelength
        phi   = RNG.uniform(0.0, 2 * np.pi)

        if i % 2 == 0:
            wy = wy + A * np.sin(2.0 * np.pi * wx / lam + phi)
        else:
            wx = wx + A * np.sin(2.0 * np.pi * wy / lam + phi)

    # ── Step 3: colour lookup ─────────────────────────────────────────────────
    # Map warped y to a smooth palette.
    # n_colors palette colours repeat over n_repeats stripe cycles.
    n_colors  = len(PALETTE)
    n_repeats = 5
    t         = (wy % 1.0) * (n_colors * n_repeats)   # continuous colour index

    i_lo = t.astype(np.int32) % n_colors
    i_hi = (i_lo + 1) % n_colors
    frac = (t - np.floor(t)).astype(np.float32)[:, :, np.newaxis]

    color = (1.0 - frac) * PALETTE[i_lo] + frac * PALETTE[i_hi]  # (H, W, 3)

    # ── Step 4: subtle paper texture ─────────────────────────────────────────
    grain = RNG.uniform(-0.018, 0.018, size=(H, W, 3)).astype(np.float32)
    grain = gaussian_filter(grain, sigma=[0.5, 0.5, 0])   # very fine grain
    color = (color + grain).clip(0.0, 1.0)

    # ── Step 5: vignette ─────────────────────────────────────────────────────
    ys_n = np.linspace(-1.0, 1.0, H, dtype=np.float32)
    xs_n = np.linspace(-1.0, 1.0, W, dtype=np.float32)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.30 * (xg ** 2 + yg ** 2)).clip(0.62, 1.0)
    color   *= vignette[:, :, np.newaxis]

    return color.clip(0.0, 1.0)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    result    = make_marbling(W, H)
    result_u8 = (result * 255.0).astype(np.uint8)
    Image.fromarray(result_u8, "RGB").save(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()


py5.run_sketch()

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

# Theme: "Magnetic curtain" — ionized plasma sheets in polar night
# Palette: deep near-black sky, electric green → cold teal → deep violet

# Aurora color stops (along horizontal axis, normalized 0–1)
# Each column gets a color from this gradient based on its x-position
AURORA_COLORS = np.array([
    [0.06,  0.82, 0.35],   # electric green  #10d258
    [0.06,  0.75, 0.72],   # cold teal       #10c0b8
    [0.22,  0.40, 0.75],   # blue-violet     #3866c0
    [0.52,  0.15, 0.72],   # deep violet     #8526b8
    [0.75,  0.18, 0.52],   # magenta rim     #c02e84
], dtype=np.float32)

N_RIBBONS = 180   # vertical ribbons across canvas width
N_LAYERS  = 5    # depth layers — each slightly different frequency/phase


def aurora_lut(x_norm):
    """Interpolate aurora color stops for a given normalized x position."""
    n = len(AURORA_COLORS)
    t = x_norm * (n - 1)
    lo = np.floor(t).astype(int).clip(0, n - 2)
    hi = lo + 1
    f = (t - lo)[:, np.newaxis]
    return AURORA_COLORS[lo] * (1 - f) + AURORA_COLORS[hi] * f


def setup():
    py5.size(*SIZE)
    py5.background(3, 4, 10)   # #030408 deep near-black

    rng = np.random.default_rng()
    W, H = SIZE[0], SIZE[1]

    # --- Stars (scattered, cold white) ---
    n_stars = 1200
    sx = rng.integers(0, W, n_stars)
    sy = rng.integers(0, int(H * 0.80), n_stars)  # stars only in upper 80%
    brightness = rng.uniform(120, 255, n_stars).astype(int)
    sizes = rng.choice([1.0, 1.0, 1.0, 2.0], n_stars)

    py5.no_stroke()
    for i in range(n_stars):
        b = brightness[i]
        # Faint blue tint for cold stars
        py5.fill(b, b, min(255, b + 30), 240)
        sz = sizes[i]
        py5.ellipse(sx[i], sy[i], sz, sz)

    # --- Aurora curtains ---
    # Ribbons are vertical columns of stacked sine-wave segments
    # Aurora occupies the upper 55–75% of the canvas height
    aurora_top    = H * 0.05
    aurora_bottom = H * 0.75

    ribbon_xs = np.linspace(0, W, N_RIBBONS, endpoint=False)
    x_norms = ribbon_xs / W

    colors = aurora_lut(x_norms)  # (N_RIBBONS, 3)

    # Layer parameters — each layer has a different horizontal frequency and phase
    layer_params = [
        # (freq_x, freq_y, phase_offset, amplitude, alpha_base, weight)
        (3.5, 0.012, 0.0,         40, 38, 3.0),
        (5.2, 0.018, np.pi * 0.4, 28, 30, 2.0),
        (2.8, 0.008, np.pi * 1.1, 55, 24, 4.0),
        (7.0, 0.025, np.pi * 0.7, 20, 18, 1.5),
        (1.5, 0.006, np.pi * 1.8, 70, 16, 5.0),
    ]

    # Precompute y-positions
    ys = np.linspace(aurora_top, aurora_bottom, 300)

    for freq_x, freq_y, phase, amp, alpha_base, weight in layer_params:
        py5.no_fill()
        py5.stroke_weight(weight)

        for ri in range(N_RIBBONS):
            x = ribbon_xs[ri]
            col = colors[ri]
            r_col = int(col[0] * 255)
            g_col = int(col[1] * 255)
            b_col = int(col[2] * 255)

            # Vertical brightness envelope: tapers at top and bottom of aurora band
            for yi in range(len(ys) - 1):
                y0 = ys[yi]
                y1 = ys[yi + 1]

                # Local x-offset from sine wave (curtain waviness)
                x_off0 = amp * np.sin(freq_x * x / W * np.pi * 2 + freq_y * y0 + phase)
                x_off1 = amp * np.sin(freq_x * x / W * np.pi * 2 + freq_y * y1 + phase)

                # Vertical fade: brighter in middle of aurora band
                t_vert = (y0 - aurora_top) / (aurora_bottom - aurora_top)
                fade = np.sin(t_vert * np.pi) ** 0.6   # peak around 60% from top

                alpha = int(alpha_base * fade)
                if alpha < 2:
                    continue

                py5.stroke(r_col, g_col, b_col, alpha)
                py5.line(x + x_off0, y0, x + x_off1, y1)

    # --- Ground horizon haze ---
    # Faint green glow near horizon
    py5.no_stroke()
    for row in range(int(H * 0.72), int(H * 0.88)):
        t = (row - H * 0.72) / (H * 0.16)
        alpha = int(22 * (1 - t))
        if alpha < 1:
            break
        py5.fill(20, 200, 90, alpha)
        py5.rect(0, row, W, 1)

    # Dark foreground silhouette (tree line)
    horizon_y = int(H * 0.85)
    py5.fill(2, 3, 8)
    py5.no_stroke()
    py5.rect(0, horizon_y, W, H - horizon_y)

    # Rough tree silhouettes (simple triangular bumps)
    tree_rng = np.random.default_rng(42)  # fixed seed for deterministic tree line
    x_pos = 0
    while x_pos < W:
        tree_w = tree_rng.integers(18, 55)
        tree_h = tree_rng.integers(20, 80)
        ty = horizon_y - tree_h
        # Simple triangle for conifer shape
        py5.fill(2, 3, 8)
        py5.triangle(x_pos, horizon_y, x_pos + tree_w // 2, ty, x_pos + tree_w, horizon_y)
        x_pos += tree_rng.integers(4, 20)


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

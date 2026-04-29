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

# Theme: "Vortex ballet" — each smoke ring is a pair of counter-rotating point
# vortices; 50k particles per ring trace the Biot-Savart induced flow paths
# under mutual induction; density accumulation reveals the toroidal roll.

BG_COL  = (6, 5, 12)
SEP     = 0.10      # half-distance between vortex pair in unit coords
GAMMA   = 1.0       # circulation strength
N_PER   = 50_000    # particles per ring
N_STEPS = 200
DT      = 0.016

# Rings: (center_x, center_y, r, g, b)
RINGS = [
    (-0.52,  0.02,  55, 145, 245),   # left  — cerulean
    ( 0.00, -0.05, 245, 195,  45),   # center — gold
    ( 0.52,  0.02,  45, 230, 155),   # right  — mint
]

X_RANGE = 1.15
Y_RANGE = 0.60


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    n_rings = len(RINGS)
    N_TOTAL = N_PER * n_rings

    # ── Build vortex array ────────────────────────────────────────────────────
    vxpos = np.empty(2 * n_rings, dtype=np.float64)
    vypos = np.empty(2 * n_rings, dtype=np.float64)
    ga    = np.empty(2 * n_rings, dtype=np.float64)
    for ri, (cx, cy, *_) in enumerate(RINGS):
        vxpos[2*ri]   = cx + SEP;  vypos[2*ri]   = cy;  ga[2*ri]   = +GAMMA
        vxpos[2*ri+1] = cx - SEP;  vypos[2*ri+1] = cy;  ga[2*ri+1] = -GAMMA

    # ── Seed particles ────────────────────────────────────────────────────────
    rng = np.random.default_rng(7)
    px_parts = []
    py_parts = []
    for cx, cy, *_ in RINGS:
        sigma = SEP * 0.38
        half  = N_PER // 2
        # cloud near each vortex core + some in wider halo
        x1 = cx + SEP + rng.normal(0, sigma, half)
        y1 = cy       + rng.normal(0, sigma, half)
        x2 = cx - SEP + rng.normal(0, sigma, N_PER - half)
        y2 = cy       + rng.normal(0, sigma, N_PER - half)
        px_parts.append(np.concatenate([x1, x2]))
        py_parts.append(np.concatenate([y1, y2]))

    px = np.concatenate(px_parts).astype(np.float64)
    py = np.concatenate(py_parts).astype(np.float64)

    # Per-particle color weights (fixed, one per ring)
    rw = np.concatenate([np.full(N_PER, r) for _, _, r, g, b in RINGS]).astype(np.float32)
    gw = np.concatenate([np.full(N_PER, g) for _, _, r, g, b in RINGS]).astype(np.float32)
    bw = np.concatenate([np.full(N_PER, b) for _, _, r, g, b in RINGS]).astype(np.float32)

    # ── Density accumulators ──────────────────────────────────────────────────
    dens_r = np.zeros(H * W, dtype=np.float64)
    dens_g = np.zeros(H * W, dtype=np.float64)
    dens_b = np.zeros(H * W, dtype=np.float64)

    # ── Simulation + accumulation ─────────────────────────────────────────────
    for _ in range(N_STEPS):
        dx = px[:, None] - vxpos[None, :]   # (N, 2n_rings)
        dy = py[:, None] - vypos[None, :]
        r2 = dx**2 + dy**2 + 1e-5
        u  = (-ga[None, :] * dy / (2 * np.pi * r2)).sum(axis=1)
        v  = ( ga[None, :] * dx / (2 * np.pi * r2)).sum(axis=1)
        px += u * DT
        py += v * DT

        sx = ((px + X_RANGE) / (2 * X_RANGE) * W).astype(np.int32)
        sy = ((py + Y_RANGE) / (2 * Y_RANGE) * H).astype(np.int32)
        valid = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
        idx   = (sy[valid] * W + sx[valid]).astype(np.int64)

        dens_r += np.bincount(idx, weights=rw[valid], minlength=H * W)
        dens_g += np.bincount(idx, weights=gw[valid], minlength=H * W)
        dens_b += np.bincount(idx, weights=bw[valid], minlength=H * W)

    dens_r = dens_r.reshape(H, W).astype(np.float32)
    dens_g = dens_g.reshape(H, W).astype(np.float32)
    dens_b = dens_b.reshape(H, W).astype(np.float32)

    # ── Tone mapping ──────────────────────────────────────────────────────────
    dens_r = np.log1p(dens_r / 255.0)
    dens_g = np.log1p(dens_g / 255.0)
    dens_b = np.log1p(dens_b / 255.0)

    peak = max(dens_r.max(), dens_g.max(), dens_b.max()) + 1e-8
    scale = 255.0 / peak

    r_ch = np.clip(dens_r * scale, 0, 255).astype(np.uint8)
    g_ch = np.clip(dens_g * scale, 0, 255).astype(np.uint8)
    b_ch = np.clip(dens_b * scale, 0, 255).astype(np.uint8)

    # Fill dark background where no particles landed
    zero = (r_ch == 0) & (g_ch == 0) & (b_ch == 0)
    r_ch[zero] = BG_COL[0]
    g_ch[zero] = BG_COL[1]
    b_ch[zero] = BG_COL[2]

    # ── Write to py5 pixel buffer ─────────────────────────────────────────────
    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != H or w_buf != W:
        r_ch = np.repeat(np.repeat(r_ch, 2, axis=0), 2, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, 2, axis=0), 2, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, 2, axis=0), 2, axis=1)

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 2] = g_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 3] = b_ch[:h_buf, :w_buf]
    py5.update_np_pixels()


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

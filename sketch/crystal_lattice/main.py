"""
crystal_lattice — The invisible geometric order hidden inside matter.

Atoms arranging into a perfect lattice, revealed through X-ray diffraction
spots that betray the deep symmetry within.  A reciprocal-space diffraction
pattern rendered from first principles: lattice → structure factor → intensity.
"""

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
BG_COLOR     = np.array([0.022, 0.025, 0.055])      # deep midnight
SAPPHIRE     = np.array([0.10, 0.16, 0.30])          # deep sapphire
CYAN_GLOW    = np.array([0.25, 0.88, 0.82])          # electric cyan
GOLD_PEAK    = np.array([1.00, 0.96, 0.84])          # warm white-gold
DIM_RING     = np.array([0.06, 0.10, 0.20])          # dim ring color


def make_diffraction(W, H):
    """Generate a 2D X-ray diffraction pattern from a crystal lattice."""

    # ── Step 1: Crystal lattice basis vectors ─────────────────────────────────
    lattice_type = RNG.choice(["hexagonal", "square", "oblique", "rectangular"])

    if lattice_type == "hexagonal":
        a1 = np.array([1.0, 0.0])
        a2 = np.array([0.5, np.sqrt(3) / 2])
    elif lattice_type == "square":
        a1 = np.array([1.0, 0.0])
        a2 = np.array([0.0, 1.0])
    elif lattice_type == "rectangular":
        ratio = RNG.uniform(1.3, 1.8)
        a1 = np.array([1.0, 0.0])
        a2 = np.array([0.0, ratio])
    else:
        angle = RNG.uniform(55, 80) * np.pi / 180
        ratio = RNG.uniform(0.8, 1.3)
        a1 = np.array([1.0, 0.0])
        a2 = np.array([ratio * np.cos(angle), ratio * np.sin(angle)])

    # ── Step 2: Reciprocal lattice vectors ────────────────────────────────────
    det = a1[0] * a2[1] - a1[1] * a2[0]
    b1  = 2 * np.pi * np.array([ a2[1], -a2[0]]) / det
    b2  = 2 * np.pi * np.array([-a1[1],  a1[0]]) / det

    # ── Step 3: Generate reciprocal lattice points ────────────────────────────
    max_index = 12
    h_range = np.arange(-max_index, max_index + 1)
    hh, kk = np.meshgrid(h_range, h_range)
    hh = hh.ravel()
    kk = kk.ravel()

    gx = hh * b1[0] + kk * b2[0]
    gy = hh * b1[1] + kk * b2[1]

    # ── Step 4: Structure factor with multi-atom basis ────────────────────────
    n_atoms = RNG.integers(2, 4)
    basis_atoms = RNG.uniform(0, 1, size=(n_atoms, 2)).astype(np.float64)
    basis_atoms[0] = [0, 0]
    f_atoms = RNG.uniform(0.6, 1.0, size=n_atoms)

    F_real = np.zeros(len(hh), dtype=np.float64)
    F_imag = np.zeros(len(hh), dtype=np.float64)

    for j in range(n_atoms):
        rj = basis_atoms[j, 0] * a1 + basis_atoms[j, 1] * a2
        phase = gx * rj[0] + gy * rj[1]
        F_real += f_atoms[j] * np.cos(phase)
        F_imag -= f_atoms[j] * np.sin(phase)

    intensity = F_real**2 + F_imag**2

    # Very gentle Debye-Waller thermal damping
    g_mag_sq = gx**2 + gy**2
    B_factor = RNG.uniform(0.0001, 0.0004)
    intensity *= np.exp(-B_factor * g_mag_sq)

    # Normalize
    intensity /= (intensity.max() + 1e-12)

    # ── Step 5: Map to pixel coordinates — SPREAD across canvas ───────────────
    g_max = np.sqrt(g_mag_sq.max()) + 1e-12
    # Use larger scale to spread spots to ~85% of canvas
    scale  = 0.82 * min(W, H) / g_max

    px = (W / 2 + gx * scale).astype(np.float64)
    py_coord = (H / 2 - gy * scale).astype(np.float64)

    # Filter to visible spots with any meaningful intensity
    visible = (
        (px > -40) & (px < W + 40) &
        (py_coord > -40) & (py_coord < H + 40) &
        (intensity > 0.001)
    )
    px        = px[visible]
    py_coord  = py_coord[visible]
    intensity_vis = intensity[visible]

    # ── Step 6: Render ────────────────────────────────────────────────────────
    canvas = np.zeros((H, W, 3), dtype=np.float64)
    canvas[:] = BG_COLOR

    # Subtle film-grain detector noise
    noise = RNG.normal(0, 0.008, size=(H, W))
    noise = gaussian_filter(noise, sigma=0.8)
    for c in range(3):
        canvas[:, :, c] += noise

    # Concentric Laue zone rings
    yy_grid, xx_grid = np.mgrid[0:H, 0:W]
    cx, cy = W / 2.0, H / 2.0
    dist_from_center = np.sqrt((xx_grid - cx)**2 + (yy_grid - cy)**2)

    ring_radii = np.linspace(scale * 0.3, min(W, H) * 0.49, 12)
    for r in ring_radii:
        ring_mask = np.exp(-0.5 * ((dist_from_center - r) / 0.8)**2)
        for c in range(3):
            canvas[:, :, c] += ring_mask * DIM_RING[c] * 0.12

    # Sort by intensity (dim first)
    order = np.argsort(intensity_vis)
    px = px[order]
    py_coord = py_coord[order]
    intensity_vis = intensity_vis[order]

    # Draw spots
    for i in range(len(px)):
        x0, y0 = px[i], py_coord[i]
        inten = intensity_vis[i]

        # Spot size: even dim spots should be visible
        sigma = 3.0 + 7.0 * inten**0.35

        r = int(sigma * 5) + 1
        x_lo = max(0, int(x0 - r))
        x_hi = min(W, int(x0 + r + 1))
        y_lo = max(0, int(y0 - r))
        y_hi = min(H, int(y0 + r + 1))

        if x_hi <= x_lo or y_hi <= y_lo:
            continue

        lx = np.arange(x_lo, x_hi, dtype=np.float64) - x0
        ly = np.arange(y_lo, y_hi, dtype=np.float64) - y0
        lxx, lyy = np.meshgrid(lx, ly)
        gauss = np.exp(-0.5 * (lxx**2 + lyy**2) / (sigma**2))

        # Color gradient: sapphire → cyan → gold
        if inten < 0.12:
            t = inten / 0.12
            color = (1 - t) * SAPPHIRE * 1.5 + t * CYAN_GLOW * 0.5
        elif inten < 0.45:
            t = (inten - 0.12) / 0.33
            color = (1 - t) * CYAN_GLOW * 0.5 + t * CYAN_GLOW
        else:
            t = (inten - 0.45) / 0.55
            color = (1 - t) * CYAN_GLOW + t * GOLD_PEAK

        brightness = 0.4 + 3.0 * inten**0.5
        blob = gauss[:, :, np.newaxis] * color[np.newaxis, np.newaxis, :] * brightness
        canvas[y_lo:y_hi, x_lo:x_hi] += blob

    # ── Step 7: Central beam (restrained) ─────────────────────────────────────
    center_glow = np.exp(-0.5 * (dist_from_center / 15)**2)
    for c in range(3):
        canvas[:, :, c] += center_glow * GOLD_PEAK[c] * 0.9

    # Very subtle cross flare
    flare_x = np.exp(-0.5 * ((yy_grid - cy) / 1.2)**2) * np.exp(-np.abs(xx_grid - cx) / 350)
    flare_y = np.exp(-0.5 * ((xx_grid - cx) / 1.2)**2) * np.exp(-np.abs(yy_grid - cy) / 350)
    for c in range(3):
        canvas[:, :, c] += (flare_x + flare_y) * GOLD_PEAK[c] * 0.025

    # ── Step 8: Post-processing ───────────────────────────────────────────────
    bloom = gaussian_filter(canvas, sigma=[3, 3, 0])
    canvas = canvas + bloom * 0.18

    # Vignette
    ys_n = np.linspace(-1, 1, H, dtype=np.float64)
    xs_n = np.linspace(-1, 1, W, dtype=np.float64)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.25 * (xg**2 + yg**2)).clip(0.6, 1.0)
    canvas *= vignette[:, :, np.newaxis]

    # Tone mapping
    canvas = 1.0 - np.exp(-canvas * 2.5)

    return canvas.clip(0.0, 1.0)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    result    = make_diffraction(W, H)
    result_u8 = (result * 255).astype(np.uint8)
    save_preview_pil(result_u8, SKETCH_DIR, filename="preview.png", mode="RGB")
    py5.exit_sketch()


py5.run_sketch()

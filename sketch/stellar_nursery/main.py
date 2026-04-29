"""
stellar_nursery — The birth of stars in a vast interstellar cloud.

Cold gas and dust collapsing under gravity, lit from within by young
protostars, glowing with emission nebula colors (Hα, OIII, SII).
Multi-scale fBm noise builds the gas density field; embedded point
sources scatter light through the cloud.
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

# ── Nebula emission palette ───────────────────────────────────────────────────
# Based on narrowband astrophotography: Hubble Palette (SII-Hα-OIII)
HA_RED    = np.array([0.85, 0.12, 0.22])    # Hα hydrogen-alpha emission
OIII_TEAL = np.array([0.08, 0.50, 0.58])    # OIII oxygen-III emission
SII_AMBER = np.array([0.83, 0.58, 0.23])    # SII sulfur-II emission
STAR_WHITE = np.array([0.95, 0.92, 0.85])   # hot protostar core
BG_VOID   = np.array([0.020, 0.008, 0.032]) # cosmic void


def fbm_noise(W, H, octaves=8, persistence=0.55, lacunarity=2.0):
    """Fractional Brownian motion via spectral synthesis (FFT)."""
    # Generate white noise in frequency domain
    noise = RNG.standard_normal((H, W))
    f_noise = np.fft.fft2(noise)

    # Build frequency grid
    fy = np.fft.fftfreq(H)[:, np.newaxis]
    fx = np.fft.fftfreq(W)[np.newaxis, :]
    freq = np.sqrt(fx**2 + fy**2)
    freq[0, 0] = 1.0  # avoid div by zero

    # Apply 1/f^β power spectrum for fractal noise
    beta = 2.0 + persistence  # spectral exponent
    power = 1.0 / (freq ** beta)
    power[0, 0] = 0  # remove DC

    result = np.real(np.fft.ifft2(f_noise * np.sqrt(power)))
    result = (result - result.min()) / (result.max() - result.min() + 1e-12)
    return result


def make_nebula(W, H):
    """Render a stellar nursery emission nebula."""

    # ── Step 1: Multi-layer gas density field ─────────────────────────────────
    # Large-scale structure
    density_large = fbm_noise(W, H, octaves=6, persistence=0.50)
    # Medium-scale filaments
    density_mid = fbm_noise(W, H, octaves=7, persistence=0.60)
    # Fine detail (wisps and tendrils)
    density_fine = fbm_noise(W, H, octaves=8, persistence=0.65)

    # Combine with different weights
    density = (
        0.50 * density_large +
        0.30 * density_mid +
        0.20 * density_fine
    )
    # Enhance contrast
    density = density ** 1.3
    density = (density - density.min()) / (density.max() - density.min() + 1e-12)

    # ── Step 2: Create dark lanes (dust absorption) ───────────────────────────
    dust = fbm_noise(W, H, octaves=6, persistence=0.55)
    dust_mask = np.clip(1.0 - 2.0 * (dust ** 1.5), 0.0, 1.0)
    # Dust darkens parts of the nebula
    density *= (0.3 + 0.7 * dust_mask)

    # ── Step 3: Emission color channels ───────────────────────────────────────
    # Each emission line has slightly different spatial distribution
    ha_field = fbm_noise(W, H, octaves=7, persistence=0.55)
    oiii_field = fbm_noise(W, H, octaves=7, persistence=0.50)
    sii_field = fbm_noise(W, H, octaves=6, persistence=0.60)

    # Normalize and shape each emission
    ha_field = ha_field ** 1.2
    oiii_field = oiii_field ** 1.5   # OIII is more concentrated
    sii_field = sii_field ** 1.1

    # ── Step 4: Place protostars ──────────────────────────────────────────────
    n_stars = RNG.integers(5, 12)
    star_x = RNG.uniform(W * 0.1, W * 0.9, n_stars)
    star_y = RNG.uniform(H * 0.1, H * 0.9, n_stars)
    star_brightness = RNG.uniform(0.3, 1.0, n_stars)
    star_radius = RNG.uniform(30, 120, n_stars)  # influence radius in pixels

    # Place stars preferentially in high-density regions
    yy, xx = np.mgrid[0:H, 0:W]

    star_glow = np.zeros((H, W), dtype=np.float64)
    for i in range(n_stars):
        dx = xx - star_x[i]
        dy = yy - star_y[i]
        d = np.sqrt(dx**2 + dy**2)
        # Each star has a sharp core + wide halo
        core = np.exp(-0.5 * (d / 3.0)**2) * star_brightness[i]
        halo = star_brightness[i] / (1.0 + (d / star_radius[i])**2)
        star_glow += core * 2.0 + halo

    # Star illumination also enhances local nebula emission
    illumination = 1.0 + star_glow * 3.0

    # ── Step 5: Compose final color ───────────────────────────────────────────
    canvas = np.zeros((H, W, 3), dtype=np.float64)
    canvas[:] = BG_VOID

    # Add emission nebula layers
    # Hα (dominant warm glow)
    ha_intensity = density * ha_field * illumination * 0.7
    for c in range(3):
        canvas[:, :, c] += ha_intensity * HA_RED[c]

    # OIII (cooler regions, edges of ionization fronts)
    oiii_intensity = density * oiii_field * illumination * 0.45
    for c in range(3):
        canvas[:, :, c] += oiii_intensity * OIII_TEAL[c]

    # SII (warmer/denser knots)
    sii_intensity = density * sii_field * illumination * 0.35
    for c in range(3):
        canvas[:, :, c] += sii_intensity * SII_AMBER[c]

    # Add protostar point sources
    for c in range(3):
        canvas[:, :, c] += star_glow * STAR_WHITE[c] * 0.4

    # ── Step 6: Background stars ──────────────────────────────────────────────
    n_bg_stars = RNG.integers(800, 1500)
    bg_x = RNG.integers(0, W, n_bg_stars)
    bg_y = RNG.integers(0, H, n_bg_stars)
    bg_bright = RNG.uniform(0.1, 0.6, n_bg_stars)
    bg_color_temp = RNG.uniform(0, 1, n_bg_stars)

    for i in range(n_bg_stars):
        x, y = bg_x[i], bg_y[i]
        b = bg_bright[i]

        # Stars behind dense nebula are dimmed
        local_density = density[y, x]
        extinction = np.exp(-local_density * 3.0)
        b *= extinction

        if b < 0.02:
            continue

        # Color temperature: blue-white to yellow-orange
        t = bg_color_temp[i]
        color = (1 - t) * np.array([0.7, 0.8, 1.0]) + t * np.array([1.0, 0.85, 0.6])

        # Simple 3×3 star with bright center
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W:
                    w = 1.0 if (dx == 0 and dy == 0) else 0.2
                    canvas[ny, nx] += color * b * w

    # ── Step 7: Post-processing ───────────────────────────────────────────────
    # Multi-scale bloom (simulates telescope diffraction)
    bloom1 = gaussian_filter(canvas, sigma=[2, 2, 0])
    bloom2 = gaussian_filter(canvas, sigma=[8, 8, 0])
    bloom3 = gaussian_filter(canvas, sigma=[25, 25, 0])
    canvas = canvas + bloom1 * 0.15 + bloom2 * 0.10 + bloom3 * 0.06

    # Subtle vignette (telescope field darkening)
    ys_n = np.linspace(-1, 1, H, dtype=np.float64)
    xs_n = np.linspace(-1, 1, W, dtype=np.float64)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.30 * (xg**2 + yg**2)).clip(0.55, 1.0)
    canvas *= vignette[:, :, np.newaxis]

    # Tone mapping: HDR → display
    canvas = 1.0 - np.exp(-canvas * 1.8)

    # Slight film grain (simulates CCD noise)
    grain = RNG.normal(0, 0.012, (H, W, 3))
    canvas += grain
    
    return canvas.clip(0.0, 1.0)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    result    = make_nebula(W, H)
    result_u8 = (result * 255).astype(np.uint8)
    save_preview_pil(result_u8, SKETCH_DIR, filename="preview.png", mode="RGB")
    py5.exit_sketch()


py5.run_sketch()

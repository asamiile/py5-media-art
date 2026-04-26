from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image
import py5

SKETCH_DIR = Path(__file__).parent

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

RNG = np.random.default_rng()


def make_starfield(w, h, n_stars=8000):
    """Return (3, H, W) float32 background with stars."""
    channels = np.zeros((3, h, w), dtype=np.float64)

    # Faint nebula: two overlapping teal/violet clouds
    ys, xs = np.mgrid[0:h, 0:w]
    for _ in range(2):
        cx = w * RNG.uniform(0.25, 0.75)
        cy = h * RNG.uniform(0.2, 0.8)
        sigma = w * RNG.uniform(0.18, 0.30)
        amp = RNG.uniform(0.04, 0.08)
        blob = amp * np.exp(-((xs - cx)**2 + (ys - cy)**2) / (2 * sigma**2))
        channels[0] += blob * 0.25
        channels[1] += blob * 0.50
        channels[2] += blob * 0.90

    # Stars: scatter brightness onto integer positions, then gaussian blur per size
    temp = RNG.uniform(0.0, 1.0, size=n_stars)
    brightness = RNG.exponential(0.6, size=n_stars).clip(0, 8.0)
    sx = RNG.integers(0, w, size=n_stars)
    sy = RNG.integers(0, h, size=n_stars)

    # Color: cool/warm temperature
    r_col = np.where(temp < 0.5, 1.0, np.clip(1.0 - (temp - 0.5) * 0.5, 0.7, 1.0))
    g_col = np.clip(0.75 + temp * 0.2, 0, 1)
    b_col = np.where(temp < 0.5, np.clip(0.3 + temp * 0.6, 0, 1), 1.0)

    # Separate dim and bright stars
    dim_mask = brightness < 1.0
    bright_mask = ~dim_mask

    # Dim stars: single-pixel, tiny sigma blur
    for ch, col in zip([0, 1, 2], [r_col, g_col, b_col]):
        layer = np.zeros((h, w), dtype=np.float64)
        np.add.at(layer, (sy[dim_mask], sx[dim_mask]),
                  brightness[dim_mask] * col[dim_mask])
        channels[ch] += gaussian_filter(layer, sigma=0.6)

    # Bright stars: larger sigma proportional to brightness
    for i in np.where(bright_mask)[0]:
        b = brightness[i]
        sigma = 0.8 + b * 0.5
        for ch, col in zip([0, 1, 2], [r_col[i], g_col[i], b_col[i]]):
            layer = np.zeros((h, w), dtype=np.float64)
            layer[sy[i], sx[i]] = b * col
            channels[ch] += gaussian_filter(layer, sigma=sigma)

    # Spike diffraction on very bright stars
    for i in np.where(brightness > 3.0)[0]:
        b = brightness[i]
        x0, y0 = sx[i], sy[i]
        spike_len = int(b * 6)
        for ch, col in zip([0, 1, 2], [r_col[i], g_col[i], b_col[i]]):
            for dx in range(-spike_len, spike_len + 1):
                nx = x0 + dx
                if 0 <= nx < w:
                    v = b * col * np.exp(-(dx**2) / (b * 3.0)) * 0.25
                    channels[ch, y0, nx] += v
            for dy in range(-spike_len, spike_len + 1):
                ny = y0 + dy
                if 0 <= ny < h:
                    v = b * col * np.exp(-(dy**2) / (b * 3.0)) * 0.25
                    channels[ch, ny, x0] += v

    img = np.stack(channels, axis=-1)  # (H, W, 3)
    return img.clip(0, 1).astype(np.float32)


def apply_lensing(bg, w, h, lens_x, lens_y, r_einstein, r_horizon):
    """
    Gravitational lensing via point mass deflection.
    alpha = r_E^2 / r  (thin lens approximation).
    Uses bilinear interpolation via map_coordinates.
    """
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xs - lens_x
    dy = ys - lens_y
    r2 = dx * dx + dy * dy
    r = np.sqrt(r2)

    r_E2 = float(r_einstein) ** 2
    safe_r2 = np.where(r2 > 1.0, r2, 1.0)
    alpha = r_E2 / safe_r2

    src_x = xs + alpha * dx
    src_y = ys + alpha * dy

    # Bilinear sample each channel
    lensed = np.empty_like(bg)
    for c in range(3):
        lensed[:, :, c] = map_coordinates(
            bg[:, :, c],
            [src_y, src_x],
            order=1, mode='nearest'
        )

    # Amplification near Einstein ring
    r_E = float(r_einstein)
    ring_dist = np.abs(r - r_E)
    amplify = 1.0 + 3.5 * np.exp(-(ring_dist / (r_E * 0.10)) ** 2)
    lensed *= amplify[:, :, np.newaxis]

    # Golden Einstein ring glow
    ring_glow = 0.65 * np.exp(-(ring_dist / (r_E * 0.055)) ** 2)
    lensed[:, :, 0] += ring_glow * 1.00
    lensed[:, :, 1] += ring_glow * 0.68
    lensed[:, :, 2] += ring_glow * 0.15

    # Blue-white photon sphere halo
    photon_r = r_horizon * 1.6
    photon_glow = 0.30 * np.exp(-((r - photon_r) / (r_horizon * 0.40)) ** 2)
    lensed[:, :, 0] += photon_glow * 0.60
    lensed[:, :, 1] += photon_glow * 0.80
    lensed[:, :, 2] += photon_glow * 1.00

    # Accretion disk: orange-white horizontal band through lens center
    disk_height = r_horizon * 0.6
    disk_inner = r_horizon * 1.15
    disk_outer = r_E * 0.82
    in_disk = (np.abs(dy) < disk_height) & (r > disk_inner) & (r < disk_outer)
    disk_brightness = np.where(
        in_disk,
        np.exp(-(np.abs(dy) / (disk_height * 0.7)) ** 2) *
        np.exp(-((r - (disk_inner + disk_outer) / 2) / ((disk_outer - disk_inner) * 0.40)) ** 2) * 0.95,
        0.0
    )
    lensed[:, :, 0] += disk_brightness * 1.00
    lensed[:, :, 1] += disk_brightness * 0.50
    lensed[:, :, 2] += disk_brightness * 0.08

    # Doppler brightening: left side of disk brighter (matter orbiting)
    doppler = np.where(in_disk & (dx < 0), 1.0 + 0.5 * np.exp(-(r / (r_E * 0.5)) ** 2), 1.0)
    lensed *= doppler[:, :, np.newaxis]

    lensed = lensed.clip(0, None)

    # Event horizon: pitch black inside
    lensed[r < r_horizon] = 0.0

    return lensed


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    w, h = SIZE
    lens_x = w * 0.5
    lens_y = h * 0.5
    r_einstein = h * 0.21
    r_horizon = h * 0.044

    bg = make_starfield(w, h, n_stars=8000)
    result = apply_lensing(bg, w, h, lens_x, lens_y, r_einstein, r_horizon)

    # Tone mapping: filmic — normalize peak then apply gamma
    p99 = np.percentile(result, 99.5)
    if p99 > 0:
        result /= p99
    result = np.power(result.clip(0, 1), 0.80)

    # Mild vignette
    ys, xs = np.mgrid[0:h, 0:w]
    vignette = 1.0 - 0.25 * ((xs / w - 0.5) ** 2 + (ys / h - 0.5) ** 2) * 4
    result *= vignette.clip(0.5, 1.0)[:, :, np.newaxis]

    result_u8 = (result.clip(0, 1) * 255).astype(np.uint8)

    # Save directly via PIL (avoids Retina np_pixels size mismatch)
    Image.fromarray(result_u8, "RGB").save(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()


py5.run_sketch()

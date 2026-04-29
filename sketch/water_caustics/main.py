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


def make_wave_surface(w, h, n_waves=8):
    """
    Analytic wave superposition height field and gradients.
    Returns (dh_dx, dh_dy) arrays computed analytically for exact surface normals.
    """
    xs = np.arange(w, dtype=np.float64)
    ys = np.arange(h, dtype=np.float64)
    xx, yy = np.meshgrid(xs, ys)

    dh_dx = np.zeros((h, w), dtype=np.float64)
    dh_dy = np.zeros((h, w), dtype=np.float64)

    wavelengths = RNG.uniform(90, 260, size=n_waves)
    amplitudes  = RNG.uniform(3.5, 9.0, size=n_waves)
    angles      = RNG.uniform(0, 2 * np.pi, size=n_waves)
    phases      = RNG.uniform(0, 2 * np.pi, size=n_waves)

    for amp, wl, ang, phi in zip(amplitudes, wavelengths, angles, phases):
        kx = 2 * np.pi / wl * np.cos(ang)
        ky = 2 * np.pi / wl * np.sin(ang)
        # h = amp * sin(kx*x + ky*y + phi)
        # dh/dx = amp * kx * cos(...)
        arg = kx * xx + ky * yy + phi
        c = np.cos(arg)
        dh_dx += amp * kx * c
        dh_dy += amp * ky * c

    return dh_dx.astype(np.float32), dh_dy.astype(np.float32)


def cast_caustics(w, h, dh_dx, dh_dy, pool_depth):
    """
    Shoot one ray per surface pixel downward, refract via Snell's law,
    accumulate hits on the pool floor into a density grid.
    n_water / n_air = 1.333
    """
    xs = np.arange(w, dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    # Surface normal N = normalize(-dh_dx, -dh_dy, 1)
    Nx = -dh_dx
    Ny = -dh_dy
    Nz = np.ones((h, w), dtype=np.float32)
    mag = np.sqrt(Nx**2 + Ny**2 + Nz**2)
    Nx /= mag
    Ny /= mag
    Nz /= mag

    # Snell's law: I = (0, 0, 1) downward, n1/n2 = 1/1.333
    n_rel = 1.0 / 1.333
    cos_i = Nz                             # N · I = Nz  (I points same direction as N_z)
    sin2_i = 1.0 - cos_i ** 2
    sin2_t = (n_rel ** 2) * sin2_i
    sin2_t = np.minimum(sin2_t, 1.0 - 1e-7)
    cos_t = np.sqrt(1.0 - sin2_t)

    # Refracted ray direction
    factor = n_rel * cos_i - cos_t
    Tx = factor * Nx
    Ty = factor * Ny
    Tz = n_rel + factor * Nz              # n_rel * 1 + factor * Nz

    # Project to pool floor: floor = surface + depth * T / Tz
    safe_Tz = np.maximum(Tz, 0.01)
    floor_x = xx + pool_depth * Tx / safe_Tz
    floor_y = yy + pool_depth * Ty / safe_Tz

    # Accumulate photon density
    fx = np.clip(floor_x.astype(np.int32), 0, w - 1)
    fy = np.clip(floor_y.astype(np.int32), 0, h - 1)
    flat = fy.ravel() * w + fx.ravel()
    density = np.bincount(flat, minlength=w * h).reshape(h, w).astype(np.float32)

    return density


def add_tile_grid(w, h, tile_px=64):
    """Subtle square tile grid for the pool floor."""
    xs = np.arange(w)
    ys = np.arange(h)
    xx, yy = np.meshgrid(xs, ys)
    grid = ((xx % tile_px == 0) | (yy % tile_px == 0)).astype(np.float32) * 0.025
    return grid


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    w, h = SIZE
    pool_depth = h * 0.55   # how deep the pool floor sits (pixels)

    dh_dx, dh_dy = make_wave_surface(w, h)
    density = cast_caustics(w, h, dh_dx, dh_dy, pool_depth)

    # Smooth just enough to remove aliasing without losing sharpness
    density = gaussian_filter(density, sigma=1.2)

    # ---- Tone mapping ----
    # Mean photon density is always 1.0 (conservation).
    # Map density → [0,1] using a fixed scale so the floor is visible
    # and caustic peaks (10-50× mean) bloom to white-gold.
    #   c   : main illumination (density 0 → 4  maps to 0 → 1)
    #   hot : extra flare above density 4 (up to 1)
    tile = add_tile_grid(w, h)

    c   = (density / 4.5).clip(0.0, 1.0)
    hot = ((density - 4.5) / 25.0).clip(0.0, 1.0)

    # Deep navy pool floor base
    r = 0.012 + c * 0.88 + hot * 0.10 + tile
    g = 0.045 + c * 0.76 + hot * 0.08 + tile
    b = 0.105 + c * 0.44 - hot * 0.04 + tile

    # Gentle vignette — keep centre bright, dim edges only lightly
    ys_n = np.linspace(-1.0, 1.0, h)
    xs_n = np.linspace(-1.0, 1.0, w)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.30 * (xg**2 + yg**2)).clip(0.55, 1.0).astype(np.float32)

    r = (r * vignette).clip(0, 1)
    g = (g * vignette).clip(0, 1)
    b = (b * vignette).clip(0, 1)

    result = np.stack([r, g, b], axis=-1).clip(0, 1)
    result_u8 = (result * 255).astype(np.uint8)

    save_preview_pil(result_u8, SKETCH_DIR, filename="preview.png", mode="RGB")
    py5.exit_sketch()


py5.run_sketch()

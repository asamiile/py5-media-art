from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE
W, H = SIZE

MAX_ITER = 60
TOL = 1e-6

# Domain: 16:9 region of the complex plane, centered at origin
RE_MIN, RE_MAX = -1.6, 1.6
IM_MIN, IM_MAX = -0.9, 0.9

# Hues for the 5 roots of z^5 = 1 (72° apart, vibrant palette)
BASIN_HUES = np.array([0.0, 72.0, 144.0, 216.0, 288.0])

pixels_arr = None


def _newton_z5(z_init: np.ndarray):
    """Newton-Raphson for f(z) = z^5 − 1, f'(z) = 5z^4."""
    roots = np.exp(2j * np.pi * np.arange(5) / 5)  # (5,) 5th roots of unity

    z = z_init.copy()
    conv_root = np.full(z.shape, -1, dtype=np.int8)
    conv_iter = np.zeros(z.shape, dtype=np.float32)
    active = np.ones(z.shape, dtype=bool)

    for it in range(1, MAX_ITER + 1):
        if not active.any():
            break

        z4 = z ** 4
        step = (z * z4 - 1) / (5 * z4 + 1e-30)   # (z^5-1)/(5z^4)
        z[active] -= step[active]

        # Find nearest root for active pixels
        min_d = np.full(z.shape, np.inf)
        nearest = np.zeros(z.shape, dtype=np.int8)
        for ri, root in enumerate(roots):
            d = np.abs(z - root)
            better = d < min_d
            min_d[better] = d[better]
            nearest[better] = ri

        just_conv = active & (min_d < TOL)
        conv_root[just_conv] = nearest[just_conv]
        conv_iter[just_conv] = float(it)
        active[just_conv] = False

    # Smoothing: adjust iteration count by sub-pixel distance
    conv_iter += 1.0 - np.clip(np.log(min_d + 1e-10) / np.log(TOL), 0, 1)

    return conv_root, conv_iter


def _build_image(conv_root: np.ndarray, conv_iter: np.ndarray) -> np.ndarray:
    rows, cols = conv_root.shape

    # Brightness: fast convergence → bright, slow → dark
    brightness = 1.0 - (conv_iter / MAX_ITER) ** 0.45
    brightness = np.clip(brightness, 0.0, 1.0)

    # Unconverged pixels: nearly black
    converged = conv_root >= 0
    brightness = np.where(converged, brightness, 0.04)

    hues = np.where(converged, BASIN_HUES[np.clip(conv_root, 0, 4)], 0.0)
    sats = np.where(converged, 0.88, 0.0)
    vals = brightness

    h = hues / 60.0
    ii = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = vals * (1 - sats)
    q = vals * (1 - sats * f)
    t = vals * (1 - sats * (1 - f))
    cnd = [ii == k for k in range(6)]
    r = np.select(cnd, [vals, q, p, p, t, vals])
    g = np.select(cnd, [t, vals, vals, q, p, p])
    b = np.select(cnd, [p, p, t, vals, vals, q])

    alpha = np.full((rows, cols), 255, dtype=np.uint8)
    img = np.stack([alpha,
                    (r * 255).astype(np.uint8),
                    (g * 255).astype(np.uint8),
                    (b * 255).astype(np.uint8)], axis=-1)
    return img


def setup():
    global pixels_arr
    py5.size(*SIZE)

    re = np.linspace(RE_MIN, RE_MAX, W, dtype=np.float64)
    im = np.linspace(IM_MAX, IM_MIN, H, dtype=np.float64)   # top→bottom
    re_g, im_g = np.meshgrid(re, im)
    z0 = (re_g + 1j * im_g).astype(np.complex128)

    conv_root, conv_iter = _newton_z5(z0)
    pixels_arr = _build_image(conv_root, conv_iter)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == H and w == W:
        py5.np_pixels[:] = pixels_arr
    else:
        # Retina 2× buffer
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

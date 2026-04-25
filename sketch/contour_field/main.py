from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N_BANDS = 14      # number of contour bands — wide, legible
EXPONENT = 2.8   # high rolloff → smooth, large-scale terrain

pixels_arr = None


def spectral_terrain(width, height, exponent):
    """Generate fractal terrain via inverse FFT with 1/f^exponent power spectrum."""
    fy = np.fft.fftfreq(height)
    fx = np.fft.fftfreq(width)
    FX, FY = np.meshgrid(fx, fy)

    freq = np.sqrt(FX ** 2 + FY ** 2)
    freq[0, 0] = 1.0  # avoid DC divide-by-zero

    amplitude = freq ** (-exponent)
    amplitude[0, 0] = 0.0  # zero mean

    phase = np.random.uniform(0, 2 * np.pi, (height, width))
    spectrum = amplitude * np.exp(1j * phase)

    field = np.real(np.fft.ifft2(spectrum))
    field = (field - field.min()) / (field.max() - field.min())
    return field.astype(np.float32)


def field_to_rgb(field, n_bands):
    """Map field values to colorful topographic contour bands."""
    # Position within band (0→1) and band index
    scaled = field * n_bands
    band_idx = scaled.astype(np.int32) % n_bands
    band_pos = scaled - np.floor(scaled)   # 0→1 within each band

    # Hue: cycles slowly over all bands (one full spectrum per n_bands)
    hue = (band_idx.astype(np.float32) / n_bands * 360.0)

    # Sharp dark contour lines at band boundaries; bright, saturated interiors
    edge_dist = np.minimum(band_pos, 1.0 - band_pos)  # 0 at border, 0.5 at center
    brightness = np.clip(edge_dist * 12.0, 0, 1)      # sharp cutoff at border
    sat = brightness * 0.88 + 0.05
    val = brightness * 0.88 + 0.08

    # HSV → RGB (vectorized)
    h = hue / 60.0
    i6 = np.floor(h).astype(np.int32) % 6
    f = h - np.floor(h)
    p = val * (1 - sat)
    q = val * (1 - sat * f)
    t = val * (1 - sat * (1 - f))

    conds = [i6 == k for k in range(6)]
    r = np.select(conds, [val, q, p, p, t, val])
    g = np.select(conds, [t, val, val, q, p, p])
    b = np.select(conds, [p, p, t, val, val, q])

    alpha = np.full(field.shape, 255, dtype=np.uint8)
    return np.stack([
        alpha,
        np.clip(r * 255, 0, 255).astype(np.uint8),
        np.clip(g * 255, 0, 255).astype(np.uint8),
        np.clip(b * 255, 0, 255).astype(np.uint8),
    ], axis=-1)


def setup():
    global pixels_arr
    py5.size(*SIZE)
    field = spectral_terrain(SIZE[0], SIZE[1], EXPONENT)
    pixels_arr = field_to_rgb(field, N_BANDS)


def draw():
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels_arr
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels_arr, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

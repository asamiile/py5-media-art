from pathlib import Path
import numpy as np
from PIL import Image
import py5

SKETCH_DIR = Path(__file__).parent

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

RNG = np.random.default_rng()

N_FILM = 1.34   # soap-water refractive index


def fBm(w, h, octaves=6, base_freq=2.8, persistence=0.52):
    """Fractional Brownian motion via random sinusoid superposition."""
    xs = np.linspace(0.0, 1.0, w, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    result = np.zeros((h, w), dtype=np.float32)
    freq = base_freq
    amp  = 1.0
    total = 0.0

    for _ in range(octaves):
        for _ in range(3):   # 3 random waves per octave
            angle = RNG.uniform(0.0, 2 * np.pi)
            phase = RNG.uniform(0.0, 2 * np.pi)
            kx = freq * np.cos(angle)
            ky = freq * np.sin(angle)
            result += amp * np.sin(2 * np.pi * (kx * xx + ky * yy) + phase)
        total += amp * 3
        freq *= 2.0
        amp  *= persistence

    # Map to [0, 1]
    result = (result / total + 1.0) / 2.0
    return result.clip(0.0, 1.0)


def thin_film_rgb(w, h):
    """
    Compute RGB image via thin-film interference.

    For a soap film of refractive index n and thickness t (nm), the
    reflectance at wavelength λ (nm) — including the π phase shift on the
    first reflection (air→soap) — is:

        I(λ) = ½ · (1 − cos(4π·n·t / λ))

    Integrate I(λ) against approximate CIE R,G,B sensitivity curves to get RGB.
    """
    # Thickness field: fBm mapped to [0, 680] nm
    # Range covers ~2.5 interference orders — enough for vivid first-order
    # colours while keeping thin-film black regions where noise ≈ 0.
    noise = fBm(w, h)

    # Gentle top→bottom gravity drain: film thinner at top, thicker below
    y_bias = np.linspace(0.0, 0.18, h, dtype=np.float32)[:, np.newaxis]
    thickness = (noise * 0.82 + y_bias * 0.18) * 680.0   # nm, (H,W)

    # Wavelength samples: 380–780 nm, step 20 nm → 21 values
    lambdas = np.arange(380, 781, 20, dtype=np.float32)  # shape (21,)

    # Approximate CIE colour-matching functions (3-Gaussian model)
    r_sens = (np.exp(-0.5 * ((lambdas - 615) / 65) ** 2)
              + 0.18 * np.exp(-0.5 * ((lambdas - 445) / 18) ** 2))
    g_sens = np.exp(-0.5 * ((lambdas - 545) / 55) ** 2)
    b_sens = np.exp(-0.5 * ((lambdas - 455) / 42) ** 2)

    r_w = (r_sens / r_sens.sum()).astype(np.float32)
    g_w = (g_sens / g_sens.sum()).astype(np.float32)
    b_w = (b_sens / b_sens.sum()).astype(np.float32)

    # Vectorised interference over all wavelengths in one shot
    # t: (H, W, 1),  lam: (1, 1, 21)
    t3   = thickness[:, :, np.newaxis]
    lam3 = lambdas[np.newaxis, np.newaxis, :]

    I = 0.5 * (1.0 - np.cos(4.0 * np.pi * N_FILM * t3 / lam3))  # (H,W,21)

    R = (I * r_w).sum(axis=2)   # (H, W)
    G = (I * g_w).sum(axis=2)
    B = (I * b_w).sum(axis=2)

    rgb = np.stack([R, G, B], axis=-1)  # (H, W, 3)
    return rgb.astype(np.float32)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    w, h = SIZE

    rgb = thin_film_rgb(w, h)

    # Colour treatment — preserve luminance structure, boost chroma only.
    # Raw interference has mean ≈ 0.5 per channel; thin-film regions (t→0)
    # naturally produce RGB≈0 (physical black film) which must stay dark.
    gray = rgb.mean(axis=2, keepdims=True)     # achromatic component
    chroma = rgb - gray                         # chromatic deviation

    # 1. Boost saturation relative to local grey (does not add a bright floor)
    rgb_sat = rgb + 2.0 * chroma               # = gray + 3.0*(rgb-gray)

    # 2. Power-law compression: darkens mid-tones (0.5→0.38), keeps whites
    rgb_gamma = np.power(rgb_sat.clip(0.0, 1.0), 1.35)

    # 3. Oval dark vignette — evokes the edge of a soap bubble
    ys_n = np.linspace(-1.0, 1.0, h, dtype=np.float32)
    xs_n = np.linspace(-1.0, 1.0, w, dtype=np.float32)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = np.exp(-(xg ** 2 * 0.38 + yg ** 2 * 0.60))
    vignette = (vignette * 0.55 + 0.45).clip(0.0, 1.0).astype(np.float32)

    rgb_final = (rgb_gamma * vignette[:, :, np.newaxis]).clip(0.0, 1.0)

    result_u8 = (rgb_final * 255.0).astype(np.uint8)
    Image.fromarray(result_u8, "RGB").save(str(SKETCH_DIR / "preview.png"))
    py5.exit_sketch()


py5.run_sketch()

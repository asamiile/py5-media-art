from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.animation import frames_dir, render_video_and_preview, save_animation_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = frames_dir(SKETCH_DIR)
DURATION_SEC = 8
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS   # 240

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

N_BANDS  = 12
EXPONENT = 2.6
T_SPEED  = 0.008   # how fast the terrain morphs per frame

# Geological palette — 5 tones, cool to warm
# valley(dark navy) → slate → sage → sandstone → peak(bone)
PALETTE = np.array([
    [14,  21,  32],   # #0e1520 deep navy valley
    [42,  64,  85],   # #2a4055 dark slate
    [92, 122, 106],   # #5c7a6a muted sage
    [160, 140, 110],  # #a08c6e warm sandstone
    [232, 220, 200],  # #e8dcc8 pale bone peak
], dtype=np.float32)

# Pre-build a smooth 256-entry LUT from the 5-color palette
def _build_lut():
    lut = np.zeros((256, 3), dtype=np.float32)
    n = len(PALETTE)
    for i in range(256):
        t = i / 255.0 * (n - 1)
        lo = int(t)
        hi = min(lo + 1, n - 1)
        f = t - lo
        lut[i] = PALETTE[lo] * (1 - f) + PALETTE[hi] * f
    return lut

LUT = _build_lut()

# Base 3D noise volume: shape (DEPTH, H, W)
# We'll use a 2D FFT field and scroll through a third axis via phase rotation
DEPTH = TOTAL_FRAMES + 1
noise_volume = None


def _spectral_field(w, h, exp, phase_offset=0.0):
    """Single 2D FFT terrain slice with a phase-shifted spectrum."""
    fy = np.fft.fftfreq(h)
    fx = np.fft.fftfreq(w)
    FX, FY = np.meshgrid(fx, fy)
    freq = np.sqrt(FX**2 + FY**2)
    freq[0, 0] = 1.0
    amp = freq ** (-exp)
    amp[0, 0] = 0.0
    return amp, freq


def _build_volume(w, h):
    """Precompute amplitude spectrum and random phases for morphing."""
    fy = np.fft.fftfreq(h)
    fx = np.fft.fftfreq(w)
    FX, FY = np.meshgrid(fx, fy)
    freq = np.sqrt(FX**2 + FY**2)
    freq[0, 0] = 1.0
    amp = freq ** (-EXPONENT)
    amp[0, 0] = 0.0

    # Two independent random phase fields; we interpolate between them over time
    phase_a = np.random.uniform(0, 2*np.pi, (h, w))
    phase_b = np.random.uniform(0, 2*np.pi, (h, w))
    return amp, phase_a, phase_b


amp_spec = None
phase_a  = None
phase_b  = None


def _frame_field(t_norm):
    """t_norm: 0→1 over animation. Returns normalised 2D field."""
    # Smoothly interpolate phase between phase_a and phase_b using cosine ease
    ease = (1 - np.cos(t_norm * np.pi)) / 2
    phase = phase_a * (1 - ease) + phase_b * ease
    spectrum = amp_spec * np.exp(1j * phase)
    field = np.real(np.fft.ifft2(spectrum))
    mn, mx = field.min(), field.max()
    return ((field - mn) / (mx - mn)).astype(np.float32)


def _field_to_pixels(field):
    """Map field to ARGB pixel array using geological LUT + sharp band edges."""
    scaled = field * N_BANDS
    band_pos = scaled - np.floor(scaled)      # 0→1 within each band
    edge_dist = np.minimum(band_pos, 1 - band_pos)
    brightness = np.clip(edge_dist * 14.0, 0, 1)   # sharp dark borders

    # LUT lookup — quantize field to 0-255
    lut_idx = np.clip((field * 255).astype(int), 0, 255)
    rgb = LUT[lut_idx]   # (H, W, 3)

    # Apply brightness (border = dark, interior = full color)
    br = brightness[:, :, np.newaxis]
    rgb_out = (rgb * br).astype(np.uint8)

    alpha = np.full(field.shape, 255, dtype=np.uint8)
    return np.stack([alpha, rgb_out[:,:,0], rgb_out[:,:,1], rgb_out[:,:,2]], axis=-1)


def setup():
    global amp_spec, phase_a, phase_b
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    amp_spec, phase_a, phase_b = _build_volume(SIZE[0], SIZE[1])


def draw():
    t_norm = (py5.frame_count - 1) / max(TOTAL_FRAMES - 1, 1)
    field = _frame_field(t_norm)
    pixels = _field_to_pixels(field)

    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = pixels
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(pixels, 2, axis=0), 2, axis=1)
    py5.update_np_pixels()

    save_animation_frame(FRAMES_DIR)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        render_video_and_preview(
            SKETCH_DIR,
            FRAMES_DIR,
            fps=FPS,
            total_frames=TOTAL_FRAMES,
            preview_frame=TOTAL_FRAMES // 2,
        )


py5.run_sketch()

from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation grid; render upscale ratio is computed at runtime from np_pixels.
GRID_W, GRID_H = 480, 270
WAVE_SPEED_SQ = 0.22  # CFL stable below 0.5 for our scheme
DAMPING = 0.992

# Palette (linear 0..1 scaled to 0..255 at write time)
BG_INDIGO = np.array([4.0, 6.0, 18.0])
CYAN_CREST = np.array([110.0, 170.0, 210.0])
PEARL_PEAK = np.array([220.0, 230.0, 240.0])
AMBER_LAMP = np.array([220.0, 165.0, 90.0])
MOONGLOW = np.array([6.0, 10.0, 22.0])

# Drop scheduling
rng = np.random.default_rng()

# Wave fields
u = np.zeros((GRID_H, GRID_W), dtype=np.float32)
u_prev = np.zeros_like(u)

# Soft mask near borders (absorbs energy to prevent boxy reflections)
def make_border_mask():
    yy, xx = np.indices((GRID_H, GRID_W))
    margin = 18
    m = np.minimum(np.minimum(xx, GRID_W - 1 - xx),
                   np.minimum(yy, GRID_H - 1 - yy))
    fade = np.clip(m / margin, 0.0, 1.0)
    return (0.95 + 0.05 * fade).astype(np.float32)

BORDER = make_border_mask()

# Cached "moonglow" diffuse field (radial soft light)
def make_moonglow():
    yy, xx = np.indices((GRID_H, GRID_W)).astype(np.float32)
    cx, cy = GRID_W * 0.68, GRID_H * 0.22
    r2 = (xx - cx) ** 2 * 1.2 + (yy - cy) ** 2 * 1.0
    g = np.exp(-r2 / (2 * (GRID_W * 0.30) ** 2))
    g = np.clip(g, 0.0, 1.0)
    return g.astype(np.float32)

MOON = make_moonglow()

# Lamplight in distance — small warm patch
def make_lamp_field():
    yy, xx = np.indices((GRID_H, GRID_W)).astype(np.float32)
    cx, cy = GRID_W * 0.18, GRID_H * 0.78
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    g = np.exp(-r2 / (2 * (GRID_W * 0.10) ** 2))
    return (g * 0.5).astype(np.float32)

LAMP = make_lamp_field()

# Pre-allocated render buffers
render_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)


def add_drop(cx: float, cy: float, strength: float, sigma: float) -> None:
    """Inject a Mexican-hat (Laplacian-of-Gaussian) impulse at (cx, cy).

    A bare Gaussian generates a single ring; the DoG profile (positive core
    surrounded by a negative annulus) seeds multiple visible concentric bands
    as the wave equation propagates it outward — closer to a real raindrop.
    """
    pad = max(4, int(sigma * 4.5))
    x0, x1 = max(0, int(cx - pad)), min(GRID_W, int(cx + pad + 1))
    y0, y1 = max(0, int(cy - pad)), min(GRID_H, int(cy + pad + 1))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    s2 = sigma * sigma
    # Mexican hat profile, normalized so peak ≈ strength
    profile = (1.0 - r2 / (2.0 * s2)) * np.exp(-r2 / (2.0 * s2))
    u[y0:y1, x0:x1] += (strength * profile).astype(np.float32)


def schedule_drops(frame: int) -> None:
    """Stochastic raindrop schedule with rising intensity."""
    t = frame / TOTAL_FRAMES  # 0..1
    # Density curve: very sparse start, builds slowly, peaks late, eases off
    density = np.sin(np.clip(t * np.pi, 0.0, np.pi)) ** 1.4
    # Expected drops per frame
    lam = 0.04 + 0.55 * density
    n = rng.poisson(lam)
    for _ in range(int(n)):
        cx = rng.uniform(10, GRID_W - 10)
        cy = rng.uniform(10, GRID_H - 10)
        sigma = rng.uniform(1.6, 2.8)
        strength = rng.uniform(0.6, 1.3) * (0.55 + 0.65 * density)
        add_drop(cx, cy, strength, sigma)


def step_wave() -> None:
    """One FDTD step of the 2D wave equation."""
    global u, u_prev
    # 5-point Laplacian without boundary reflections (use zero padding)
    lap = np.zeros_like(u)
    lap[1:-1, 1:-1] = (
        u[:-2, 1:-1] + u[2:, 1:-1]
        + u[1:-1, :-2] + u[1:-1, 2:]
        - 4.0 * u[1:-1, 1:-1]
    )
    u_next = (2.0 * u - u_prev + WAVE_SPEED_SQ * lap) * DAMPING
    # Soft border absorber — fade values in margin zone
    u_next *= BORDER
    u_prev, u = u, u_next


def render_to_rgb() -> np.ndarray:
    """Compute RGB color at simulation resolution from current u.

    Renders signed surface height: peaks reflect cyan moonlight, troughs sink
    to deeper shadow, leaving alternating bright/dark concentric bands as the
    only ripple signature. The base water surface stays nearly black so the
    ripples read as light on darkness, not as light-on-light.
    """
    # Signed deflection — positive = crest, negative = trough
    pos = np.clip(u, 0.0, None)
    neg = np.clip(-u, 0.0, None)

    # Compress dynamic range so faint ripples register without saturating
    crest = np.tanh(pos * 4.0)
    trough = np.tanh(neg * 4.0)

    # Sharp specular: only the very highest peaks reflect bright pearl
    sharp = np.clip(pos * 6.0 - 0.55, 0.0, None) ** 1.6
    sharp = np.clip(sharp, 0.0, 1.6)

    # Slope gives a faint rim shimmer on steep wave fronts (subtle)
    gy, gx = np.gradient(u)
    slope = np.sqrt(gx * gx + gy * gy)
    rim = np.clip(np.tanh(slope * 5.0) - 0.55, 0.0, None) ** 1.4

    # Base: dark indigo + a soft cool moonlight on one side
    base = BG_INDIGO[None, None, :] + MOON[..., None] * MOONGLOW[None, None, :]
    base = base + LAMP[..., None] * AMBER_LAMP[None, None, :] * 0.18

    # Crest tint adds cyan toward CYAN_CREST color
    crest_layer = crest[..., None] * (CYAN_CREST - BG_INDIGO)[None, None, :] * 0.55
    # Pearl peak highlight
    pearl_layer = sharp[..., None] * (PEARL_PEAK - BG_INDIGO)[None, None, :] * 0.45
    # Trough darkens toward near-black
    shadow_layer = -trough[..., None] * BG_INDIGO[None, None, :] * 0.55
    # Subtle rim glint
    rim_layer = rim[..., None] * (PEARL_PEAK - CYAN_CREST)[None, None, :] * 0.40

    rgb = base + crest_layer + pearl_layer + shadow_layer + rim_layer

    np.clip(rgb, 0.0, 255.0, out=rgb)
    return rgb


def upscale_to_buffer(rgb_small: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    """Nearest-neighbor upscale a (H,W,3) float array to (out_h, out_w, 3) uint8."""
    sy = out_h // GRID_H
    sx = out_w // GRID_W
    # If buffer not exact multiple, fall back to repeat then crop
    if sy * GRID_H != out_h or sx * GRID_W != out_w:
        sy = max(1, sy)
        sx = max(1, sx)
    big = np.repeat(np.repeat(rgb_small, sy, axis=0), sx, axis=1)
    if big.shape[0] < out_h or big.shape[1] < out_w:
        # Pad if rare mismatch (shouldn't happen with our integer ratios)
        pad_h = max(0, out_h - big.shape[0])
        pad_w = max(0, out_w - big.shape[1])
        big = np.pad(big, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
    return big[:out_h, :out_w].astype(np.uint8)


def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    # Pre-warm one drop so the surface isn't perfectly flat at frame 1
    add_drop(GRID_W * 0.5, GRID_H * 0.5, 0.4, 1.8)


def draw():
    schedule_drops(py5.frame_count)
    # Multiple physics sub-steps per frame for smoother propagation
    for _ in range(2):
        step_wave()

    rgb_small = render_to_rgb()

    py5.load_np_pixels()
    ph, pw = py5.np_pixels.shape[:2]
    big = upscale_to_buffer(rgb_small, ph, pw)
    # py5 np_pixels is ARGB-ordered (alpha first)
    py5.np_pixels[..., 0] = 255
    py5.np_pixels[..., 1] = big[..., 0]  # R
    py5.np_pixels[..., 2] = big[..., 1]  # G
    py5.np_pixels[..., 3] = big[..., 2]  # B
    py5.update_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "17",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Pick a frame with strong interference for the still preview
        mid = str(FRAMES_DIR / f"frame-{int(TOTAL_FRAMES * 0.62):04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)


py5.run_sketch()

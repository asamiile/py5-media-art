from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 500

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

N_PARTICLES = 80000
SPEED = 2.5
JITTER = 0.8  # random perturbation to break closed orbits

particles = None
trail = None


def flow_angle(x, y, t):
    ax = x / SIZE[0] * np.pi * 2
    ay = y / SIZE[1] * np.pi * 2
    angle = (
        np.sin(ax * 1.5 + t * 0.30) * 1.2
        + np.cos(ay * 2.0 + t * 0.20) * 1.0
        + np.sin(ax * 3.5 - ay * 2.5 + t * 0.18) * 0.7
        + np.cos(ax * 0.8 + ay * 3.2 + t * 0.12) * 0.6
        + np.sin(ax * 5.0 + ay * 1.0 - t * 0.25) * 0.3
    ) * np.pi
    return angle


def setup():
    global particles, trail
    py5.size(*SIZE)
    particles = np.random.rand(N_PARTICLES, 2) * np.array([SIZE[0], SIZE[1]])
    trail = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.float64)


def draw():
    global particles, trail

    t = py5.frame_count * 0.010

    angle = flow_angle(particles[:, 0], particles[:, 1], t)
    vx = np.cos(angle) * SPEED + np.random.randn(N_PARTICLES) * JITTER
    vy = np.sin(angle) * SPEED + np.random.randn(N_PARTICLES) * JITTER

    particles[:, 0] = (particles[:, 0] + vx) % SIZE[0]
    particles[:, 1] = (particles[:, 1] + vy) % SIZE[1]

    # Color by flow direction — full HSV hue spectrum
    hue = (angle / (2 * np.pi)) % 1.0
    r_col = np.clip(np.abs(hue * 6 - 3) - 1, 0, 1)
    g_col = np.clip(2 - np.abs(hue * 6 - 2), 0, 1)
    b_col = np.clip(2 - np.abs(hue * 6 - 4), 0, 1)

    trail *= 0.988

    xi = particles[:, 0].astype(np.int32) % SIZE[0]
    yi = particles[:, 1].astype(np.int32) % SIZE[1]
    flat = yi * SIZE[0] + xi
    total = SIZE[0] * SIZE[1]

    trail[:, :, 0] += np.bincount(flat, weights=r_col, minlength=total).reshape(SIZE[1], SIZE[0])
    trail[:, :, 1] += np.bincount(flat, weights=g_col, minlength=total).reshape(SIZE[1], SIZE[0])
    trail[:, :, 2] += np.bincount(flat, weights=b_col, minlength=total).reshape(SIZE[1], SIZE[0])

    # log1p tone mapping with high scale — dim areas become luminous
    scale = 12.0
    log_trail = np.log1p(trail * scale)
    max_v = log_trail.max()
    if max_v > 0:
        display = np.clip(log_trail / max_v * 255, 0, 255).astype(np.uint8)
    else:
        display = trail.astype(np.uint8)

    alpha = np.full((SIZE[1], SIZE[0], 1), 255, dtype=np.uint8)
    argb = np.concatenate([alpha, display], axis=-1)

    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]

    if h == SIZE[1] and w == SIZE[0]:
        py5.np_pixels[:] = argb
    else:
        py5.np_pixels[:] = np.repeat(np.repeat(argb, 2, axis=0), 2, axis=1)

    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

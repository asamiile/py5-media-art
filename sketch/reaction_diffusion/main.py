from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Gray-Scott parameters — dense labyrinthine pattern
F, K   = 0.035, 0.060
DU, DV = 0.20,  0.10
STEPS  = 2000
DT     = 1.0


def laplacian(Z):
    return (
        np.roll(Z,  1, axis=0) + np.roll(Z, -1, axis=0) +
        np.roll(Z,  1, axis=1) + np.roll(Z, -1, axis=1) - 4 * Z
    )


def setup():
    py5.size(*SIZE)
    h, w = PREVIEW_SIZE[1], PREVIEW_SIZE[0]

    U = np.ones((h, w), dtype=np.float32)
    V = np.zeros((h, w), dtype=np.float32)

    rng = np.random.default_rng()
    for _ in range(80):
        x = rng.integers(10, w - 10)
        y = rng.integers(10, h - 10)
        r = rng.integers(8, 18)
        U[y - r:y + r, x - r:x + r] = 0.50
        V[y - r:y + r, x - r:x + r] = 0.25

    U += rng.uniform(-0.01, 0.01, (h, w)).astype(np.float32)
    V += rng.uniform(-0.005, 0.005, (h, w)).astype(np.float32)
    np.clip(U, 0, 1, out=U)
    np.clip(V, 0, 1, out=V)

    for _ in range(STEPS):
        uvv = U * V * V
        U += DT * (DU * laplacian(U) - uvv + F * (1 - U))
        V += DT * (DV * laplacian(V) + uvv - (F + K) * V)
        np.clip(U, 0, 1, out=U)
        np.clip(V, 0, 1, out=V)

    d = (V - V.min()) / (V.max() - V.min() + 1e-8)

    # Biological palette: dark teal → bright coral/orange at peaks
    r_ch = (d * 255).clip(0, 255).astype(np.uint8)
    g_ch = (d ** 0.6 * 160 + (1 - d) * 40).clip(0, 255).astype(np.uint8)
    b_ch = ((1 - d) ** 0.8 * 180 + d * 30).clip(0, 255).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != h or w_buf != w:
        sy = h_buf // h
        sx = w_buf // w
        r_ch = np.repeat(np.repeat(r_ch, sy, axis=0), sx, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, sy, axis=0), sx, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, sy, axis=0), sx, axis=1)

    alpha = np.full((h_buf, w_buf), 255, dtype=np.uint8)
    py5.np_pixels[:, :, 0] = alpha
    py5.np_pixels[:, :, 1] = r_ch
    py5.np_pixels[:, :, 2] = g_ch
    py5.np_pixels[:, :, 3] = b_ch
    py5.update_np_pixels()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

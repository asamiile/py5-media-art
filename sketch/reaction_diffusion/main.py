from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Isolated organisms" — spots regime, cold sage palette
# Spots regime: lower F, higher k → isolated spots instead of connected labyrinths
F, K   = 0.035, 0.064
DU, DV = 0.20,  0.10
STEPS  = 1000   # fewer steps — catch isolated-spot stage before merging
DT     = 1.0

# Palette (normalized 0–1)
BG_COL       = np.array([8,  12,  16], dtype=np.float32) / 255.0   # #080c10 near-black
TRANS_COL    = np.array([26, 48,  48], dtype=np.float32) / 255.0   # #1a3030 dark teal
STRUCT_COL   = np.array([200, 216, 184], dtype=np.float32) / 255.0 # #c8d8b8 pale sage
CORE_COL     = np.array([240, 244, 232], dtype=np.float32) / 255.0 # #f0f4e8 near-white


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
    # Scattered circular seeds — controls where spots form (not random noise)
    for _ in range(60):
        x = rng.integers(15, w - 15)
        y = rng.integers(15, h - 15)
        r = rng.integers(6, 14)
        U[y - r:y + r, x - r:x + r] = 0.50
        V[y - r:y + r, x - r:x + r] = 0.25

    # Very slight perturbation to break symmetry
    U += rng.uniform(-0.005, 0.005, (h, w)).astype(np.float32)
    V += rng.uniform(-0.002, 0.002, (h, w)).astype(np.float32)
    np.clip(U, 0, 1, out=U)
    np.clip(V, 0, 1, out=V)

    for _ in range(STEPS):
        uvv = U * V * V
        U += DT * (DU * laplacian(U) - uvv + F * (1 - U))
        V += DT * (DV * laplacian(V) + uvv - (F + K) * V)
        np.clip(U, 0, 1, out=U)
        np.clip(V, 0, 1, out=V)

    d = (V - V.min()) / (V.max() - V.min() + 1e-8)

    # 4-zone cold sage palette: BG → dark teal → pale sage → near-white core
    d0 = np.clip(d * 3.0, 0.0, 1.0)        # first zone: BG → teal
    d1 = np.clip(d * 3.0 - 1.0, 0.0, 1.0)  # second zone: teal → sage
    d2 = np.clip(d * 3.0 - 2.0, 0.0, 1.0)  # third zone: sage → core-white

    r_f = BG_COL[0] * (1 - d0) + TRANS_COL[0] * d0 * (1 - d1) + STRUCT_COL[0] * d1 * (1 - d2) + CORE_COL[0] * d2
    g_f = BG_COL[1] * (1 - d0) + TRANS_COL[1] * d0 * (1 - d1) + STRUCT_COL[1] * d1 * (1 - d2) + CORE_COL[1] * d2
    b_f = BG_COL[2] * (1 - d0) + TRANS_COL[2] * d0 * (1 - d1) + STRUCT_COL[2] * d1 * (1 - d2) + CORE_COL[2] * d2

    r_ch = np.clip(r_f * 255, 0, 255).astype(np.uint8)
    g_ch = np.clip(g_f * 255, 0, 255).astype(np.uint8)
    b_ch = np.clip(b_f * 255, 0, 255).astype(np.uint8)

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

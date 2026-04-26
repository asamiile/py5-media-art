from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Stained glass mandala" — a 12-fold kaleidoscope; a small wedge (15°) of
# a multi-frequency sine pattern is reflected and rotated to fill a circle,
# producing a jewel-toned stained-glass window from pure mathematical symmetry.

N_FOLD  = 12          # 12-fold rotational + reflective symmetry
SECTOR  = np.pi / N_FOLD   # half-sector = 15°
R_MAX   = min(SIZE) * 0.47  # circle radius in pixels

BG_COL = np.array([ 6,  5, 10], dtype=np.uint8)   # near-black outer ring

# Jewel-tone cyclic palette (4 colors, smoothly interpolated)
PALETTE = np.array([
    [205, 155,  28],   # warm gold
    [ 28, 152, 158],   # cool teal
    [158,  28,  38],   # crimson
    [108,  28, 168],   # deep violet
], dtype=np.float32)


def setup():
    py5.size(*SIZE)
    W, H = SIZE
    CX, CY = W / 2.0, H / 2.0

    x = np.arange(W, dtype=np.float32) - CX
    y = np.arange(H, dtype=np.float32) - CY
    gx, gy = np.meshgrid(x, y)    # (H, W) — signed distance from center

    r     = np.sqrt(gx ** 2 + gy ** 2)
    theta = np.arctan2(gy, gx)    # [-π, π]

    # Map every angle into canonical sector [0, SECTOR] via fold symmetry
    theta_pos  = np.mod(theta, 2 * SECTOR)        # wrap to [0, 2*SECTOR]
    theta_can  = np.where(theta_pos > SECTOR,      # reflect upper half
                          2 * SECTOR - theta_pos,
                          theta_pos)

    # Canonical Cartesian coordinates in the wedge
    u = r * np.cos(theta_can) / R_MAX   # [0, 1] along radius
    v = r * np.sin(theta_can) / R_MAX   # [0, ~0.26] across wedge

    # Multi-frequency pattern in the canonical wedge
    p1 = np.sin(u * 12 * np.pi + v * 6 * np.pi)
    p2 = np.cos(u *  9 * np.pi - v * 8 * np.pi)
    p3 = np.sin(u *  5 * np.pi + v * 15 * np.pi)
    combined = (p1 * p2 + p3 * 0.6) / 1.6          # range ~ [-1, 1]
    t = (combined + 1.0) * 0.5                       # [0, 1]

    # Map t to cyclic jewel palette
    t4    = (t * 4.0) % 4.0                         # [0, 4)
    idx0  = t4.astype(np.int32) % 4
    idx1  = (idx0 + 1) % 4
    frac  = (t4 - idx0).astype(np.float32)

    r_ch = (PALETTE[idx0, 0] * (1 - frac) + PALETTE[idx1, 0] * frac)
    g_ch = (PALETTE[idx0, 1] * (1 - frac) + PALETTE[idx1, 1] * frac)
    b_ch = (PALETTE[idx0, 2] * (1 - frac) + PALETTE[idx1, 2] * frac)

    # Mask: outside circle → background
    outside = r > R_MAX
    r_ch[outside] = BG_COL[0]
    g_ch[outside] = BG_COL[1]
    b_ch[outside] = BG_COL[2]

    r_ch = np.clip(r_ch, 0, 255).astype(np.uint8)
    g_ch = np.clip(g_ch, 0, 255).astype(np.uint8)
    b_ch = np.clip(b_ch, 0, 255).astype(np.uint8)

    py5.load_np_pixels()
    h_buf, w_buf = py5.np_pixels.shape[:2]

    if h_buf != H or w_buf != W:
        r_ch = np.repeat(np.repeat(r_ch, 2, axis=0), 2, axis=1)
        g_ch = np.repeat(np.repeat(g_ch, 2, axis=0), 2, axis=1)
        b_ch = np.repeat(np.repeat(b_ch, 2, axis=0), 2, axis=1)

    py5.np_pixels[:, :, 0] = 255
    py5.np_pixels[:, :, 1] = r_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 2] = g_ch[:h_buf, :w_buf]
    py5.np_pixels[:, :, 3] = b_ch[:h_buf, :w_buf]
    py5.update_np_pixels()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

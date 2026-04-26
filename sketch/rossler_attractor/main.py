from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Spiral descent" — the Rössler attractor; a 3D chaotic system whose orbits
# trace a continuous funnel-spiral in (x,y) before snapping back to a tight inner
# loop — rendered with z-height as the color dimension, unlike Lorenz (density-colored).

# Rössler parameters (classic: a=0.2, b=0.2, c=5.7)
A, B, C = 0.2, 0.2, 5.7
DT     = 0.012
N_TRAJ = 250
N_STEP = 35_000
BURN   = 500      # discard first steps per trajectory

# Spatial bounds of the (x, y) projection
X_MIN, X_MAX = -14.0,  16.0
Y_MIN, Y_MAX = -13.0,  12.0
Z_MIN, Z_MAX =   0.0,  25.0    # z colour range

BG_COL = np.array([ 5,  4, 10], dtype=np.uint8)

# Palette: z low → deep violet, z high → electric gold
COL_LOW  = np.array([ 28,  18, 100], dtype=np.float32)  # deep violet
COL_MID  = np.array([  8, 120, 160], dtype=np.float32)  # electric teal
COL_HIGH = np.array([220, 180,  28], dtype=np.float32)  # warm gold


def rossler_step(pos, a, b, c, dt):
    """Vectorised RK4 step for N trajectories. pos shape: (N, 3)."""
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        return np.stack([-y - z,
                          x + a * y,
                          b + z * (x - c)], axis=1)
    k1 = f(pos)
    k2 = f(pos + 0.5 * dt * k1)
    k3 = f(pos + 0.5 * dt * k2)
    k4 = f(pos + dt * k3)
    return pos + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def setup():
    py5.size(*SIZE)
    W, H = SIZE

    rng = np.random.default_rng()

    # Initial conditions: small spread around (1, 0, 0)
    pos = rng.normal([1.0, 0.0, 0.0], 0.3, (N_TRAJ, 3)).astype(np.float64)

    # Burn-in to reach attractor
    for _ in range(BURN):
        pos = rossler_step(pos, A, B, C, DT)

    # Accumulate density separately per z-layer
    # Strategy: accumulate 3 density arrays (low/mid/high z) then composite
    density_low  = np.zeros((H, W), dtype=np.float32)
    density_mid  = np.zeros((H, W), dtype=np.float32)
    density_high = np.zeros((H, W), dtype=np.float32)

    x_range = X_MAX - X_MIN
    y_range = Y_MAX - Y_MIN
    z_range = Z_MAX - Z_MIN

    for _ in range(N_STEP):
        pos = rossler_step(pos, A, B, C, DT)
        x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]

        px = np.clip(((x - X_MIN) / x_range * W).astype(np.int32), 0, W - 1)
        py_coord = np.clip(((Y_MAX - y) / y_range * H).astype(np.int32), 0, H - 1)
        tz = np.clip((z - Z_MIN) / z_range, 0.0, 1.0).astype(np.float32)

        np.add.at(density_low,  (py_coord, px), (1.0 - np.minimum(tz * 2, 1.0)))
        np.add.at(density_mid,  (py_coord, px), np.maximum(0.0, 1.0 - np.abs(tz * 2 - 1.0)))
        np.add.at(density_high, (py_coord, px), np.maximum(0.0, tz * 2 - 1.0))

    # Log-scale and normalize each layer
    def logscale(d):
        d = np.log1p(d * 30.0)
        mx = d.max()
        return d / (mx + 1e-8) if mx > 0 else d

    dl = logscale(density_low)
    dm = logscale(density_mid)
    dh = logscale(density_high)

    # Composite: additive blend of 3 color layers
    r_ch = np.clip(COL_LOW[0]*dl + COL_MID[0]*dm + COL_HIGH[0]*dh, 0, 255)
    g_ch = np.clip(COL_LOW[1]*dl + COL_MID[1]*dm + COL_HIGH[1]*dh, 0, 255)
    b_ch = np.clip(COL_LOW[2]*dl + COL_MID[2]*dm + COL_HIGH[2]*dh, 0, 255)

    r_ch = r_ch.astype(np.uint8)
    g_ch = g_ch.astype(np.uint8)
    b_ch = b_ch.astype(np.uint8)

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

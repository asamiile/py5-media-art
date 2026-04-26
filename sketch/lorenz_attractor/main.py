from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Convective turbulence" — Lorenz attractor, the butterfly of chaos
# Classic parameters: σ=10, ρ=28, β=8/3 (Lorenz 1963 meteorology paper)
SIGMA = 10.0
RHO   = 28.0
BETA  = 8.0 / 3.0

N_TRAJECTORIES = 800      # parallel trajectories for density
N_STEPS        = 25000    # integration steps per trajectory
DT             = 0.004    # time step (RK4)
BURN_IN        = 2000     # discard initial transient

# Palette: deep rust → amber → pale gold at peak density
RUST_COL  = np.array([90,   30,   8], dtype=np.float32)   # #5a1e08
AMBER_COL = np.array([200, 120,  20], dtype=np.float32)   # #c87814
GOLD_COL  = np.array([255, 220, 140], dtype=np.float32)   # #ffdC8c

pixels_arr = None


def lorenz_rk4(x, y, z, dt):
    """Single RK4 step for Lorenz system (vectorized over N trajectories)."""
    def f(x_, y_, z_):
        dx = SIGMA * (y_ - x_)
        dy = x_ * (RHO - z_) - y_
        dz = x_ * y_ - BETA * z_
        return dx, dy, dz

    k1x, k1y, k1z = f(x, y, z)
    k2x, k2y, k2z = f(x + dt/2*k1x, y + dt/2*k1y, z + dt/2*k1z)
    k3x, k3y, k3z = f(x + dt/2*k2x, y + dt/2*k2y, z + dt/2*k2z)
    k4x, k4y, k4z = f(x + dt*k3x,   y + dt*k3y,   z + dt*k3z)

    x_new = x + dt/6 * (k1x + 2*k2x + 2*k3x + k4x)
    y_new = y + dt/6 * (k1y + 2*k2y + 2*k3y + k4y)
    z_new = z + dt/6 * (k1z + 2*k2z + 2*k3z + k4z)
    return x_new, y_new, z_new


def setup():
    global pixels_arr
    py5.size(*SIZE)

    rng = np.random.default_rng()

    # Start near the classic fixed point region with small perturbations
    x = rng.normal(0.1, 0.5, N_TRAJECTORIES).astype(np.float32)
    y = rng.normal(0.1, 0.5, N_TRAJECTORIES).astype(np.float32)
    z = rng.normal(25.0, 0.5, N_TRAJECTORIES).astype(np.float32)

    # Burn-in
    for _ in range(BURN_IN):
        x, y, z = lorenz_rk4(x, y, z, DT)

    # Collect projected 2D positions for density map
    # Project onto (x, z) plane — shows the classic butterfly shape
    all_px = []
    all_pz = []

    for step in range(N_STEPS):
        x, y, z = lorenz_rk4(x, y, z, DT)
        all_px.append(x.copy())
        all_pz.append(z.copy())

    xs = np.concatenate(all_px)   # x-axis of butterfly
    zs = np.concatenate(all_pz)   # z-axis of butterfly (height in Lorenz space)

    # Map to canvas pixels — use actual np_pixels buffer size
    py5.load_np_pixels()
    h, w = py5.np_pixels.shape[:2]
    margin = 80

    x_min, x_max = xs.min(), xs.max()
    z_min, z_max = zs.min(), zs.max()

    # Maintain aspect ratio: center the attractor
    x_range = x_max - x_min
    z_range = z_max - z_min
    draw_w = w - 2 * margin
    draw_h = h - 2 * margin
    scale = min(draw_w / x_range, draw_h / z_range) * 0.90

    cx = w / 2
    cy = h / 2 + (z_min + z_range / 2) * scale * 0   # center

    px = ((xs - (x_min + x_max) / 2) * scale + cx).astype(np.int32)
    py_arr = (-(zs - (z_min + z_max) / 2) * scale + cy).astype(np.int32)  # flip z
    np.clip(px, 0, w - 1, out=px)
    np.clip(py_arr, 0, h - 1, out=py_arr)

    density = np.zeros((h, w), dtype=np.float32)
    np.add.at(density, (py_arr, px), 1.0)

    d = np.log1p(density)
    d /= d.max()

    # 3-stop palette: rust (low) → amber (mid) → gold (peak)
    d0 = np.clip(d * 2.0, 0.0, 1.0)           # rust → amber
    d1 = np.clip(d * 2.0 - 1.0, 0.0, 1.0)    # amber → gold

    r_f = RUST_COL[0]  * (1 - d0) + AMBER_COL[0] * d0 * (1 - d1) + GOLD_COL[0]  * d1
    g_f = RUST_COL[1]  * (1 - d0) + AMBER_COL[1] * d0 * (1 - d1) + GOLD_COL[1]  * d1
    b_f = RUST_COL[2]  * (1 - d0) + AMBER_COL[2] * d0 * (1 - d1) + GOLD_COL[2]  * d1

    # Multiply by d to keep background dark
    r_px = np.clip(r_f * d, 0, 255).astype(np.uint8)
    g_px = np.clip(g_f * d, 0, 255).astype(np.uint8)
    b_px = np.clip(b_f * d, 0, 255).astype(np.uint8)

    alpha = np.full((h, w), 255, dtype=np.uint8)
    pixels_arr = np.stack([alpha, r_px, g_px, b_px], axis=-1)


def draw():
    py5.load_np_pixels()
    # pixels_arr was built at actual buffer size in setup() — assign directly
    py5.np_pixels[:] = pixels_arr
    py5.update_np_pixels()

    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

"""
magnetic_pendulum — Three invisible attractors pulling a swinging pendulum
into unpredictable trajectories.

Basin-of-attraction fractal: for each starting position, simulate a damped
magnetic pendulum over three magnets and color by which magnet captures it.
The fractal boundary between basins reveals the hidden chaos.
"""

from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import save_preview_pil
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

RNG = np.random.default_rng()

# ── Palette ───────────────────────────────────────────────────────────────────
# Three basin colors + background
AMETHYST = np.array([0.29, 0.18, 0.48])     # deep amethyst
TEAL     = np.array([0.10, 0.42, 0.42])     # muted teal
COPPER   = np.array([0.77, 0.49, 0.24])     # burnished copper

# Bright versions for convergence-speed highlights
AMETHYST_BRIGHT = np.array([0.60, 0.40, 0.85])
TEAL_BRIGHT     = np.array([0.25, 0.80, 0.75])
COPPER_BRIGHT   = np.array([1.00, 0.75, 0.40])

BG_COLOR = np.array([0.055, 0.055, 0.07])


def simulate_pendulum(W, H):
    """
    Magnetic pendulum basin-of-attraction map.

    Physics: a pendulum bob swings over a plane with 3 magnets.
    - Gravity provides restoring force toward center (z=0 equilibrium)
    - Each magnet attracts the bob with F ~ 1/r^2
    - Damping dissipates energy until the bob settles over one magnet
    """

    # ── Magnet positions (equilateral triangle) ───────────────────────────────
    # Add small random perturbation for variety each run
    base_angle = RNG.uniform(0, 2 * np.pi)
    magnet_r = 1.0
    magnets = np.array([
        [magnet_r * np.cos(base_angle + k * 2 * np.pi / 3),
         magnet_r * np.sin(base_angle + k * 2 * np.pi / 3)]
        for k in range(3)
    ])

    # ── Physical parameters ───────────────────────────────────────────────────
    gravity   = 0.2        # restoring force strength
    magnetic  = 1.0        # magnetic attraction strength
    damping   = 0.18       # velocity damping
    height_sq = 0.15       # pendulum height² above magnet plane (softening)
    dt        = 0.02       # timestep
    max_steps = 800        # max integration steps
    capture_r = 0.08       # convergence radius²

    # ── Set up pixel grid in physical coords ──────────────────────────────────
    extent = 2.8
    xs = np.linspace(-extent, extent, W, dtype=np.float32)
    ys = np.linspace(-extent, extent, H, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    # Flatten for vectorized simulation
    N = W * H
    px = xx.ravel().copy()
    py = yy.ravel().copy()
    vx = np.zeros(N, dtype=np.float32)
    vy = np.zeros(N, dtype=np.float32)

    # Result arrays
    basin   = np.full(N, -1, dtype=np.int32)     # which magnet captured
    speed   = np.full(N, max_steps, dtype=np.int32)  # steps to converge

    active = np.ones(N, dtype=bool)  # still simulating

    # ── Integration loop ──────────────────────────────────────────────────────
    for step in range(max_steps):
        if not active.any():
            break

        idx = np.where(active)[0]
        px_a = px[idx]
        py_a = py[idx]
        vx_a = vx[idx]
        vy_a = vy[idx]

        # Gravity: restoring force toward origin
        ax = -gravity * px_a
        ay = -gravity * py_a

        # Magnetic forces from each magnet
        for m in range(3):
            dx = magnets[m, 0] - px_a
            dy = magnets[m, 1] - py_a
            r2 = dx * dx + dy * dy + height_sq
            r3 = r2 * np.sqrt(r2)
            ax += magnetic * dx / r3
            ay += magnetic * dy / r3

        # Damping
        ax -= damping * vx_a
        ay -= damping * vy_a

        # Velocity Verlet integration
        vx_a += ax * dt
        vy_a += ay * dt
        px_a += vx_a * dt
        py_a += vy_a * dt

        # Write back
        px[idx] = px_a
        py[idx] = py_a
        vx[idx] = vx_a
        vy[idx] = vy_a

        # Check convergence: close to a magnet with low velocity
        v_sq = vx_a * vx_a + vy_a * vy_a
        for m in range(3):
            dx = px_a - magnets[m, 0]
            dy = py_a - magnets[m, 1]
            d2 = dx * dx + dy * dy
            captured = (d2 < capture_r) & (v_sq < 0.01)
            captured_idx = idx[captured]
            basin[captured_idx] = m
            speed[captured_idx] = step
            active[captured_idx] = False

    # Assign uncaptured pixels to nearest magnet
    uncaptured = basin == -1
    if uncaptured.any():
        uc_idx = np.where(uncaptured)[0]
        for m in range(3):
            dx = px[uc_idx] - magnets[m, 0]
            dy = py[uc_idx] - magnets[m, 1]
            d2 = dx * dx + dy * dy
            if m == 0:
                best_d = d2.copy()
                basin[uc_idx] = 0
            else:
                closer = d2 < best_d
                basin[uc_idx[closer]] = m
                best_d[closer] = d2[closer]

    # ── Color mapping ─────────────────────────────────────────────────────────
    basin   = basin.reshape(H, W)
    speed   = speed.reshape(H, W).astype(np.float32)

    # Normalize speed to [0, 1]: fast convergence = bright, slow = dark
    speed_norm = 1.0 - (speed / max_steps) ** 0.5

    # Base colors per basin
    dark_colors  = [AMETHYST, TEAL, COPPER]
    bright_colors = [AMETHYST_BRIGHT, TEAL_BRIGHT, COPPER_BRIGHT]

    canvas = np.zeros((H, W, 3), dtype=np.float32)

    for m in range(3):
        mask = basin == m
        t = speed_norm[mask][:, np.newaxis]
        color = (1 - t) * dark_colors[m] + t * bright_colors[m]
        canvas[mask] = color

    # ── Post-processing ───────────────────────────────────────────────────────
    # Subtle edge enhancement at basin boundaries via Laplacian
    gray = canvas.mean(axis=2)
    edge = np.abs(gaussian_filter(gray, sigma=1) - gaussian_filter(gray, sigma=0.5))
    edge_norm = edge / (edge.max() + 1e-12)
    # Darken basin boundaries slightly
    canvas *= (1.0 - 0.3 * edge_norm[:, :, np.newaxis])

    # Bloom on bright spots
    bloom = gaussian_filter(canvas, sigma=[4, 4, 0])
    canvas = canvas + bloom * 0.12

    # Vignette
    ys_n = np.linspace(-1, 1, H, dtype=np.float32)
    xs_n = np.linspace(-1, 1, W, dtype=np.float32)
    xg, yg = np.meshgrid(xs_n, ys_n)
    vignette = (1.0 - 0.35 * (xg**2 + yg**2)).clip(0.5, 1.0)
    canvas *= vignette[:, :, np.newaxis]

    return canvas.clip(0.0, 1.0)


def setup():
    py5.size(*SIZE)
    py5.no_loop()


def draw():
    W, H = SIZE
    result    = simulate_pendulum(W, H)
    result_u8 = (result * 255).astype(np.uint8)
    save_preview_pil(result_u8, SKETCH_DIR, filename="preview.png", mode="RGB")
    py5.exit_sketch()


py5.run_sketch()

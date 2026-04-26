"""
ink_diffusion — The quiet moment when ink meets wet paper
Stochastic particle diffusion simulating sumi-e ink wash bleeding on washi paper.
Multiple ink drops release particles that undergo Brownian motion along paper fibers,
accumulating density trails that fray into gossamer tendrils. Drops interact through
connecting flows and satellite spatters add natural imperfection.
"""

from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 120

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE = (3840, 2160)
SIZE = PREVIEW_SIZE

# --- Color palette ---
PARCHMENT = np.array([245, 240, 232], dtype=np.float64)   # warm off-white
INK_BLACK = np.array([26, 26, 26], dtype=np.float64)       # sumi ink
WARM_GREY = np.array([107, 101, 96], dtype=np.float64)     # wash grey
INDIGO    = np.array([58, 61, 92], dtype=np.float64)        # faint blue tint

# --- Simulation parameters ---
NUM_DROPS = np.random.randint(5, 9)            # number of ink drops
DIFFUSION_STEPS = 800                          # simulation steps
BROWNIAN_SCALE = 3.2                           # random walk step size

# Global fiber direction (paper grain)
FIBER_ANGLE = np.random.uniform(-np.pi / 6, np.pi / 6)  # slight tilt from horizontal
FIBER_DX = np.cos(FIBER_ANGLE)
FIBER_DY = np.sin(FIBER_ANGLE)

density = None
drop_centers = None
drop_radii = None
drop_concentrations = None


def generate_ink_drops():
    """Generate random ink drop positions with varying sizes and concentrations."""
    global drop_centers, drop_radii, drop_concentrations
    w, h = SIZE
    margin = min(w, h) * 0.12

    centers = []
    radii = []
    concentrations = []
    for _ in range(NUM_DROPS):
        cx = np.random.uniform(margin, w - margin)
        cy = np.random.uniform(margin, h - margin)
        r = np.random.uniform(min(w, h) * 0.015, min(w, h) * 0.07)
        # Variable concentration: some drops are dilute washes, some are dense
        conc = np.random.choice([0.3, 0.5, 0.7, 1.0, 1.0], p=[0.15, 0.2, 0.2, 0.25, 0.2])
        centers.append((cx, cy))
        radii.append(r)
        concentrations.append(conc)

    drop_centers = np.array(centers)
    drop_radii = np.array(radii)
    drop_concentrations = np.array(concentrations)


def simulate_drop(cx, cy, r, concentration, w, h, local_density):
    """Simulate a single ink drop diffusion."""
    n_particles = int(60000 * concentration)

    angles = np.random.uniform(0, 2 * np.pi, n_particles)
    radii_init = np.sqrt(np.random.uniform(0, 1, n_particles)) * r
    px = cx + radii_init * np.cos(angles)
    py = cy + radii_init * np.sin(angles)

    # Drift along fiber direction with some per-drop variation
    drift_strength = np.random.uniform(1.2, 2.5)
    angle_jitter = np.random.uniform(-0.3, 0.3)
    ddx = np.cos(FIBER_ANGLE + angle_jitter) * drift_strength
    ddy = np.sin(FIBER_ANGLE + angle_jitter) * drift_strength

    # Per-particle lifetime (variable creates density gradients)
    lifetimes = np.random.randint(
        DIFFUSION_STEPS // 5, DIFFUSION_STEPS, n_particles
    )

    for step in range(DIFFUSION_STEPS):
        alive = step < lifetimes

        noise_x = np.random.randn(n_particles) * BROWNIAN_SCALE
        noise_y = np.random.randn(n_particles) * BROWNIAN_SCALE

        dist = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        speed_factor = 1.0 / (1.0 + dist * 0.003)

        # Fiber-direction anisotropy: noise is stretched along fiber direction
        fiber_noise = np.random.randn(n_particles) * 1.5
        noise_x += fiber_noise * FIBER_DX
        noise_y += fiber_noise * FIBER_DY

        px += (noise_x + ddx) * speed_factor * alive
        py += (noise_y + ddy) * speed_factor * alive

        px = np.clip(px, 0, w - 1)
        py = np.clip(py, 0, h - 1)

        ix = px[alive].astype(np.int32)
        iy = py[alive].astype(np.int32)
        np.add.at(local_density, (iy, ix), concentration)

    # Concentrated center
    center_x = np.clip(int(cx), 0, w - 1)
    center_y = np.clip(int(cy), 0, h - 1)
    cr = int(r * 1.8)
    y_grid, x_grid = np.mgrid[
        max(0, center_y - cr): min(h, center_y + cr),
        max(0, center_x - cr): min(w, center_x + cr),
    ]
    if y_grid.size > 0:
        center_dist = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
        center_mask = center_dist < r
        center_intensity = np.exp(-center_dist / (r * 0.5)) * 300 * concentration
        local_density[
            max(0, center_y - cr): min(h, center_y + cr),
            max(0, center_x - cr): min(w, center_x + cr),
        ] += center_intensity * center_mask


def simulate_tendrils(w, h, local_density):
    """Create connecting tendrils between nearby drops."""
    n = len(drop_centers)
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.sqrt(np.sum((drop_centers[i] - drop_centers[j]) ** 2))
            # Connect drops that are reasonably close
            max_connect = min(w, h) * 0.55
            if dist < max_connect:
                # Spawn flow particles between the two drops
                n_tendril = int(15000 * (1 - dist / max_connect))
                if n_tendril < 500:
                    continue

                # Start from drop i, drift toward drop j
                cx1, cy1 = drop_centers[i]
                cx2, cy2 = drop_centers[j]
                r1 = drop_radii[i]

                t_init = np.random.uniform(0, 0.3, n_tendril)
                px = cx1 + (cx2 - cx1) * t_init + np.random.randn(n_tendril) * r1
                py = cy1 + (cy2 - cy1) * t_init + np.random.randn(n_tendril) * r1

                flow_dx = (cx2 - cx1) / dist * 0.8
                flow_dy = (cy2 - cy1) / dist * 0.8

                for step in range(DIFFUSION_STEPS // 2):
                    noise_x = np.random.randn(n_tendril) * BROWNIAN_SCALE * 0.8
                    noise_y = np.random.randn(n_tendril) * BROWNIAN_SCALE * 0.8

                    px += noise_x + flow_dx
                    py += noise_y + flow_dy

                    px = np.clip(px, 0, w - 1)
                    py = np.clip(py, 0, h - 1)

                    ix = px.astype(np.int32)
                    iy = py.astype(np.int32)
                    np.add.at(local_density, (iy, ix), 0.3)


def simulate_splatter(w, h, local_density):
    """Add tiny satellite drops around main impacts."""
    for i in range(len(drop_centers)):
        cx, cy = drop_centers[i]
        r = drop_radii[i]
        conc = drop_concentrations[i]

        n_satellites = np.random.randint(3, 10)
        for _ in range(n_satellites):
            angle = np.random.uniform(0, 2 * np.pi)
            dist = np.random.uniform(r * 1.5, r * 4.0)
            sx = cx + np.cos(angle) * dist
            sy = cy + np.sin(angle) * dist

            if 0 <= sx < w and 0 <= sy < h:
                sr = np.random.uniform(2, max(3, r * 0.15))
                n_p = int(np.random.uniform(500, 3000) * conc)

                angles_s = np.random.uniform(0, 2 * np.pi, n_p)
                radii_s = np.sqrt(np.random.uniform(0, 1, n_p)) * sr
                spx = sx + radii_s * np.cos(angles_s)
                spy = sy + radii_s * np.sin(angles_s)

                for step in range(150):
                    noise_x = np.random.randn(n_p) * 1.5
                    noise_y = np.random.randn(n_p) * 1.5
                    spx += noise_x
                    spy += noise_y
                    spx = np.clip(spx, 0, w - 1)
                    spy = np.clip(spy, 0, h - 1)
                    ix = spx.astype(np.int32)
                    iy = spy.astype(np.int32)
                    np.add.at(local_density, (iy, ix), conc * 0.5)


def simulate_diffusion():
    """Run particle diffusion for all drops, accumulating density."""
    global density
    w, h = SIZE
    density = np.zeros((h, w), dtype=np.float64)

    for i in range(NUM_DROPS):
        cx, cy = drop_centers[i]
        r = drop_radii[i]
        conc = drop_concentrations[i]
        print(f"  Drop {i + 1}/{NUM_DROPS} (concentration={conc:.1f}, r={r:.0f})")
        simulate_drop(cx, cy, r, conc, w, h, density)

    print("  Generating tendrils...")
    simulate_tendrils(w, h, density)

    print("  Adding splatter...")
    simulate_splatter(w, h, density)


def render_to_pixels():
    """Convert density field to RGBA pixel array on parchment background."""
    w, h = SIZE
    d = density.copy()
    d = np.log1p(d)
    d_max = np.percentile(d[d > 0], 99.5) if np.any(d > 0) else 1.0
    d = np.clip(d / d_max, 0, 1)

    # Gamma for ink-like tonal curve
    d = np.power(d, 0.65)

    # Build color: three-stop gradient with indigo in mid-tones
    pixels = np.zeros((h, w, 3), dtype=np.float64)

    low_mask = d < 0.25
    mid_mask = (d >= 0.25) & (d < 0.65)
    high_mask = d >= 0.65

    # Low density: parchment to warm grey with indigo tint
    t_low = d / 0.25
    for c in range(3):
        mix_color = WARM_GREY[c] * 0.6 + INDIGO[c] * 0.4
        pixels[:, :, c] += (
            PARCHMENT[c] * (1 - t_low) + mix_color * t_low
        ) * low_mask

    # Mid density: warm grey to ink black
    t_mid = (d - 0.25) / 0.4
    for c in range(3):
        pixels[:, :, c] += (
            WARM_GREY[c] * (1 - t_mid) + INK_BLACK[c] * t_mid
        ) * mid_mask

    # High density: near ink black
    t_high = (d - 0.65) / 0.35
    for c in range(3):
        pixels[:, :, c] += (
            INK_BLACK[c] * (1 - t_high * 0.08)
        ) * high_mask

    # Subtle paper texture
    texture = np.random.uniform(-5, 5, (h, w, 3))
    pixels += texture * (1 - d[:, :, np.newaxis] * 0.85)

    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    return pixels


def setup():
    py5.size(*SIZE)
    py5.background(245, 240, 232)

    print("Generating ink drops...")
    generate_ink_drops()

    print(f"Simulating diffusion for {NUM_DROPS} drops...")
    simulate_diffusion()

    print("Rendering...")
    pixels = render_to_pixels()

    # Write to py5 pixel buffer
    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]

    if actual_h != SIZE[1] or actual_w != SIZE[0]:
        from PIL import Image
        img = Image.fromarray(pixels)
        img = img.resize((actual_w, actual_h), Image.LANCZOS)
        pixels = np.array(img)

    py5.np_pixels[:, :, 1] = pixels[:, :, 0]  # R
    py5.np_pixels[:, :, 2] = pixels[:, :, 1]  # G
    py5.np_pixels[:, :, 3] = pixels[:, :, 2]  # B
    py5.update_np_pixels()

    print("Done.")


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

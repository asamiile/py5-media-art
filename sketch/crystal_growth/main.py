"""
crystal_growth — The slow persistence of mineral crystallization
Dendritic crystal growth from multiple seeds using stochastic branching
with crystallographic angle preferences. Branches grow with Brownian
deflection and spawn sub-branches at 60°/90° angles, creating mineral
dendrites glowing amethyst-gold against cave darkness.
"""

from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes
from lib.paths import sketch_dir
SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 120

PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# --- Color palette ---
BG_COLOR = np.array([12, 12, 18], dtype=np.float64)
AMETHYST = np.array([138, 92, 168], dtype=np.float64)
QUARTZ_ROSE = np.array([195, 155, 170], dtype=np.float64)
MINERAL_GOLD = np.array([212, 185, 120], dtype=np.float64)
DEEP_VIOLET = np.array([68, 42, 100], dtype=np.float64)
ICE_WHITE = np.array([220, 215, 230], dtype=np.float64)

# --- Growth parameters ---
NUM_SEEDS = np.random.randint(3, 6)
MAX_DEPTH = 8
STEP_LENGTH = 1.8               # smaller step = smoother lines
DEFLECTION_STD = 0.04
MAX_TOTAL_SEGMENTS = 400000
PREFERRED_ANGLES = [np.pi / 3, -np.pi / 3, np.pi / 2, -np.pi / 2,
                    np.pi / 6, -np.pi / 6]

density = None
age_field = None
seed_centers = None


def draw_line_on_grid(x0, y0, x1, y1, thickness, value, age_val, w, h):
    """Draw an anti-aliased thick line segment on the density grid."""
    global density, age_field
    dx = x1 - x0
    dy = y1 - y0
    length = np.sqrt(dx * dx + dy * dy)
    if length < 0.1:
        return

    # Normal direction
    nx = -dy / length
    ny = dx / length

    # Sample along the line
    n_samples = max(2, int(length * 2))
    r = max(1, int(thickness))

    for i in range(n_samples):
        t = i / max(1, n_samples - 1)
        cx = x0 + dx * t
        cy = y0 + dy * t
        ix, iy = int(cx), int(cy)

        for ddx in range(-r, r + 1):
            for ddy in range(-r, r + 1):
                d2 = ddx * ddx + ddy * ddy
                if d2 <= r * r:
                    px, py_c = ix + ddx, iy + ddy
                    if 0 <= px < w and 0 <= py_c < h:
                        falloff = 1.0 - (np.sqrt(d2) / max(1, r)) * 0.7
                        density[py_c, px] += value * falloff
                        if age_field[py_c, px] < 0:
                            age_field[py_c, px] = age_val


def grow_crystals():
    """Grow dendritic crystals from multiple seeds."""
    global density, age_field, seed_centers
    w, h = SIZE
    density = np.zeros((h, w), dtype=np.float64)
    age_field = np.full((h, w), -1.0, dtype=np.float64)

    margin = min(w, h) * 0.15
    global_age = 0
    total_segments = 0

    seed_centers = []

    # Branch storage: [x, y, prev_x, prev_y, angle, depth, max_steps, step, thickness, seed_id]
    branches = []

    for i in range(NUM_SEEDS):
        sx = np.random.uniform(margin, w - margin)
        sy = np.random.uniform(margin, h - margin)
        seed_centers.append((sx, sy))

        # Draw seed core glow
        core_r = np.random.randint(8, 18)
        for ddx in range(-core_r, core_r + 1):
            for ddy in range(-core_r, core_r + 1):
                d2 = ddx * ddx + ddy * ddy
                if d2 <= core_r * core_r:
                    px, py_c = int(sx) + ddx, int(sy) + ddy
                    if 0 <= px < w and 0 <= py_c < h:
                        dist = np.sqrt(d2)
                        intensity = np.exp(-dist / (core_r * 0.4)) * 5
                        density[py_c, px] += intensity
                        if age_field[py_c, px] < 0:
                            age_field[py_c, px] = 0

        n_arms = np.random.randint(4, 8)
        base_angle = np.random.uniform(0, 2 * np.pi)
        for j in range(n_arms):
            angle = base_angle + j * (2 * np.pi / n_arms) + np.random.uniform(-0.1, 0.1)
            max_steps = int(np.random.uniform(300, 500))
            branches.append([sx, sy, sx, sy, angle, 0, max_steps, 0, 3.0, i + 1])

    print(f"  {NUM_SEEDS} seeds, {len(branches)} initial arms")

    while branches and total_segments < MAX_TOTAL_SEGMENTS:
        next_branches = []
        new_children = []

        for br in branches:
            x, y, prev_x, prev_y, angle, depth, max_steps, step, thickness, seed_id = br

            step += 1
            prev_x, prev_y = x, y

            # Angular deflection
            angle += np.random.randn() * DEFLECTION_STD

            # Move
            x += np.cos(angle) * STEP_LENGTH
            y += np.sin(angle) * STEP_LENGTH

            ix, iy = int(x), int(y)
            if ix < 2 or ix >= w - 2 or iy < 2 or iy >= h - 2:
                continue
            if step >= max_steps:
                continue

            # Draw line segment from prev to current
            draw_line_on_grid(prev_x, prev_y, x, y, thickness, 0.8, global_age, w, h)

            global_age += 1
            total_segments += 1

            br[:] = [x, y, prev_x, prev_y, angle, depth, max_steps, step, thickness, seed_id]
            next_branches.append(br)

            # Branch spawning
            if (depth < MAX_DEPTH and
                step > 15 and
                total_segments + len(new_children) < MAX_TOTAL_SEGMENTS):

                # Branch probability decreases with depth
                branch_prob = 0.035 * (0.75 ** depth)
                if np.random.random() < branch_prob:
                    child_angle = angle + PREFERRED_ANGLES[np.random.randint(len(PREFERRED_ANGLES))]
                    child_depth = depth + 1
                    child_decay = 0.72 ** child_depth
                    child_max = int(np.random.uniform(100, 250) * child_decay)
                    child_thick = max(1.0, thickness * 0.7)
                    new_children.append([x, y, x, y, child_angle, child_depth,
                                        child_max, 0, child_thick, seed_id])

        branches = next_branches + new_children

        if total_segments % 50000 < 200:
            print(f"    {total_segments}/{MAX_TOTAL_SEGMENTS} segments, "
                  f"{len(branches)} active")

    print(f"  Growth complete: {total_segments} segments")


def render_to_pixels():
    """Render the crystal field to pixels with glow."""
    w, h = SIZE

    pixels = np.zeros((h, w, 3), dtype=np.float64)
    pixels[:, :] = BG_COLOR

    mask = age_field >= 0
    if not mask.any():
        return pixels.astype(np.uint8)

    max_age = age_field[mask].max()
    age_norm = np.zeros((h, w), dtype=np.float64)
    age_norm[mask] = age_field[mask] / max(1, max_age)

    d = density.copy()
    d = np.log1p(d)
    d_max = np.percentile(d[d > 0], 99) if np.any(d > 0) else 1.0
    d = np.clip(d / d_max, 0, 1)

    # 4-stop color gradient by age
    crystal_color = np.zeros((h, w, 3), dtype=np.float64)
    t = age_norm

    stops = [
        (0.0, 0.15, DEEP_VIOLET, AMETHYST),
        (0.15, 0.45, AMETHYST, QUARTZ_ROSE),
        (0.45, 0.75, QUARTZ_ROSE, MINERAL_GOLD),
        (0.75, 1.0, MINERAL_GOLD, ICE_WHITE),
    ]

    for t_start, t_end, color_a, color_b in stops:
        s = (t >= t_start) & (t < t_end)
        tt = np.clip((t - t_start) / (t_end - t_start), 0, 1)
        for c in range(3):
            crystal_color[:, :, c] += (
                color_a[c] * (1 - tt) + color_b[c] * tt
            ) * s

    # Brightness from density
    brightness = 0.25 + 0.75 * np.power(d, 0.8)
    for c in range(3):
        pixels[:, :, c] = np.where(
            mask,
            crystal_color[:, :, c] * brightness,
            pixels[:, :, c]
        )

    # Multi-scale glow
    glow_base = d * mask
    for sigma, intensity in [(2, 0.45), (5, 0.3), (12, 0.2), (30, 0.12), (60, 0.06)]:
        blurred = gaussian_filter(glow_base, sigma=sigma)
        for c in range(3):
            glow_color = AMETHYST[c] * 0.5 + QUARTZ_ROSE[c] * 0.3 + DEEP_VIOLET[c] * 0.2
            pixels[:, :, c] += blurred * glow_color * intensity

    # Background mineral sparkle (tiny dots)
    n_sparkle = 400
    sx = np.random.randint(0, w, n_sparkle)
    sy = np.random.randint(0, h, n_sparkle)
    for s in range(n_sparkle):
        if not mask[sy[s], sx[s]]:
            b = np.random.uniform(10, 35)
            for c in range(3):
                col = AMETHYST[c] * 0.3 + QUARTZ_ROSE[c] * 0.2
                pixels[sy[s], sx[s], c] += b * col / 255

    # Subtle noise
    pixels += np.random.uniform(-1.5, 1.5, (h, w, 3))

    return np.clip(pixels, 0, 255).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.background(12, 12, 18)

    print("Growing crystals...")
    grow_crystals()

    print("Rendering...")
    pixels = render_to_pixels()

    py5.load_np_pixels()
    actual_h, actual_w = py5.np_pixels.shape[:2]

    if actual_h != SIZE[1] or actual_w != SIZE[0]:
        from PIL import Image
        img = Image.fromarray(pixels)
        img = img.resize((actual_w, actual_h), Image.LANCZOS)
        pixels = np.array(img)

    py5.np_pixels[:, :, 1] = pixels[:, :, 0]
    py5.np_pixels[:, :, 2] = pixels[:, :, 1]
    py5.np_pixels[:, :, 3] = pixels[:, :, 2]
    py5.update_np_pixels()

    print("Done.")


def draw():
    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR, filename="preview.png")


py5.run_sketch()

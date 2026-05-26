"""
sumi_ink_dissolution
====================
A 2D diffusion-advection simulation of ink drops dissolving in still water.
Multiple drops are introduced over time, blooming into organic tendrils via
curl-noise advection and Gaussian diffusion — a digital sumi-e (ink wash).

Palette: Warm Parchment (bg), Sumi Ink Black, Warm Sepia Wash, Deep Indigo
Format: 15s @ 60fps -> sumi_ink_dissolution.mp4
"""

from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

# ── Configuration ────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# ── Simulation Settings ──────────────────────────────────────────────────────
GW, GH = 960, 540           # Simulation grid (16:9)
DIFFUSION_RATE = 0.8         # Gaussian diffusion spread per step (increased)
ADVECTION_STRENGTH = 6.0     # Curl-noise advection magnitude (boosted 2x)
NOISE_SCALE = 0.003          # Lower = larger swirl structures
NOISE_Z_SPEED = 0.004        # Temporal drift speed
EVAPORATION = 0.9992         # Slow density decay per frame
SUBSTEPS = 4                 # Multiple simulation steps per render frame
N_DROPS = 12                 # Total ink drops over the animation
DROP_RADIUS_BASE = 55        # Much larger initial drop radius

# ── Ink Drop Schedule ────────────────────────────────────────────────────────
np.random.seed(None)  # No fixed seed — varies each run
drop_schedule = []

# First 3 drops appear early and spread across the canvas
early_positions = [
    (GW * 0.3, GH * 0.35),
    (GW * 0.65, GH * 0.55),
    (GW * 0.45, GH * 0.7),
]
for i, (px, py) in enumerate(early_positions):
    frame_trigger = i * 30 + np.random.randint(0, 10)
    radius = DROP_RADIUS_BASE + np.random.randint(0, 20)
    intensity = np.random.uniform(0.7, 1.0)
    drop_schedule.append((frame_trigger, int(px), int(py), radius, intensity))

# Remaining drops spread across full canvas over time
for i in range(N_DROPS - 3):
    frame_trigger = int(((i + 1) / (N_DROPS - 2)) * TOTAL_FRAMES * 0.65) + np.random.randint(0, 40)
    cx = np.random.randint(GW // 8, GW * 7 // 8)
    cy = np.random.randint(GH // 8, GH * 7 // 8)
    radius = DROP_RADIUS_BASE + np.random.randint(-15, 25)
    intensity = np.random.uniform(0.5, 1.0)
    drop_schedule.append((frame_trigger, cx, cy, radius, intensity))

# ── State Variables ──────────────────────────────────────────────────────────
density = None
velocity_x = None
velocity_y = None
paper_texture = None


def _fast_curl_noise(t_offset):
    """Fast curl-noise using multi-octave sine interference for organic swirls."""
    global velocity_x, velocity_y

    xs = np.arange(GW, dtype=np.float32) * NOISE_SCALE
    ys = np.arange(GH, dtype=np.float32) * NOISE_SCALE
    xx, yy = np.meshgrid(xs, ys)
    z = t_offset

    # Multi-octave interference pattern — lower frequencies for larger swirls
    f1 = np.sin(xx * 1.2 + z * 0.6) * np.cos(yy * 1.5 - z * 0.9)
    f2 = np.sin(xx * 2.4 - z * 0.4 + yy * 1.3) * 0.6
    f3 = np.cos(xx * 0.5 + yy * 0.7 + z * 1.2) * np.sin(yy * 1.8 + z * 0.25) * 0.4
    f4 = np.sin((xx + yy) * 0.9 + z * 0.7) * np.cos((xx - yy) * 1.6 - z * 0.3) * 0.3
    f5 = np.cos(xx * 3.5 + z * 1.1) * np.sin(yy * 3.2 - z * 0.8) * 0.15  # Fine detail

    noise = f1 + f2 + f3 + f4 + f5

    # Curl via finite differences: dN/dy -> vx,  -dN/dx -> vy
    velocity_x = np.zeros_like(noise)
    velocity_y = np.zeros_like(noise)

    velocity_x[1:-1, :] = (noise[2:, :] - noise[:-2, :]) * 0.5
    velocity_y[:, 1:-1] = -(noise[:, 2:] - noise[:, :-2]) * 0.5

    # Add gentle rotational eddies around random centers
    for _ in range(3):
        ecx = np.random.uniform(0.2, 0.8) * GW * NOISE_SCALE
        ecy = np.random.uniform(0.2, 0.8) * GH * NOISE_SCALE
        rx = (xx - ecx)
        ry = (yy - ecy)
        dist = np.sqrt(rx**2 + ry**2) + 0.001
        eddy = 0.12 * np.sin(z * 0.3 + dist * 8.0) * np.exp(-dist * 1.5)
        velocity_x += -ry * eddy / dist
        velocity_y += rx * eddy / dist


def _diffuse(field, rate):
    """Apply Laplacian diffusion with 3x3 kernel."""
    lap = (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) +
        0.5 * np.roll(np.roll(field, 1, axis=0), 1, axis=1) +
        0.5 * np.roll(np.roll(field, 1, axis=0), -1, axis=1) +
        0.5 * np.roll(np.roll(field, -1, axis=0), 1, axis=1) +
        0.5 * np.roll(np.roll(field, -1, axis=0), -1, axis=1) -
        6.0 * field
    )
    return field + rate * lap * 0.08  # Increased diffusion coefficient


def _advect(field, vx, vy, strength):
    """Semi-Lagrangian advection with bilinear interpolation."""
    yy, xx = np.mgrid[:GH, :GW].astype(np.float32)

    src_x = xx - vx * strength
    src_y = yy - vy * strength

    src_x = np.clip(src_x, 0, GW - 1.001)
    src_y = np.clip(src_y, 0, GH - 1.001)

    x0 = src_x.astype(np.int32)
    y0 = src_y.astype(np.int32)
    x1 = np.minimum(x0 + 1, GW - 1)
    y1 = np.minimum(y0 + 1, GH - 1)
    fx = src_x - x0
    fy = src_y - y0

    return (
        field[y0, x0] * (1 - fx) * (1 - fy) +
        field[y0, x1] * fx * (1 - fy) +
        field[y1, x0] * (1 - fx) * fy +
        field[y1, x1] * fx * fy
    )


def _add_drop(cx, cy, radius, intensity):
    """Add a soft circular ink drop with organic edge irregularity."""
    global density
    y_idx, x_idx = np.ogrid[:GH, :GW]
    dist2 = ((x_idx - cx)**2 + (y_idx - cy)**2).astype(np.float32)
    sigma = radius * 0.5
    drop = intensity * np.exp(-dist2 / (2.0 * sigma**2))
    # Cut off at ~2.5 radii
    drop[dist2 > (radius * 2.5)**2] = 0.0
    density = np.clip(density + drop, 0.0, 1.0)


def setup():
    global density, paper_texture
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.frame_rate(FPS)

    density = np.zeros((GH, GW), dtype=np.float32)

    # Generate paper texture once
    paper_texture = np.random.uniform(-4, 4, (GH, GW)).astype(np.float32)
    for _ in range(8):
        paper_texture = (
            np.roll(paper_texture, 1, axis=0) + np.roll(paper_texture, -1, axis=0) +
            np.roll(paper_texture, 1, axis=1) + np.roll(paper_texture, -1, axis=1) +
            paper_texture * 2
        ) / 6.0

    # Add the first drops immediately for visual interest
    for ft, cx, cy, r, inten in drop_schedule:
        if ft == 0:
            _add_drop(cx, cy, r, inten)

    print(f"[{WORK_NAME}] Sumi ink dissolution initialized: {GW}x{GH}. Canvas: {SIZE[0]}x{SIZE[1]}.")


def draw():
    global density

    fc = py5.frame_count
    t = fc * NOISE_Z_SPEED

    # ── Check for new ink drops ──────────────────────────────────────────────
    for frame_trigger, cx, cy, radius, intensity in drop_schedule:
        if fc == frame_trigger:
            _add_drop(cx, cy, radius, intensity)

    # ── Update curl-noise velocity field ─────────────────────────────────────
    if fc % 2 == 1:
        _fast_curl_noise(t)

    # ── Multiple Simulation Substeps for dramatic dissolution ────────────────
    for _ in range(SUBSTEPS):
        # Diffuse
        density = _diffuse(density, DIFFUSION_RATE)

        # Advect
        if velocity_x is not None:
            density = _advect(density, velocity_x, velocity_y, ADVECTION_STRENGTH)

        # Evaporate slowly
        density *= EVAPORATION

    # Clamp
    density = np.clip(density, 0.0, 1.0)

    # ── Render ───────────────────────────────────────────────────────────────
    bg_r, bg_g, bg_b = 245.0, 238.0, 228.0    # Warm parchment
    ink_r, ink_g, ink_b = 15.0, 12.0, 18.0     # Sumi black
    sepia_r, sepia_g, sepia_b = 130.0, 105.0, 82.0  # Warm sepia
    indigo_r, indigo_g, indigo_b = 40.0, 30.0, 75.0  # Deep indigo

    d = density

    # Smooth multi-zone color mapping
    w_light = np.clip(1.0 - d * 2.5, 0.0, 1.0)
    w_sepia = np.clip(d * 3.5, 0.0, 1.0) * np.clip(1.0 - (d - 0.3) * 2.5, 0.0, 1.0)
    w_indigo = np.clip((d - 0.2) * 3.0, 0.0, 1.0) * np.clip(1.0 - (d - 0.55) * 2.5, 0.0, 1.0)
    w_ink = np.clip((d - 0.4) * 2.0, 0.0, 1.0)

    w_total = w_light + w_sepia + w_indigo + w_ink + 1e-8
    w_light /= w_total
    w_sepia /= w_total
    w_indigo /= w_total
    w_ink /= w_total

    r_grid = (bg_r * w_light + sepia_r * w_sepia + indigo_r * w_indigo + ink_r * w_ink)
    g_grid = (bg_g * w_light + sepia_g * w_sepia + indigo_g * w_indigo + ink_g * w_ink)
    b_grid = (bg_b * w_light + sepia_b * w_sepia + indigo_b * w_indigo + ink_b * w_ink)

    # Paper texture (more visible on light areas)
    tex_weight = np.clip(1.0 - d * 3.0, 0.0, 1.0)
    r_grid += paper_texture * tex_weight
    g_grid += paper_texture * tex_weight * 0.9
    b_grid += paper_texture * tex_weight * 0.7

    # Convert to uint8
    r_grid = np.clip(r_grid, 0, 255).astype(np.uint8)
    g_grid = np.clip(g_grid, 0, 255).astype(np.uint8)
    b_grid = np.clip(b_grid, 0, 255).astype(np.uint8)

    # ── Upscale to Canvas ────────────────────────────────────────────────────
    W, H = SIZE
    scale_x = W // GW
    scale_y = H // GH
    scale_block = np.ones((scale_y, scale_x), dtype=np.uint8)

    r_up = np.kron(r_grid, scale_block)[:H, :W]
    g_up = np.kron(g_grid, scale_block)[:H, :W]
    b_up = np.kron(b_grid, scale_block)[:H, :W]

    # ── Write to Py5 Pixels Buffer ───────────────────────────────────────────
    py5.load_np_pixels()
    ah, aw = py5.np_pixels.shape[:2]
    py5.np_pixels[:ah, :aw, 0] = 255
    py5.np_pixels[:ah, :aw, 1] = r_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 2] = g_up[:ah, :aw]
    py5.np_pixels[:ah, :aw, 3] = b_up[:ah, :aw]
    py5.update_np_pixels()

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid_frame = TOTAL_FRAMES // 2
        shutil.copyfile(
            str(FRAMES_DIR / f"frame-{mid_frame:04d}.png"),
            str(SKETCH_DIR / PREVIEW_FILENAME)
        )
        print(f"[Render Preview] Saved preview image as {PREVIEW_FILENAME}")

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

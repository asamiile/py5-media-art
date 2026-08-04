"""
kinetic_kuramoto_firefly_sync_2d

A 4K kinetic visualization of the Kuramoto model of coupled phase oscillators,
rendered as a bioluminescent firefly swarm spontaneously synchronizing. 500
fireflies drift across the void, each flashing at its own natural rhythm.
As the coupling constant K slowly rises above the critical threshold K_c,
the chaos of independent rhythms suddenly collapses into a single coherent pulse —
the most beautiful phase transition in nature.
"""
import struct
from pathlib import Path
import shutil
import subprocess
import sys
import math
import numpy as np

import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840x2160

# --- Simulation constants ---
N = 300             # Number of oscillators (fireflies)
DT = 0.06           # Euler integration timestep
SIGMA_OMEGA = 0.8   # Std dev of natural frequency distribution (Lorentzian-like)
K_START = 0.0       # Initial coupling strength
K_END = 3.2         # Final coupling strength (well above critical K_c ≈ 2*sigma)
DRIFT_SPEED = 0.4   # How fast fireflies drift (sim coords per frame)

# Sim coordinates: 960x540, upscaled to 4K
SIM_W, SIM_H = 960, 540

# --- Firefly visual parameters ---
FIREFLY_RADIUS = 12    # Visual glow radius in sim pixels
TRAIL_ALPHA = 0.88     # Trail decay factor per frame (1=no decay, 0=instant)

def pack_argb(a, r, g, b):
    """Pack ARGB as signed int32 (py5 format)."""
    val = ((int(a) & 0xFF) << 24) | ((int(r) & 0xFF) << 16) | ((int(g) & 0xFF) << 8) | (int(b) & 0xFF)
    return struct.unpack('i', struct.pack('I', val & 0xFFFFFFFF))[0]


def omega_to_rgb(omega, omega_max=2.5):
    """Map natural frequency to RGB color. Slow=violet, fast=amber/gold."""
    t = np.clip((omega + omega_max) / (2 * omega_max), 0, 1)
    # Blue(0) → Cyan → Green → Yellow → Red(1)
    # Map through hue 240→0 (blue→red)
    hue = (1.0 - t) * 260.0   # 260 (violet) → 0 (red)
    # Simple HSV→RGB with S=1, V=1
    hf = hue / 60.0
    i = int(hf) % 6
    f = hf - int(hf)
    q = 1 - f
    pairs = [(1,f,0),(q,1,0),(0,1,f),(0,q,1),(f,0,1),(1,0,q)]
    r_f, g_f, b_f = pairs[i % 6]
    return int(r_f * 230), int(g_f * 230), int(b_f * 230)


# --- State ---
thetas = None     # Phase of each oscillator (N,)
omegas = None     # Natural frequency of each oscillator (N,)
positions = None  # (x, y) positions in sim space (N, 2)
velocities = None # Drift velocities (N, 2)
colors_rgb = None # (N, 3) RGB tuples based on omega
# Offscreen trail buffer: float32 (SIM_H, SIM_W, 3) for smooth accumulation
trail_buf = None
pimg = None       # Py5Image for blit


def update_kuramoto(K):
    """Vectorized Kuramoto update: d(theta_i)/dt = omega_i + K/N * sum_j sin(theta_j - theta_i)"""
    # diff[i,j] = theta_j - theta_i (correct Kuramoto coupling direction)
    diff = thetas[None, :] - thetas[:, None]   # shape (N, N)
    coupling_sum = np.sum(np.sin(diff), axis=1)  # sum over j for each i
    thetas[:] += (omegas + (K / N) * coupling_sum) * DT


def order_parameter():
    """Compute Kuramoto order parameter R (0=chaos, 1=sync) and mean phase psi."""
    sx = np.mean(np.cos(thetas))
    sy = np.mean(np.sin(thetas))
    R = np.sqrt(sx**2 + sy**2)
    psi = np.arctan2(sy, sx)
    return float(R), float(psi)


def setup():
    global thetas, omegas, positions, velocities, colors_rgb, trail_buf, pimg

    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 255, 255, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng(None)  # random seed each run

    # Initialize phases uniformly random
    thetas = rng.uniform(0, 2 * np.pi, N)
    # Natural frequencies: Gaussian (Lorentzian approximation)
    omegas = rng.normal(0.0, SIGMA_OMEGA, N)
    # Random positions across sim space
    positions = rng.uniform([20, 20], [SIM_W - 20, SIM_H - 20], (N, 2))
    # Random drift velocities
    angles = rng.uniform(0, 2 * np.pi, N)
    speeds = rng.uniform(0.1, DRIFT_SPEED, N)
    velocities = np.stack([np.cos(angles) * speeds, np.sin(angles) * speeds], axis=1)
    # Precompute colors
    colors_rgb = np.array([omega_to_rgb(o) for o in omegas], dtype=np.float32)

    # Trail buffer: dark background (obsidian)
    trail_buf = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    trail_buf[:, :, :] = np.array([2, 3, 8], dtype=np.float32)

    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)


def draw_firefly_on_trail(buf, x, y, r, g, b, phase, brightness):
    """Draw a soft glowing firefly blob on the float32 trail buffer."""
    rad = FIREFLY_RADIUS
    ix, iy = int(x), int(y)
    x0 = max(0, ix - rad - 1)
    x1 = min(SIM_W, ix + rad + 2)
    y0 = max(0, iy - rad - 1)
    y1 = min(SIM_H, iy + rad + 2)

    if x0 >= x1 or y0 >= y1:
        return

    ys_arr = np.arange(y0, y1)
    xs_arr = np.arange(x0, x1)
    yy, xx = np.meshgrid(ys_arr, xs_arr, indexing='ij')
    dist2 = (xx - x) ** 2 + (yy - y) ** 2
    falloff = np.exp(-dist2 / (rad * rad * 0.5)) * brightness

    # Flash modulation: bright when near phase 0 (mod 2pi)
    flash = max(0.0, math.cos(phase)) ** 3  # flashes at phase ~ 0

    # Add color contribution
    buf[y0:y1, x0:x1, 0] += falloff * r * flash
    buf[y0:y1, x0:x1, 1] += falloff * g * flash
    buf[y0:y1, x0:x1, 2] += falloff * b * flash


def draw():
    global trail_buf, velocities

    fc = py5.frame_count
    t = fc / TOTAL_FRAMES  # 0 → 1

    # K ramp: slow rise for dramatic phase transition around t=0.5
    K = K_START + (K_END - K_START) * t

    # --- Physics update ---
    update_kuramoto(K)
    R, psi = order_parameter()

    # Update positions (toroidal wrap)
    positions[:] += velocities
    positions[:, 0] %= SIM_W
    positions[:, 1] %= SIM_H

    # Slightly randomize drift direction occasionally
    if fc % 90 == 0:
        noise = np.random.normal(0, 0.05, velocities.shape)
        velocities += noise
        speeds = np.linalg.norm(velocities, axis=1, keepdims=True)
        speeds = np.clip(speeds, 0.05, DRIFT_SPEED)
        velocities = velocities / (np.linalg.norm(velocities, axis=1, keepdims=True) + 1e-8) * speeds

    # --- Trail decay (gives motion blur / persistence) ---
    trail_buf *= TRAIL_ALPHA
    trail_buf[:, :, 0] = np.maximum(trail_buf[:, :, 0], 2)
    trail_buf[:, :, 1] = np.maximum(trail_buf[:, :, 1], 3)
    trail_buf[:, :, 2] = np.maximum(trail_buf[:, :, 2], 8)

    # --- Draw fireflies ---
    for i in range(N):
        x, y = positions[i]
        r, g, b = colors_rgb[i]
        theta = float(thetas[i])
        # Brightness: healthy glow for all, extra flash at phase peak
        brightness = 0.3 + R * 0.7  # brighter when more synchronized
        draw_firefly_on_trail(trail_buf, x, y, r, g, b, theta, brightness)

    # --- Mean-field vector: draw synchrony arrow ---
    if R > 0.05:
        mx = SIM_W / 2 + R * SIM_W * 0.05 * math.cos(psi)
        my = SIM_H / 2 + R * SIM_H * 0.05 * math.sin(psi)
        # Draw thin line from center to mean phase indicator
        cx_s, cy_s = SIM_W // 2, SIM_H // 2
        steps = max(1, int(math.hypot(mx - cx_s, my - cy_s)))
        for s in range(steps):
            frac = s / max(1, steps)
            px = int(cx_s + frac * (mx - cx_s))
            py_v = int(cy_s + frac * (my - cy_s))
            if 0 <= px < SIM_W and 0 <= py_v < SIM_H:
                trail_buf[py_v, px, 0] += R * 200
                trail_buf[py_v, px, 1] += R * 180
                trail_buf[py_v, px, 2] += R * 20

    # --- Convert trail buffer to ARGB pixels ---
    # Clamp and convert to uint8
    buf_clamped = np.clip(trail_buf, 0, 255).astype(np.uint8)
    # Pack ARGB as signed int32
    argb = (
        (np.int32(255) << 24)
        | (buf_clamped[:, :, 0].astype(np.int32) << 16)
        | (buf_clamped[:, :, 1].astype(np.int32) << 8)
        | buf_clamped[:, :, 2].astype(np.int32)
    )
    # Reinterpret as signed int32
    argb_signed = argb.view(np.int32)

    pimg.load_pixels()
    pimg.pixels[:] = argb_signed.flatten()
    pimg.update_pixels()

    # --- Blit to 4K canvas ---
    py5.background(2, 3, 8)
    py5.image(pimg, 0, 0, py5.width, py5.height)

    # --- HUD overlay ---
    scale_x = py5.width / SIM_W
    ts = int(10 * scale_x)
    py5.no_stroke()

    # Dark panel
    panel_w = int(300 * scale_x)
    panel_h = int(100 * scale_x)
    py5.fill(0, 0, 8, 210)
    py5.rect(0, 0, panel_w, panel_h, 0, 0, 8, 0)

    # Title
    py5.fill(45, 220, 255)
    py5.text_size(ts)
    py5.text("KURAMOTO FIREFLY SYNC", int(10 * scale_x), int(18 * scale_x))

    # Stats
    py5.text_size(int(8 * scale_x))
    py5.fill(185, 180, 220)
    py5.text(f"K (coupling): {K:.3f} / {K_END:.1f}", int(10 * scale_x), int(38 * scale_x))
    py5.text(f"R (order):    {R:.3f}  {'SYNCED' if R > 0.7 else 'CHAOS' if R < 0.2 else 'PARTIAL'}", int(10 * scale_x), int(55 * scale_x))
    py5.text(f"Oscillators:  {N}", int(10 * scale_x), int(72 * scale_x))
    py5.text(f"ψ (mean phase): {math.degrees(psi):.1f}°", int(10 * scale_x), int(88 * scale_x))

    # R meter bar
    bar_x = int(10 * scale_x)
    bar_y = int(96 * scale_x)
    bar_w = int(280 * scale_x)
    bar_h = int(6 * scale_x)
    py5.fill(0, 0, 30)
    py5.rect(bar_x, bar_y, bar_w, bar_h, 3)
    # Color: red(chaos)→yellow(partial)→green(synced)
    r_hue = int(120 * R)  # 0=red, 120=green
    py5.fill(r_hue, 240, 220)
    py5.rect(bar_x, bar_y, int(bar_w * R), bar_h, 3)

    # Progress bar
    py5.fill(0, 0, 20)
    py5.rect(0, py5.height - int(5 * scale_x), py5.width, int(5 * scale_x))
    py5.fill(45, 200, 200)
    py5.rect(0, py5.height - int(5 * scale_x), int(py5.width * t), int(5 * scale_x))

    # Watermark
    py5.fill(185, 60, 140, 100)
    py5.text_size(int(7 * scale_x))
    py5.text(WORK_NAME, int(10 * scale_x), py5.height - int(10 * scale_x))

    # Fail-safe
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen on frame {fc}. Aborting.")
            import os
            os._exit(1)

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | K={K:.2f} R={R:.3f}")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames removed.")

        import os
        os._exit(0)


py5.run_sketch()

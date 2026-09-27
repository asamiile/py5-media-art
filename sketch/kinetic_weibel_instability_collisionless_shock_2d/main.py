"""
Kinetic Weibel Instability & Collisionless Shock Wave 2D
Generative media art depicting the spontaneous generation of intense magnetic
filaments in relativistic counter-streaming collisionless plasmas via the
Weibel electromagnetic instability, culminating in a turbulent collisionless
shock front with Fermi particle acceleration.

Features:
- Counter-streaming relativistic plasma beam interaction (v_rel ~ c)
- Multi-mode transverse Weibel magnetic field B_z(x, y) with skin-depth scaling (k ~ omega_pe/c)
- Pinched longitudinal current filaments J_x = c/(4pi) * (dB_z/dy)
- Kink undulation and magnetic filament coalescence toward the shock center
- Downstream post-shock magnetic turbulence core (|x| < 2.0)
- Multi-layer shock front ripples and separatrix boundaries
- Dual-light Blinn-Phong specular normal mapping with metallic plasma sheen
- 4,000 relativistic charged particles (Bennett-pinched trajectories and Fermi acceleration sparks)
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_weibel_instability_collisionless_shock_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 900
FPS = 60
SIZE = (1920, 1080)

# High-resolution computational domain
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)


def compute_weibel_mhd(t_norm):
    """
    Computes the 2D relativistic Weibel electromagnetic instability and shock field.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Counter-streaming relativistic beam envelopes
    beam_left = 0.5 * (1.0 - np.tanh(x / 2.6))
    beam_right = 0.5 * (1.0 + np.tanh(x / 2.6))

    # 2. Weibel Current Filaments J_x(x, y)
    k_skin = 3.6
    kink_y = 0.25 * np.sin(1.2 * x - tau * 1.8) * np.exp(-x**2 / 24.0)
    y_eff = y + kink_y

    bz_field = np.zeros_like(x)
    for m in [1, 2, 3, 5]:
        km = m * (k_skin / 2.0)
        amp = 0.45 / (m**0.7)
        bz_field += amp * np.sin(km * y_eff + 0.3 * np.sin(1.5 * x))

    # Shock compression envelope at x ~ 0: magnetic energy is amplified 4x at the shock front
    shock_compression = 1.0 + 3.2 * np.exp(-x**2 / (2.0 * 1.8**2))
    bz_total = bz_field * shock_compression

    # Current density J_x ~ dB_z / dy
    dbz_dy = (np.roll(bz_total, -1, axis=0) - np.roll(bz_total, 1, axis=0)) * 0.5
    current_filaments = np.power(np.clip(np.abs(dbz_dy) / 1.5, 0.0, 1.0), 1.6)

    # 3. Downstream Post-Shock Magnetic Turbulence Core (|x| < 2.0)
    turb_vortices = (
        0.40 * np.sin(3.5 * x + 3.2 * y - tau * 3.5)
        + 0.30 * np.cos(4.8 * x - 3.7 * y + tau * 4.2)
        + 0.22 * np.sin(6.2 * x + 5.5 * y - tau * 5.0)
    ) * np.exp(-x**2 / 4.8)
    turb_energy = np.power(np.clip(np.abs(turb_vortices) * 1.6, 0.0, 1.0), 1.4)

    # 4. Filamentary Magnetic Channels
    channel_ribbons = np.power(np.clip(np.cos(bz_total * 3.8) * 0.5 + 0.5, 0.0, 1.0), 10.0) * np.exp(-x**2 / 30.0)

    # 5. Surface Normal & Lighting
    h_field = (
        0.45 * current_filaments
        + 0.38 * turb_energy
        + 0.25 * np.abs(bz_total) / 2.8
        + 0.20 * channel_ribbons
    )
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(np.clip((dot1 - 0.52) / 0.48, 0.0, 1.0), 7.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(np.clip((dot2 - 0.50) / 0.50, 0.0, 1.0), 5.0)

    norm_fil = np.clip(current_filaments * 1.6, 0.0, 1.0)
    norm_turb = np.clip(turb_energy * 1.8, 0.0, 1.0)
    norm_rib = np.clip(channel_ribbons * 1.4, 0.0, 1.0)

    bz_pos = np.clip(bz_total / 2.2, 0.0, 1.0)
    bz_neg = np.clip(-bz_total / 2.2, 0.0, 1.0)

    bg_left = beam_left * 0.22
    bg_right = beam_right * 0.22

    red = (
        2.0
        + 12.0 * bg_left
        + 240.0 * bg_right
        + 255.0 * norm_fil
        + 250.0 * norm_turb
        + 220.0 * bz_neg
        + 15.0 * bz_pos
        + 200.0 * norm_rib
        + spec1 * 255.0
        + spec2 * 190.0 * 0.8
    )
    green = (
        3.0
        + 190.0 * bg_left
        + 25.0 * bg_right
        + 180.0 * norm_fil
        + 230.0 * norm_turb
        + 25.0 * bz_neg
        + 225.0 * bz_pos
        + 160.0 * norm_rib
        + spec1 * 255.0 * 0.95
        + spec2 * 140.0 * 0.5
    )
    blue = (
        16.0
        + 245.0 * bg_left
        + 110.0 * bg_right
        + 25.0 * norm_fil
        + 255.0 * norm_turb
        + 190.0 * bz_neg
        + 245.0 * bz_pos
        + 235.0 * norm_rib
        + spec1 * 255.0
        + spec2 * 40.0 * 0.2
    )

    vig = np.clip(1.0 - (np.abs(x) / 9.4)**8.0, 0.0, 1.0) * np.clip(1.0 - (np.abs(y) / 5.25)**8.0, 0.0, 1.0)
    red = np.clip(red * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


def to_screen(x, y):
    """Maps physical coordinates to screen pixels."""
    sx = (x + 9.6) / 19.2 * SIZE[0]
    sy = (5.4 - y) / 10.8 * SIZE[1]
    return sx, sy


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = (frame - 1) / TOTAL_FRAMES
    tau = 2.0 * np.pi * t_norm

    # 1. Background Weibel Electromagnetic Fluid
    bg_rgb = compute_weibel_mhd(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Weibel Current Filament Spines (Golden high-current conduits)
    for fila in range(-7, 8):
        py5.no_fill()
        py5.stroke(255, 215, 60, 150)
        py5.stroke_weight(2.0)
        py5.begin_shape()
        y_base = fila * 0.72
        for x_step in np.linspace(-9.2, 9.2, 120):
            kink = 0.24 * np.sin(1.1 * x_step - tau * 1.8 + fila * 0.5) * np.exp(-x_step**2 / 20.0)
            sx, sy = to_screen(x_step, y_base + kink)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 3. Multi-layer Shock Front Ripples
    for layer in range(3):
        w_offset = 1.3 + layer * 0.35
        for sign_x in [-1, 1]:
            py5.no_fill()
            alpha = 140 - layer * 35
            py5.stroke(255, 255, 255, alpha)
            py5.stroke_weight(1.5)
            py5.begin_shape()
            for y_step in np.linspace(-5.2, 5.2, 100):
                x_shock = sign_x * (w_offset + 0.18 * np.sin(2.4 * y_step + tau * 2.8 + layer))
                sx, sy = to_screen(x_shock, y_step)
                py5.vertex(sx, sy)
            py5.end_shape()

    # 4. 4,000 Relativistic Particles: Counter-streaming & Fermi Shock Acceleration
    for p in range(4000):
        seed = p * 0.61803398875
        phase = seed * 100.0
        t_part = (t_norm * 3.2 + phase) % 1.0

        dir_beam = 1.0 if (p % 2 == 0) else -1.0
        init_x = -9.2 * dir_beam + dir_beam * t_part * 18.4
        fila_idx = (p % 15) - 7
        base_y = fila_idx * 0.72 + ((p * 7) % 50 - 25) / 120.0

        in_shock = np.exp(-init_x**2 / 5.5)
        y_wiggle = 0.16 * np.sin(init_x * 2.4 + tau * 2.5 + p) * (1.0 + 3.2 * in_shock)
        cur_y = base_y + y_wiggle
        cur_x = init_x

        sx, sy = to_screen(cur_x, cur_y)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if in_shock > 0.50 and p % 4 == 0:
                py5.stroke(255, 255, 255, 255)
                py5.stroke_weight(2.6)
            elif dir_beam > 0:
                py5.stroke(0, 240, 255, 190)
                py5.stroke_weight(1.5)
            else:
                py5.stroke(255, 50, 110, 190)
                py5.stroke_weight(1.5)
            py5.point(sx, sy)

    # Save frame image
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Weibel shock preview captured: {PREVIEW_FILE}")

    if frame % 60 == 0:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")


def finish_render():
    print("[Rendering Complete] Encoding master MP4 via ffmpeg...")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        OUTPUT_VIDEO
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[Video Compiled] Master MP4 saved: {OUTPUT_VIDEO}")
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
    else:
        print(f"[Video Encoding Failed] ffmpeg error:\n{res.stderr}")

    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

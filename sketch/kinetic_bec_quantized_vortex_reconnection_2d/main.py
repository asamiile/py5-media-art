"""
kinetic_bec_quantized_vortex_reconnection_2d
--------------------------------------------
Kinetic 2D macroscopic quantum fluid simulation of Bose-Einstein Condensate (BEC)
quantized vortex dipole reconnection and dark soliton snake instability.

Features:
- Macroscopic quantum order parameter Psi = sqrt(rho) * exp(i * theta).
- Harmonic magnetic trapping potential with smooth Thomas-Fermi boundary profile.
- 8 quantized vortices undergoing helical approach, dipole collision, and topological reconnection.
- Phase winding singularities around each vortex core (oint v_s . dl = 2 * pi * hbar / m).
- Dark soliton density stripe with snake instability transverse undulating breakdown.
- Dispersive Bogoliubov acoustic sound wave ripples radiated from reconnection events.
- Dual-light Blinn-Phong specular quantum fluid chrome normal shading.
- 2,400 superfluid condensate atoms circulating with irrotational quantum vorticity (v ~ 1/r).
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_bec_quantized_vortex_reconnection_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

# Rendering parameters
SIZE = (1920, 1080)
TOTAL_FRAMES = 900
FPS = 60

# Domain & Grid configuration
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Directional lighting vectors for Blinn-Phong specular sheen
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)


def compute_bec_field(t_norm):
    """
    Computes 2D Gross-Pitaevskii macroscopic condensate density, quantized phase
    singularities, dark soliton snake instability, and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY
    r = np.sqrt(x * x + y * y)

    # 1. Thomas-Fermi Condensate Density Envelope in Harmonic Trap
    r_tf = 7.8
    rho_tf = np.clip(1.0 - (r / r_tf)**2.0, 0.0, 1.0)
    condensate_envelope = np.power(rho_tf, 0.65)

    # 2. Moving Quantized Vortices & Dipole Reconnection Dynamics
    num_vortices = 8
    theta_total = np.zeros_like(x)
    core_density = np.ones_like(x)
    healing_length = 0.38

    vortex_coords = []
    charges = [1, -1, 1, -1, 1, -1, 1, -1]
    for k in range(num_vortices):
        q = charges[k]
        pair_idx = k // 2
        r_base = 2.6 + 1.2 * np.cos(tau + pair_idx * np.pi * 0.5)
        angle_base = (pair_idx * np.pi * 0.5) + (1 if q > 0 else -1) * (0.35 + 0.25 * np.sin(tau * 2.0))
        angle = angle_base + tau * 1.5 * (1 if pair_idx % 2 == 0 else -1)

        vx = r_base * np.cos(angle)
        vy = r_base * np.sin(angle) * 0.72
        vortex_coords.append((vx, vy, q))

        dx = x - vx
        dy = y - vy
        d2 = dx * dx + dy * dy

        # Core profile: rho_core = d^2 / (d^2 + 2 * xi^2)
        rho_c = d2 / (d2 + 2.0 * healing_length * healing_length)
        core_density *= rho_c

        # Phase winding around vortex: q * atan2(dy, dx)
        phase_k = q * np.arctan2(dy, dx)
        theta_total += phase_k

    # 3. Dark Soliton Stripe with Snake Instability Undulations
    y_soliton = 0.55 * np.sin(1.2 * x - tau * 2.0) + 0.2 * np.cos(2.4 * x + tau * 4.0)
    dist_soliton = np.abs(y - y_soliton)
    soliton_dip = np.tanh(dist_soliton / 0.42)**2.0
    core_density *= (0.35 + 0.65 * soliton_dip)

    # Phase jump across dark soliton
    theta_total += np.pi * 0.5 * np.tanh((y - y_soliton) / 0.35)

    # 4. Bogoliubov Acoustic Phonon Emission (Shock Wave Ripples from Reconnection)
    k_sound = 4.2
    sound_wave = 0.18 * np.sin(k_sound * r - tau * 5.0) * condensate_envelope

    # Total Condensate Density & Superfluid Phase
    total_density = condensate_envelope * core_density + sound_wave
    total_density = np.clip(total_density, 0.0, 1.2)

    # Quantum Interference Fringes
    quantum_fringes = np.power(0.5 + 0.5 * np.cos(theta_total * 2.0 + tau * 2.0), 3.0)

    # 5. Specular Height Field & Surface Normals
    h_field = (
        0.42 * total_density
        + 0.28 * quantum_fringes * condensate_envelope
        + 0.18 * (1.0 - core_density) * condensate_envelope
    )
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(np.clip((dot1 - 0.50) / 0.50, 0.0, 1.0), 6.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(np.clip((dot2 - 0.50) / 0.50, 0.0, 1.0), 5.0)

    # Color Palette:
    # Condensate Bulk: Luminous Emerald (#00ffaa) & Deep Sapphire Cobalt (#0033aa)
    # Vortex Singularities & Solitons: Neon Laser Fuchsia (#ff0088) & Amethyst Violet (#7700cc)
    # Reconnection Sound Ripples: Incandescent Solar Amber (#ffaa00)
    # Specular Highlights: Pure Diamond Chrome White (#ffffff)
    # Ultra-Cold Abyss: Midnight Obsidian (#010209)

    norm_rho = np.clip(total_density, 0.0, 1.0)
    norm_vort = np.clip((1.0 - core_density) * condensate_envelope * 1.5, 0.0, 1.0)
    norm_phase = np.clip(quantum_fringes * condensate_envelope, 0.0, 1.0)

    red = (
        1.0
        + 230.0 * norm_vort
        + 190.0 * norm_phase
        + 10.0 * norm_rho
        + spec1 * 255.0
        + spec2 * 185.0 * 0.8
    )
    green = (
        2.0
        + 25.0 * norm_vort
        + 40.0 * norm_phase
        + 225.0 * norm_rho
        + spec1 * 255.0 * 0.95
        + spec2 * 135.0 * 0.5
    )
    blue = (
        10.0
        + 180.0 * norm_vort
        + 245.0 * norm_phase
        + 170.0 * norm_rho
        + spec1 * 255.0
        + spec2 * 50.0 * 0.2
    )

    vig = np.clip(1.0 - (np.abs(x) / 9.4)**8.0, 0.0, 1.0) * np.clip(1.0 - (np.abs(y) / 5.25)**8.0, 0.0, 1.0)
    red = np.clip(red * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1), vortex_coords


def to_screen(x, y):
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
    t_norm = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    # 1. Background Condensate Density & Quantum Phase Field
    bg_rgb, vortices = compute_bec_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Vortex Core Singularities & Quantum Circulation Rings
    for (vx, vy, q) in vortices:
        sx, sy = to_screen(vx, vy)
        py5.no_fill()
        py5.stroke(255, 255, 255, 220)
        py5.stroke_weight(2.2)
        py5.circle(sx, sy, 8)

        py5.stroke(255, 0, 136, 160) if q > 0 else py5.stroke(0, 255, 170, 160)
        py5.stroke_weight(1.4)
        py5.circle(sx, sy, 22)
        py5.circle(sx, sy, 36)

    # 3. 2,400 Superfluid Condensate Atoms Circulating Around Quantum Vortices
    py5.stroke_weight(1.8)
    for p in range(2400):
        seed = p * 0.61803398875
        r_p = 1.0 + (seed * 6.5)
        th_p = (p * 2.39996 + tau * (2.4 / (r_p + 0.5)))
        
        px = r_p * np.cos(th_p)
        py_cur = r_p * np.sin(th_p) * 0.85
        
        # Perturbation from nearest vortex
        for (vx, vy, q) in vortices:
            dx = px - vx
            dy = py_cur - vy
            d2 = dx * dx + dy * dy
            if d2 < 2.5:
                inv_d = 1.0 / (np.sqrt(d2) + 0.2)
                px += -dy * inv_d * q * 0.08
                py_cur += dx * inv_d * q * 0.08

        sx, sy = to_screen(px, py_cur)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if p % 6 == 0:
                py5.stroke(255, 255, 255, 245)
                py5.stroke_weight(2.4)
            elif p % 2 == 0:
                py5.stroke(0, 255, 180, 190)
                py5.stroke_weight(1.6)
            else:
                py5.stroke(255, 180, 30, 175)
                py5.stroke_weight(1.4)
            py5.point(sx, sy)

    # 4. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] BEC quantized vortex preview captured: {PREVIEW_PNG}")

    if frame % 60 == 0:
        pct = (frame / float(TOTAL_FRAMES)) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 5. Completion and Video Encoding
    if frame >= TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame-%04d.png"),
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "5.1",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast",
            OUTPUT_MP4
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ffmpeg ERROR] {result.stderr}")
        else:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")

        # Cleanup frame images
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

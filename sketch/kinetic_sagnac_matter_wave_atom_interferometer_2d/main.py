"""
Kinetic Sagnac Matter-Wave Atom Interferometer 2D
Generative media art depicting coherent matter-wave de Broglie wavepacket
splitting, redirection, and recombination in a Mach-Zehnder cold-atom
interferometer, sensing rotation via the quantum Sagnac effect
(Delta Phi = (4*m/hbar) * Omega . A).

Features:
- Diamond Mach-Zehnder matter-wave arm trajectories with de Broglie wave carrier
- Optical Bragg laser standing wave lattices (pi/2 splitter, pi mirror, pi/2 recombiner)
- Quantum phase winding arg(Psi) mapped across an iridescent quantum color wheel
- Sagnac rotation phase accumulation and spatial output interference fringes
- Dual-light Blinn-Phong specular normal mapping for cryogenic vacuum chamber optics
- 3,600 laser-cooled Rubidium-87 atoms tracing ballistic matter-wave geodesics
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_sagnac_matter_wave_atom_interferometer_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 900
FPS = 60
SIZE = (1920, 1080)

# Computational domain
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)


def compute_interferometer_field(t_norm):
    """
    Computes the 2D matter-wave wavefunction and Bragg laser standing wave field.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Mach-Zehnder Matter-Wave Arm Coordinates
    packet_x = ((t_norm * 1.5) % 1.0) * 15.0 - 7.5
    
    diamond_h = 2.6
    arm1_y = diamond_h * (1.0 - np.clip(np.abs(x) / 5.2, 0.0, 1.0))
    arm2_y = -diamond_h * (1.0 - np.clip(np.abs(x) / 5.2, 0.0, 1.0))

    # Sagnac rotation phase accumulation
    sagnac_phase = 2.5 * np.sin(tau)

    # 2. Continuous Matter-Wave Beams & Probability Density
    sigma_arm = 0.55
    arm1_guide = np.exp(-((y - arm1_y)**2) / (2.0 * sigma_arm**2)) * np.clip(1.0 - (np.abs(x) / 6.2)**6.0, 0.0, 1.0)
    arm2_guide = np.exp(-((y - arm2_y)**2) / (2.0 * sigma_arm**2)) * np.clip(1.0 - (np.abs(x) / 6.2)**6.0, 0.0, 1.0)

    # Coherent matter-wave interference carrier
    k_matter = 7.5
    psi1_phase = k_matter * x - arm1_y * 3.0 - tau * 4.0
    psi2_phase = k_matter * x + arm2_y * 3.0 - tau * 4.0 + sagnac_phase

    psi1 = arm1_guide * np.exp(1j * psi1_phase)
    psi2 = arm2_guide * np.exp(1j * psi2_phase)

    # Wavepacket propagation envelopes
    packet_w = 1.6
    packet_env1 = np.exp(-((x - packet_x)**2 + (y - arm1_y)**2) / (2.0 * packet_w**2))
    packet_env2 = np.exp(-((x - packet_x)**2 + (y - arm2_y)**2) / (2.0 * packet_w**2))

    psi_total = (psi1 + 1.2 * packet_env1 * np.exp(1j * psi1_phase)) + (psi2 + 1.2 * packet_env2 * np.exp(1j * psi2_phase))
    prob_density = np.abs(psi_total)**2
    prob_norm = np.clip(prob_density / 2.2, 0.0, 1.0)

    # Quantum phase angle [-pi..pi]
    quantum_phase = np.angle(psi_total)

    # 3. Optical Bragg Laser Standing Wave Beams (Pulse stations at x = -5.2, 0.0, +5.2)
    k_laser = 14.0
    laser_standing = np.cos(k_laser * y)**2
    
    bragg_beams = np.zeros_like(x)
    for bx in [-5.2, 0.0, 5.2]:
        beam_profile = np.exp(-((x - bx)**2) / (2.0 * 0.28**2)) * np.exp(-(y**2) / (2.0 * 4.2**2))
        pulse_glow = 0.7 + 0.3 * np.cos(tau * 3.0 + bx)
        bragg_beams += beam_profile * (0.4 + 0.6 * laser_standing) * pulse_glow

    # 4. Recombination Interference Fringes at Output Port (x > 5.2)
    recomb_region = np.clip((x - 5.2) / 2.5, 0.0, 1.0)
    fringe_carrier = np.cos(5.0 * y + sagnac_phase) * 0.5 + 0.5
    fringe_intensity = recomb_region * fringe_carrier * np.exp(-(y**2) / 4.0)

    # 5. Normal Mapping Shading
    h_field = (
        0.45 * prob_norm
        + 0.35 * bragg_beams
        + 0.25 * fringe_intensity
        + 0.15 * (arm1_guide + arm2_guide)
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

    # Color Palette:
    # Bragg Laser Beams: Fluorescent Laser Emerald (#00ff77) & Electric Mint (#20ffa5)
    # Matter-Wave Cores: Electric Glacial Cyan (#00e5ff) & Sapphire Blue (#0033aa)
    # Quantum Phase Interference: Neon Laser Magenta (#ff0088) & Royal Amethyst (#7700ff)
    # Sagnac Output Fringes: Incandescent Solar Gold (#ffea00)
    # Specular Chamber Optics: Liquid Diamond White (#ffffff)
    # Cryogenic Vacuum Void: Midnight Obsidian (#010208)

    phase_col_r = np.clip(np.cos(quantum_phase) * 0.5 + 0.5, 0.0, 1.0)
    phase_col_g = np.clip(np.cos(quantum_phase - 2.094) * 0.5 + 0.5, 0.0, 1.0)
    phase_col_b = np.clip(np.cos(quantum_phase + 2.094) * 0.5 + 0.5, 0.0, 1.0)

    norm_prob = np.clip(prob_norm * 1.6, 0.0, 1.0)
    norm_bragg = np.clip(bragg_beams * 1.8, 0.0, 1.0)
    norm_fringe = np.clip(fringe_intensity * 1.8, 0.0, 1.0)

    red = (
        2.0
        + 190.0 * norm_prob * phase_col_r
        + 25.0 * norm_bragg
        + 255.0 * norm_fringe
        + spec1 * 255.0
        + spec2 * 180.0 * 0.8
    )
    green = (
        4.0
        + 160.0 * norm_prob * phase_col_g
        + 255.0 * norm_bragg
        + 210.0 * norm_fringe
        + spec1 * 255.0 * 0.95
        + spec2 * 140.0 * 0.5
    )
    blue = (
        16.0
        + 245.0 * norm_prob * phase_col_b
        + 130.0 * norm_bragg
        + 30.0 * norm_fringe
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

    # 1. Background Matter-Wave Quantum Field & Bragg Lattices
    bg_rgb = compute_interferometer_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Optical Bragg Pulse Station Vertical Guides
    for bx in [-5.2, 0.0, 5.2]:
        py5.stroke(0, 255, 140, 150)
        py5.stroke_weight(2.0)
        sx, sy1 = to_screen(bx, -4.5)
        _, sy2 = to_screen(bx, 4.5)
        py5.line(sx, sy1, sx, sy2)

    # 3. Interferometer Geodesic Trajectory Rails
    diamond_h = 2.6
    for sign_arm in [-1.0, 1.0]:
        py5.no_fill()
        py5.stroke(0, 220, 255, 170)
        py5.stroke_weight(1.8)
        py5.begin_shape()
        for x_step in np.linspace(-6.0, 6.0, 120):
            y_arm = sign_arm * diamond_h * (1.0 - np.clip(np.abs(x_step) / 5.2, 0.0, 1.0))
            sx, sy = to_screen(x_step, y_arm)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 4. 3,600 Laser-Cooled Atoms traversing interferometer
    for p in range(3600):
        seed = p * 0.61803398875
        phase = seed * 100.0
        t_atom = (t_norm * 2.2 + phase) % 1.0

        x_atom = -7.5 + t_atom * 15.0
        arm_choice = 1.0 if (p % 2 == 0) else -1.0

        if x_atom < -5.2:
            # Entering common guide
            y_atom = ((p % 30) - 15) / 50.0
        elif x_atom < 5.2:
            # In split interferometer arms
            y_ideal = arm_choice * diamond_h * (1.0 - np.clip(np.abs(x_atom) / 5.2, 0.0, 1.0))
            y_dispersion = (((p * 13) % 40) - 20) / 70.0
            y_atom = y_ideal + y_dispersion
        else:
            # Exiting through recombined port with Sagnac fringe modulation
            sagnac_shift = np.sin(tau)
            port_bias = 0.8 * sagnac_shift * arm_choice
            y_atom = port_bias + (((p * 7) % 30) - 15) / 50.0

        sx, sy = to_screen(x_atom, y_atom)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if p % 8 == 0:
                py5.stroke(255, 255, 255, 255)
                py5.stroke_weight(2.5)
            elif p % 2 == 0:
                py5.stroke(0, 255, 140, 200) # Emerald
                py5.stroke_weight(1.6)
            else:
                py5.stroke(0, 230, 255, 190) # Cyan
                py5.stroke_weight(1.5)
            py5.point(sx, sy)

    # Save frame image
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Atom interferometer preview captured: {PREVIEW_FILE}")

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

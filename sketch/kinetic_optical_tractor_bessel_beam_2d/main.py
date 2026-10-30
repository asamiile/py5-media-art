"""
Kinetic Optical Tractor Bessel Beam 2D (Revised)
Generative media art depicting structured singular optics, non-diffracting
high-order Bessel-vortex beams, negative radiation pressure, and retrograde
optical tractor pulling dynamics.

Features:
- Analytical high-order Bessel-vortex beam intensity profile J_2(k_r r)^2 with orbital angular momentum
- Dynamic helical phase wave caustics propagating forward along the optical axis
- Negative optical radiation pressure pulling trapped particles backward toward the light source
- Transverse optical gradient force trapping particles onto concentric Bessel diffraction rings
- Elimination of wrap-around trail artifacts with segmented trail validation and buffer resets
- Dual-light Blinn-Phong specular relief normal mapping on optical wave caustics
- Fast vectorized multi-trail Lagrangian particle kinematics using py5.lines() and py5.points()
- 2,400 particles: retrograde pulled matter sparks (Gold) vs forward photon wavepackets (Mint)
- 720 frames @ 60 FPS (12 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import scipy.special as sp
import py5

WORK_NAME = "kinetic_optical_tractor_bessel_beam_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
WORK_VIDEO = os.path.join(SKETCH_DIR, f"{WORK_NAME}.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 720
FPS = 60
SIZE = (1920, 1080)

# Computational Grid for field synthesis
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-6.4, 6.4, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-3.6, 3.6, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)  # Cool emerald cyan
LIGHT2_DIR = np.array([0.577, 0.577, 0.577], dtype=np.float32)    # Warm solar topaz

# Optical constants
APERTURE_X = -5.0
TOPOLOGICAL_CHARGE = 2
KR = 3.8  # Radial wavevector for Bessel rings
KZ = 3.6  # Axial wavevector

# Particle system: 2,400 particles with multi-segment history trails
NUM_PARTICLES = 2400
TRAIL_LEN = 6

P_X = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_Y = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_TYPE = np.zeros(NUM_PARTICLES, dtype=np.int32)     # 0: Pulled Matter (Gold), 1: Forward Photon (Mint)
P_RADIUS = np.zeros(NUM_PARTICLES, dtype=np.float32) # Preferred Bessel ring radius
P_THETA = np.zeros(NUM_PARTICLES, dtype=np.float32)  # Azimuthal angle
P_AGE = np.zeros(NUM_PARTICLES, dtype=np.float32)

TRAIL_X = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)
TRAIL_Y = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)


def init_particles():
    global P_X, P_Y, P_TYPE, P_RADIUS, P_THETA, P_AGE, TRAIL_X, TRAIL_Y
    np.random.seed(99)

    # Ring radii corresponding to Bessel J_2 peaks: ~0.8, 1.6, 2.4, 3.2
    ring_radii = np.array([0.82, 1.65, 2.45, 3.25], dtype=np.float32)

    # 1,700 retrograde pulled matter particles (Type 0)
    n_pulled = 1700
    P_X[:n_pulled] = np.random.uniform(-4.5, 6.2, size=n_pulled).astype(np.float32)
    chosen_r = np.random.choice(ring_radii, size=n_pulled) + np.random.normal(0, 0.08, size=n_pulled)
    P_RADIUS[:n_pulled] = np.abs(chosen_r).astype(np.float32)
    P_THETA[:n_pulled] = np.random.uniform(0.0, 2.0 * np.pi, size=n_pulled).astype(np.float32)
    P_Y[:n_pulled] = P_RADIUS[:n_pulled] * np.sin(P_THETA[:n_pulled])
    P_TYPE[:n_pulled] = 0
    P_AGE[:n_pulled] = np.random.uniform(0.0, 100.0, size=n_pulled).astype(np.float32)

    # 700 forward photon wavepacket sparks (Type 1)
    n_forward = NUM_PARTICLES - n_pulled
    P_X[n_pulled:] = np.random.uniform(-4.8, 6.0, size=n_forward).astype(np.float32)
    P_Y[n_pulled:] = np.random.uniform(-3.2, 3.2, size=n_forward).astype(np.float32)
    P_TYPE[n_pulled:] = 1
    P_AGE[n_pulled:] = np.random.uniform(0.0, 100.0, size=n_forward).astype(np.float32)

    for k in range(TRAIL_LEN):
        TRAIL_X[:, k] = P_X
        TRAIL_Y[:, k] = P_Y


init_particles()


def compute_bessel_tractor_field(t_norm):
    """
    Computes analytical Bessel-vortex beam intensity J_m(k_r r)^2,
    helical phase wave caustics, launch aperture core glow,
    and dual-light specular wavefront normal mapping.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # Distance along beam axis from aperture
    z_dist = np.clip(x - APERTURE_X, 0.05, 12.0)
    r_perp = np.abs(y)

    # 1. High-order Bessel beam radial profile J_2(k_r * r_perp)
    u_arg = KR * r_perp
    j2_val = sp.jv(TOPOLOGICAL_CHARGE, u_arg).astype(np.float32)
    bessel_intensity = (j2_val ** 2)

    # Beam envelope: conical expansion and gentle axial decay
    beam_envelope = np.exp(-0.5 * (r_perp / (1.1 + 0.22 * z_dist))**2) / (1.0 + 0.04 * z_dist)
    beam_field = bessel_intensity * beam_envelope

    # 2. Helical Phase Carrier & Forward Caustic Modulation
    theta_coord = np.arctan2(y, z_dist)
    helical_phase = TOPOLOGICAL_CHARGE * theta_coord + KZ * z_dist - tau * 3.0
    phase_waves = np.cos(helical_phase)

    # Luminous caustic modulation
    caustic_glow = beam_field * (1.1 + 0.6 * phase_waves)

    # 3. Launch Aperture Core Glow
    r_aperture = np.sqrt((x - APERTURE_X)**2 + y**2)
    aperture_glow = np.exp(-0.5 * (r_aperture / 0.52)**2)

    # 4. Wavefront Topography and Specular Normal Relief
    topo = caustic_glow * 2.2 + aperture_glow * 3.0
    gy, gx = np.gradient(topo)
    nx = -gx * 5.0
    ny = -gy * 5.0
    nz = np.ones_like(nx)
    norm_len = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = dot1 ** 16.0

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = dot2 ** 22.0

    # 5. Color Synthesis
    # Base vacuum void: Deep indigo obsidian
    r_bg, g_bg, b_bg = 6.0, 9.0, 16.0

    # Bessel Beam intensity: Radiant Laser Emerald & Electric Mint
    intensity_norm = np.clip(caustic_glow * 3.2, 0.0, 1.0)
    wave_accent = np.clip(phase_waves * 0.5 + 0.5, 0.0, 1.0) * intensity_norm

    r_beam = 12.0 * intensity_norm + wave_accent * 55.0
    g_beam = 90.0 * intensity_norm + wave_accent * 140.0
    b_beam = 110.0 * intensity_norm + wave_accent * 150.0

    # Combined radiance
    r_out = r_bg + r_beam + aperture_glow * 255.0 + spec2 * 255.0 + spec1 * 50.0
    g_out = g_bg + g_beam + aperture_glow * 252.0 + spec2 * 230.0 + spec1 * 240.0
    b_out = b_bg + b_beam + aperture_glow * 245.0 + spec2 * 140.0 + spec1 * 255.0

    rgb = np.stack([
        np.clip(r_out, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_out, 0, 255).astype(np.uint8)
    ], axis=-1)

    return rgb


def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized revised setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count

    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = ((frame - 1) % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    field_rgb = compute_bessel_tractor_field(t_norm)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Update particles and history trails
    global P_X, P_Y, P_TYPE, P_RADIUS, P_THETA, P_AGE, TRAIL_X, TRAIL_Y
    P_AGE += 1.0

    # Shift trail positions
    TRAIL_X[:, 1:] = TRAIL_X[:, :-1]
    TRAIL_X[:, 0] = P_X
    TRAIL_Y[:, 1:] = TRAIL_Y[:, :-1]
    TRAIL_Y[:, 0] = P_Y

    is_pulled = (P_TYPE == 0)
    is_forward = (P_TYPE == 1)

    # Type 0: Retrograde Optical Pulling Force with 3D Helical Corkscrew
    P_THETA[is_pulled] += 0.055 / (P_RADIUS[is_pulled] + 0.25)
    target_y = P_RADIUS[is_pulled] * np.sin(P_THETA[is_pulled])
    pull_speed = 0.042 * (0.85 + 0.35 * np.cos(P_THETA[is_pulled]))

    P_X[is_pulled] -= pull_speed
    P_Y[is_pulled] += (target_y - P_Y[is_pulled]) * 0.16

    # Recycle pulled particles when they reach the aperture
    reached_core = is_pulled & (P_X < APERTURE_X + 0.2)
    if np.any(reached_core):
        new_x = np.random.uniform(5.5, 6.3, size=np.sum(reached_core))
        new_r = np.random.choice([0.82, 1.65, 2.45, 3.25], size=np.sum(reached_core)) + np.random.normal(0, 0.06, size=np.sum(reached_core))
        new_theta = np.random.uniform(0.0, 2.0 * np.pi, size=np.sum(reached_core))
        new_y = new_r * np.sin(new_theta)

        P_X[reached_core] = new_x
        P_RADIUS[reached_core] = np.abs(new_r).astype(np.float32)
        P_THETA[reached_core] = new_theta
        P_Y[reached_core] = new_y

        # Reset history trail buffer to eliminate wrap-around lines
        TRAIL_X[reached_core, :] = new_x[:, None]
        TRAIL_Y[reached_core, :] = new_y[:, None]

    # Type 1: Forward Light Pulses
    fwd_speed = 0.078
    P_X[is_forward] += fwd_speed
    P_Y[is_forward] += np.sin(P_X[is_forward] * 2.2 + tau * 3.0) * 0.009

    # Wrap forward photons
    wrap_fwd = is_forward & (P_X > 6.35)
    if np.any(wrap_fwd):
        new_fx = APERTURE_X + 0.35
        new_fy = np.random.uniform(-3.0, 3.0, size=np.sum(wrap_fwd))
        P_X[wrap_fwd] = new_fx
        P_Y[wrap_fwd] = new_fy
        TRAIL_X[wrap_fwd, :] = new_fx
        TRAIL_Y[wrap_fwd, :] = new_fy[:, None]

    # Fast Vectorized Drawing via py5.lines() and py5.points()
    # 1. Ribbon Trails (with distance thresholding to guarantee zero wrap lines)
    for k in range(TRAIL_LEN - 1):
        alpha_factor = (TRAIL_LEN - 1 - k) / float(TRAIL_LEN)
        x0 = ((TRAIL_X[:, k + 1] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y0 = ((TRAIL_Y[:, k + 1] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
        x1 = ((TRAIL_X[:, k] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y1 = ((TRAIL_Y[:, k] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)

        dist_sq = (x1 - x0)**2 + (y1 - y0)**2
        valid = (dist_sq < (160.0**2)) & (x0 >= 0) & (x0 < SIZE[0]) & (y0 >= 0) & (y0 < SIZE[1]) & \
                (x1 >= 0) & (x1 < SIZE[0]) & (y1 >= 0) & (y1 < SIZE[1])

        # Type 0: Pulled Matter (Solar Amber & Radiant Topaz)
        m0 = valid & (P_TYPE == 0)
        if np.any(m0):
            lines0 = np.column_stack([x0[m0], y0[m0], x1[m0], y1[m0]])
            py5.stroke(255, 175, 20, int(170 * alpha_factor))
            py5.stroke_weight(2.0)
            py5.lines(lines0)

        # Type 1: Forward Photons (Radiant Electric Mint)
        m1 = valid & (P_TYPE == 1)
        if np.any(m1):
            lines1 = np.column_stack([x0[m1], y0[m1], x1[m1], y1[m1]])
            py5.stroke(0, 240, 160, int(140 * alpha_factor))
            py5.stroke_weight(1.6)
            py5.lines(lines1)

    # 2. Particle Heads
    sx = ((P_X + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
    sy = ((P_Y + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
    valid_head = (sx >= 0) & (sx < SIZE[0]) & (sy >= 0) & (sy < SIZE[1])

    m0_head = valid_head & (P_TYPE == 0)
    if np.any(m0_head):
        py5.stroke(255, 235, 160, 250)
        py5.stroke_weight(2.8)
        py5.points(np.column_stack([sx[m0_head], sy[m0_head]]))

    m1_head = valid_head & (P_TYPE == 1)
    if np.any(m1_head):
        py5.stroke(210, 255, 235, 245)
        py5.stroke_weight(2.4)
        py5.points(np.column_stack([sx[m1_head], sy[m1_head]]))

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 240:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Revised optical tractor beam preview captured: {PREVIEW_FILE}")

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
        shutil.copyfile(OUTPUT_VIDEO, WORK_VIDEO)
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
    else:
        print(f"[Video Encoding Failed] ffmpeg error:\n{res.stderr}")

    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

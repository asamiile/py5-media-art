"""
Kinetic Andreev Reflection Bound States 2D (Revised & Vectorized)
Generative media art depicting Bogoliubov-de Gennes quasiparticle dynamics,
Andreev retro-reflection at superconductor-normal-superconductor (SNS) interfaces,
quantized Andreev bound state resonances, and macroscopic Cooper pair condensation.

Features:
- Macroscopic superconducting order parameter profile Delta(x, y) with sharp proximity barriers
- Dynamic Josephson phase difference Delta phi(t) driving time-dependent 2D concentric condensate ripples
- Time-reversed retro-reflection: glowing cyan electrons converting into radiant magenta holes
- Luminous particle ribbon trails demonstrating the exact time-reversed retro-reflection trajectories
- Resonant standing-wave Andreev bound states inside the mesoscopic normal metal cavity
- Dual-light Blinn-Phong specular relief shading on cryogenic quantum interface topography
- Vectorized batch rendering using py5.lines() and py5.points() for 60 FPS performance
- 2,400 multi-trail Lagrangian quasiparticles (Electrons, Holes, Cooper Pairs)
- 720 frames @ 60 FPS (12 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_andreev_reflection_bound_states_2d"
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
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)  # Cool glacial cyan
LIGHT2_DIR = np.array([0.577, 0.577, 0.577], dtype=np.float32)    # Warm solar gold

# Cavity boundary constants
CAVITY_X = 2.85
XI = 0.18  # Superconducting coherence length / interface sharpness

# Particle system: 2,400 quasiparticles with multi-segment history trails
NUM_PARTICLES = 2400
TRAIL_LEN = 6

P_X = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_Y = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_VX = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_VY = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_TYPE = np.zeros(NUM_PARTICLES, dtype=np.int32)     # 0: Electron (-e), 1: Hole (+e), 2: Cooper Pair (2e)
P_AGE = np.zeros(NUM_PARTICLES, dtype=np.float32)

TRAIL_X = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)
TRAIL_Y = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)


def init_particles():
    global P_X, P_Y, P_VX, P_VY, P_TYPE, P_AGE, TRAIL_X, TRAIL_Y
    np.random.seed(42)

    # 1,600 particles in normal cavity (|x| < CAVITY_X)
    n_cavity = 1600
    P_X[:n_cavity] = np.random.uniform(-CAVITY_X * 0.92, CAVITY_X * 0.92, size=n_cavity).astype(np.float32)
    P_Y[:n_cavity] = np.random.uniform(-3.4, 3.4, size=n_cavity).astype(np.float32)
    angles = np.random.uniform(-0.75, 0.75, size=n_cavity).astype(np.float32)
    dirs = np.random.choice([-1.0, 1.0], size=n_cavity).astype(np.float32)
    speed = np.random.uniform(0.05, 0.08, size=n_cavity).astype(np.float32)
    P_VX[:n_cavity] = dirs * np.cos(angles) * speed
    P_VY[:n_cavity] = np.sin(angles) * speed
    P_TYPE[:n_cavity] = np.random.choice([0, 1], size=n_cavity, p=[0.55, 0.45])
    P_AGE[:n_cavity] = np.random.uniform(0.0, 100.0, size=n_cavity).astype(np.float32)

    # 800 particles in superconducting leads (|x| > CAVITY_X)
    n_sc = NUM_PARTICLES - n_cavity
    side = np.random.choice([-1.0, 1.0], size=n_sc)
    P_X[n_cavity:] = (side * np.random.uniform(CAVITY_X * 1.08, 6.2, size=n_sc)).astype(np.float32)
    P_Y[n_cavity:] = np.random.uniform(-3.4, 3.4, size=n_sc).astype(np.float32)
    P_VX[n_cavity:] = (side * np.random.uniform(0.015, 0.035, size=n_sc)).astype(np.float32)
    P_VY[n_cavity:] = np.random.uniform(-0.01, 0.01, size=n_sc).astype(np.float32)
    P_TYPE[n_cavity:] = 2
    P_AGE[n_cavity:] = np.random.uniform(0.0, 100.0, size=n_sc).astype(np.float32)

    for k in range(TRAIL_LEN):
        TRAIL_X[:, k] = P_X - P_VX * k
        TRAIL_Y[:, k] = P_Y - P_VY * k


init_particles()


def compute_andreev_field(t_norm):
    """
    Synthesize the macroscopic superconducting order parameter,
    dynamic 2D concentric Josephson phase ripples in the leads,
    Andreev bound state interference moiré in the cavity,
    and dual-light specular relief normal mapping.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Superconducting Order Parameter Magnitude Delta(x)
    delta_left = 1.0 / (1.0 + np.exp((x + CAVITY_X) / XI))
    delta_right = 1.0 / (1.0 + np.exp(-(x - CAVITY_X) / XI))
    Delta_mag = np.clip(delta_left + delta_right, 0.0, 1.0)
    normal_fraction = 1.0 - Delta_mag

    # 2. Josephson Phase Difference between leads
    phi_L = -np.pi * np.sin(tau)
    phi_R = np.pi * np.sin(tau)

    # 3. 2D Concentric Condensate Wavefronts in Superconducting Leads
    r_left = np.sqrt((x + CAVITY_X + 2.2)**2 + (y * 0.9)**2)
    r_right = np.sqrt((x - CAVITY_X - 2.2)**2 + (y * 0.9)**2)
    k_sc = 5.2

    sc_wave_left = np.cos(k_sc * r_left + phi_L - tau * 2.0)
    sc_wave_right = np.cos(k_sc * r_right - phi_R + tau * 2.0)
    condensate_ripples = delta_left * (0.55 + 0.45 * sc_wave_left) + delta_right * (0.55 + 0.45 * sc_wave_right)

    # 4. Andreev Bound States (ABS) Resonance in Normal Cavity (|x| < CAVITY_X)
    abs_field = np.zeros_like(x)
    for m in range(1, 6):
        kx = m * np.pi / CAVITY_X
        ky = m * np.pi / 2.7
        phase_shift = (phi_R - phi_L) * 0.5 * (m % 2)
        mode = np.cos(kx * x + phase_shift) * np.sin(ky * y + 0.6 * np.sin(tau + m * 0.7))
        abs_field += (0.45 / np.sqrt(m)) * (mode**2)

    abs_intensity = normal_fraction * abs_field

    # 5. Interface Specular Relief & Normal Mapping
    topo = Delta_mag * 1.5 + abs_intensity * 0.4
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

    # 6. Color Synthesis
    # Base background: Deep cryogenic vacuum obsidian
    r_bg, g_bg, b_bg = 6.0, 8.0, 16.0

    # Superconducting leads bulk: Deep azure cobalt + glowing teal/cyan ripples
    r_sc = 12.0 + condensate_ripples * 18.0
    g_sc = 45.0 + condensate_ripples * 135.0
    b_sc = 110.0 + condensate_ripples * 145.0

    # Normal cavity bulk: Deep quantum well with rich magenta/violet interference
    r_norm = 28.0 + abs_intensity * 185.0
    g_norm = 12.0 + abs_intensity * 45.0
    b_norm = 48.0 + abs_intensity * 210.0

    base_r = Delta_mag * r_sc + normal_fraction * r_norm
    base_g = Delta_mag * g_sc + normal_fraction * g_norm
    base_b = Delta_mag * b_sc + normal_fraction * b_norm

    # Interface highlights & specular sheen
    interface_glow = np.exp(-0.5 * ((np.abs(x) - CAVITY_X) / 0.14)**2)

    r_out = base_r + interface_glow * 190.0 + spec2 * 255.0 + spec1 * 60.0
    g_out = base_g + interface_glow * 230.0 + spec2 * 210.0 + spec1 * 220.0
    b_out = base_b + interface_glow * 255.0 + spec2 * 110.0 + spec1 * 255.0

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
    print(f"[{WORK_NAME}] Initialized fast vectorized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count

    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = ((frame - 1) % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    field_rgb = compute_andreev_field(t_norm)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Update 2,400 quasiparticles and history trails
    global P_X, P_Y, P_VX, P_VY, P_TYPE, P_AGE, TRAIL_X, TRAIL_Y
    P_AGE += 1.0

    # Push current positions into trail buffer
    TRAIL_X[:, 1:] = TRAIL_X[:, :-1]
    TRAIL_X[:, 0] = P_X
    TRAIL_Y[:, 1:] = TRAIL_Y[:, :-1]
    TRAIL_Y[:, 0] = P_Y

    # Gentle transverse ABS wave steering
    cavity_mask = np.abs(P_X) < CAVITY_X
    abs_kick_y = np.where(
        cavity_mask,
        np.sin(P_X * 2.2 + tau * 2.5) * 0.0025,
        0.0
    ).astype(np.float32)

    P_X += P_VX
    P_Y += P_VY + abs_kick_y

    # Andreev Retro-Reflection at interfaces |x| = CAVITY_X
    hit_right = (P_X >= CAVITY_X) & (P_TYPE == 0)
    P_VX[hit_right] = -np.abs(P_VX[hit_right])
    P_TYPE[hit_right] = 1

    hit_left = (P_X <= -CAVITY_X) & (P_TYPE == 1)
    P_VX[hit_left] = np.abs(P_VX[hit_left])
    P_TYPE[hit_left] = 0

    hit_left_e = (P_X <= -CAVITY_X) & (P_TYPE == 0)
    P_VX[hit_left_e] = np.abs(P_VX[hit_left_e])
    P_TYPE[hit_left_e] = 1

    hit_right_h = (P_X >= CAVITY_X) & (P_TYPE == 1)
    P_VX[hit_right_h] = -np.abs(P_VX[hit_right_h])
    P_TYPE[hit_right_h] = 0

    # Top/Bottom boundary reflection
    hit_top = P_Y > 3.45
    P_VY[hit_top] = -np.abs(P_VY[hit_top])
    hit_bot = P_Y < -3.45
    P_VY[hit_bot] = np.abs(P_VY[hit_bot])

    # Superconducting lead recirculator
    sc_wrap_right = (P_TYPE == 2) & (P_X > 6.35)
    P_X[sc_wrap_right] = CAVITY_X * 1.06
    P_Y[sc_wrap_right] = np.random.uniform(-3.4, 3.4, size=np.sum(sc_wrap_right))

    sc_wrap_left = (P_TYPE == 2) & (P_X < -6.35)
    P_X[sc_wrap_left] = -CAVITY_X * 1.06
    P_Y[sc_wrap_left] = np.random.uniform(-3.4, 3.4, size=np.sum(sc_wrap_left))

    # Fast Vectorized Quasiparticle Rendering with py5.lines() and py5.points()
    # 1. Draw ribbon trails across history segments
    for k in range(TRAIL_LEN - 1):
        alpha_factor = (TRAIL_LEN - 1 - k) / float(TRAIL_LEN)
        x0 = ((TRAIL_X[:, k + 1] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y0 = ((TRAIL_Y[:, k + 1] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
        x1 = ((TRAIL_X[:, k] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y1 = ((TRAIL_Y[:, k] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)

        valid = (x0 >= 0) & (x0 < SIZE[0]) & (y0 >= 0) & (y0 < SIZE[1]) & \
                (x1 >= 0) & (x1 < SIZE[0]) & (y1 >= 0) & (y1 < SIZE[1])

        # Type 0: Electron (Glacial Cyan)
        m0 = valid & (P_TYPE == 0)
        if np.any(m0):
            lines0 = np.column_stack([x0[m0], y0[m0], x1[m0], y1[m0]])
            py5.stroke(0, 225, 255, int(150 * alpha_factor))
            py5.stroke_weight(2.0)
            py5.lines(lines0)

        # Type 1: Hole (Neon Magenta)
        m1 = valid & (P_TYPE == 1)
        if np.any(m1):
            lines1 = np.column_stack([x0[m1], y0[m1], x1[m1], y1[m1]])
            py5.stroke(255, 25, 185, int(160 * alpha_factor))
            py5.stroke_weight(2.0)
            py5.lines(lines1)

        # Type 2: Cooper Pair (Solar Pearl)
        m2 = valid & (P_TYPE == 2)
        if np.any(m2):
            lines2 = np.column_stack([x0[m2], y0[m2], x1[m2], y1[m2]])
            py5.stroke(255, 235, 140, int(130 * alpha_factor))
            py5.stroke_weight(1.6)
            py5.lines(lines2)

    # 2. Draw particle heads with py5.points()
    sx = ((P_X + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
    sy = ((P_Y + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
    valid_head = (sx >= 0) & (sx < SIZE[0]) & (sy >= 0) & (sy < SIZE[1])

    m0_head = valid_head & (P_TYPE == 0)
    if np.any(m0_head):
        py5.stroke(215, 250, 255, 245)
        py5.stroke_weight(2.8)
        py5.points(np.column_stack([sx[m0_head], sy[m0_head]]))

    m1_head = valid_head & (P_TYPE == 1)
    if np.any(m1_head):
        py5.stroke(255, 190, 240, 245)
        py5.stroke_weight(2.8)
        py5.points(np.column_stack([sx[m1_head], sy[m1_head]]))

    m2_head = valid_head & (P_TYPE == 2)
    if np.any(m2_head):
        py5.stroke(255, 255, 255, 250)
        py5.stroke_weight(3.2)
        py5.points(np.column_stack([sx[m2_head], sy[m2_head]]))

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 240:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Revised Andreev reflection preview captured: {PREVIEW_FILE}")

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

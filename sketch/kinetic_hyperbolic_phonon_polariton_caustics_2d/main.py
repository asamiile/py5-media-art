"""
Kinetic Hyperbolic Phonon Polariton Caustics 2D
Generative media art depicting anisotropic polariton propagation,
directional ray caustics, and sub-diffraction wavepacket canalization
in a 2D van der Waals crystal (alpha-MoO3) across the Reststrahlen band.

Features:
- Natural hyperbolic dispersion with open hyperbolic equifrequency surfaces
- Directional polariton ray caustics fanning out from nanoscale gold antenna tips
- Negative phase velocity wavefronts with concave curvature and sub-wavelength fringes
- Crossing ray caustics forming diamond interference moire networks
- Atomic cleavage step edge reflections and terrace standing waves
- Dual-light Blinn-Phong specular normal mapping for crystalline van der Waals luster
- 4,000 Lagrangian polariton quasiparticle wavepackets tracing Poynting vector rays
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_hyperbolic_phonon_polariton_caustics_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 900
FPS = 60
SIZE = (1920, 1080)

# Computational Grid
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-6.4, 6.4, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-3.6, 3.6, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32) # Cool Glacial Cyan
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)  # Warm Incandescent Gold

# Particle system: 4,000 polariton quasiparticles
NUM_PARTICLES = 4000
P_SOURCE = np.zeros(NUM_PARTICLES, dtype=np.int32)
P_ARM = np.zeros(NUM_PARTICLES, dtype=np.int32)
P_DIST = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_SPEED = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_PHASE = np.zeros(NUM_PARTICLES, dtype=np.float32)

SOURCES = [
    (0.0, 0.0, 1.0, 0.0),
    (-3.4, 0.0, 0.65, 0.9),
    (3.4, 0.0, 0.65, -0.9)
]

def init_particles():
    global P_SOURCE, P_ARM, P_DIST, P_SPEED, P_PHASE
    np.random.seed(42)
    P_SOURCE = np.random.choice([0, 1, 2], size=NUM_PARTICLES, p=[0.5, 0.25, 0.25])
    P_ARM = np.random.choice([0, 1, 2, 3], size=NUM_PARTICLES) # 4 ray branches (+/- X, +/- Y)
    P_DIST = np.random.uniform(0.05, 5.5, size=NUM_PARTICLES).astype(np.float32)
    P_SPEED = np.random.uniform(0.025, 0.055, size=NUM_PARTICLES).astype(np.float32)
    P_PHASE = np.random.uniform(0.0, 2.0 * np.pi, size=NUM_PARTICLES).astype(np.float32)

init_particles()


def compute_polariton_field(t_norm):
    """
    Computes hyperbolic polariton field, caustics, and specular lighting.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # Hyperbolic asymptote angle sweep across Reststrahlen band
    theta_c = 0.64 + 0.16 * np.sin(tau)
    tan_th = np.tan(theta_c)
    cos_th = np.cos(theta_c)
    sin_th = np.sin(theta_c)
    inv_hyp = 1.0 / np.sqrt(1.0 + tan_th**2)

    kp = 17.5 # Sub-diffraction polariton wavevector
    w_ray = 0.13 # Ray caustic transverse waist width

    total_real = np.zeros_like(x)
    total_imag = np.zeros_like(x)
    caustic_envelope = np.zeros_like(x)

    for sx, sy, weight, phase_offset in SOURCES:
        dx = x - sx
        dy = y - sy
        r = np.sqrt(dx**2 + dy**2) + 0.07

        # Distance from hyperbolic ray asymptotes
        dist_asymptote = np.abs(np.abs(dy) - tan_th * np.abs(dx)) * inv_hyp
        ray_amp = np.exp(-0.5 * (dist_asymptote / w_ray)**2) / (np.sqrt(r) + 0.18)

        # Spatial decay envelope
        decay = np.exp(-r / 5.0)
        amp = weight * (ray_amp * 1.7 + 0.3 * decay)

        # Concave hyperbolic phase with negative dispersion
        phase = kp * (np.abs(dx) * cos_th + np.abs(dy) * sin_th) - tau * 3.0 + phase_offset

        total_real += amp * np.cos(phase)
        total_imag += amp * np.sin(phase)
        caustic_envelope += amp * ray_amp

    intensity = total_real**2 + total_imag**2
    phase_angle = np.arctan2(total_imag, total_real)

    # Crystal cleavage step edges reflection fringes (atomic terraces)
    step_fringes = 0.32 * (
        np.sin(kp * 1.1 * (y - 2.7))**2 * np.exp(-np.abs(y - 2.7) / 0.45) +
        np.sin(kp * 1.1 * (y + 2.7))**2 * np.exp(-np.abs(y + 2.7) / 0.45) +
        np.sin(kp * 1.1 * (x - 5.2))**2 * np.exp(-np.abs(x - 5.2) / 0.45) +
        np.sin(kp * 1.1 * (x + 5.2))**2 * np.exp(-np.abs(x + 5.2) / 0.45)
    )

    # Normal mapping & specular sheen
    gy, gx = np.gradient(intensity + step_fringes * 0.5)
    nx = -gx * 2.8
    ny = -gy * 2.8
    nz = np.ones_like(nx)
    norm_len = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = dot1 ** 16.0

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = dot2 ** 22.0

    # Color synthesis:
    # 1. van der Waals basal plane (Deep Obsidian / Bismuth Indigo)
    r_bg = 9.0 + 6.0 * np.sin(x * 0.4)
    g_bg = 14.0 + 8.0 * np.cos(y * 0.4)
    b_bg = 26.0 + 10.0 * np.sin((x + y) * 0.25)

    # 2. Caustic cones: Electric Emerald & Glacial Cyan
    caust_norm = np.clip(caustic_envelope * 0.75, 0.0, 1.0)
    # 3. Interference fringes: Neon Laser Fuchsia / Magenta & Amethyst
    interf_norm = np.clip(intensity * 0.45, 0.0, 1.0)
    phase_hue = 0.5 + 0.5 * np.sin(phase_angle)

    r_out = r_bg + interf_norm * (225.0 * phase_hue + 30.0) + spec2 * 255.0 + step_fringes * 175.0
    g_out = g_bg + caust_norm * 255.0 + interf_norm * 45.0 * (1.0 - phase_hue) + spec2 * 215.0 + spec1 * 175.0
    b_out = b_bg + caust_norm * 240.0 + interf_norm * 255.0 * (1.0 - phase_hue * 0.5) + spec1 * 255.0 + step_fringes * 215.0

    # 4. Metallic nano-antenna tip glow (Solar Gold & Liquid White)
    for sx, sy, _, _ in SOURCES:
        r_ant = np.sqrt((x - sx)**2 + (y - sy)**2)
        tip_glow = np.exp(-r_ant / 0.17) * 255.0
        r_out += tip_glow * 1.0
        g_out += tip_glow * 0.86
        b_out += tip_glow * 0.38

    r_final = np.clip(r_out, 0, 255).astype(np.uint32)
    g_final = np.clip(g_out, 0, 255).astype(np.uint32)
    b_final = np.clip(b_out, 0, 255).astype(np.uint32)

    rgb = np.stack([
        np.clip(r_out, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_out, 0, 255).astype(np.uint8)
    ], axis=-1)
    return rgb, theta_c


def to_screen(x, y):
    sx = int((x + 6.4) / 12.8 * SIZE[0])
    sy = int((y + 3.6) / 7.2 * SIZE[1])
    return sx, sy


def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count

    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = ((frame - 1) % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    # Compute polariton field and current asymptote angle
    field_rgb, theta_c = compute_polariton_field(t_norm)
    cos_th = np.cos(theta_c)
    sin_th = np.sin(theta_c)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Draw crystal edge guide markers
    py5.stroke(0, 255, 170, 70)
    py5.stroke_weight(1.0)
    s_top_x1, s_top_y = to_screen(-5.2, -2.7)
    s_top_x2, _ = to_screen(5.2, -2.7)
    py5.line(s_top_x1, s_top_y, s_top_x2, s_top_y)

    _, s_bot_y = to_screen(-5.2, 2.7)
    py5.line(s_top_x1, s_bot_y, s_top_x2, s_bot_y)

    s_left_x, s_left_y1 = to_screen(-5.2, -2.7)
    _, s_left_y2 = to_screen(-5.2, 2.7)
    py5.line(s_left_x, s_left_y1, s_left_x, s_left_y2)

    s_right_x, _ = to_screen(5.2, -2.7)
    py5.line(s_right_x, s_left_y1, s_right_x, s_left_y2)

    # Update and draw 4,000 polariton quasiparticles
    global P_DIST
    P_DIST += P_SPEED
    P_DIST = np.where(P_DIST > 5.5, 0.05, P_DIST)

    # Arm direction signs (+/- dx, +/- dy)
    arm_signs = [
        (1.0, 1.0),
        (-1.0, 1.0),
        (1.0, -1.0),
        (-1.0, -1.0)
    ]

    for i in range(NUM_PARTICLES):
        src_idx = P_SOURCE[i]
        sx_src, sy_src = SOURCES[src_idx][0], SOURCES[src_idx][1]
        arm_idx = P_ARM[i]
        sign_x, sign_y = arm_signs[arm_idx]

        d = P_DIST[i]
        # Quasiparticle position along hyperbolic ray asymptote + transverse ripple
        jitter = 0.03 * np.sin(d * 18.0 + P_PHASE[i] + tau * 4.0)
        px = sx_src + sign_x * (d * cos_th - jitter * sin_th)
        py = sy_src + sign_y * (d * sin_th + jitter * cos_th)

        screen_x, screen_y = to_screen(px, py)
        if 0 <= screen_x < SIZE[0] and 0 <= screen_y < SIZE[1]:
            # Color gradient: Near antenna is Solar Gold, mid-ray is Emerald/Cyan, far is Violet
            alpha = int(240 * (1.0 - d / 5.5))
            if d < 0.6:
                py5.stroke(255, 235, 120, alpha)
                py5.stroke_weight(2.2)
            elif i % 3 == 0:
                py5.stroke(0, 255, 170, alpha) # Emerald
                py5.stroke_weight(1.6)
            elif i % 3 == 1:
                py5.stroke(0, 220, 255, alpha) # Cyan
                py5.stroke_weight(1.5)
            else:
                py5.stroke(255, 0, 140, alpha) # Fuchsia
                py5.stroke_weight(1.4)
            py5.point(screen_x, screen_y)

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Polariton caustics preview captured: {PREVIEW_FILE}")

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

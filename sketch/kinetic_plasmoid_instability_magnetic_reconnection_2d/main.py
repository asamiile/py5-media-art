"""
Kinetic Plasmoid Instability & Magnetic Reconnection 2D
Generative media art depicting the spontaneous breakdown of a Sweet-Parker
current sheet into a cascading chain of plasmoids (magnetic islands) via the
tearing-mode plasmoid instability at high Lundquist numbers (S >> 10^4).

Features:
- Continuous 2D magnetic flux function A_z(x, y) with tearing mode harmonics
- Magnetic field B = curl(A_z z_hat) and current density J_z = -nabla^2 A_z
- Hall-MHD quadrupolar out-of-plane magnetic field B_z around X-points
- Concentric plasmoid flux loops (O-points) and hyperbolic separatrix geometry
- Specular surface normal shading with dual dynamic light sources
- 3,800 charged plasma particles undergoing E x B drift, Larmor gyration, and Alfvenic jetting
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_plasmoid_instability_magnetic_reconnection_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 900
FPS = 60
SIZE = (1920, 1080)

# High-resolution computational grid
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional light vectors
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)


def compute_plasmoid_mhd(t_norm):
    """
    Computes the 2D resistive and Hall-MHD plasmoid reconnection field.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Base Harris Current Sheet with Inflow Funnel Curvature
    delta_sheet = 0.55
    b0 = 1.6
    funnel = 0.28 * (x**2 / 45.0) * np.exp(-np.abs(y) / 2.2)
    a_base = -b0 * delta_sheet * np.log(np.cosh(y / delta_sheet) + 1e-5) + funnel

    # 2. Multi-scale Tearing Modes & Plasmoid Hierarchy
    k_tearing = 1.30
    sheet_envelope = np.exp(-(y * y) / (2.0 * (1.2 * delta_sheet)**2))
    
    plasmoid_perturbation = np.zeros_like(x)
    for m in [1, 2, 3, 5, 7]:
        km = m * k_tearing
        phase_vel = np.sign(x) * (0.9 + 0.35 * np.abs(x))
        amp = 0.35 / (m**0.75)
        plasmoid_perturbation += amp * np.cos(km * x - tau * 1.6 * phase_vel)

    a_total = a_base + sheet_envelope * plasmoid_perturbation

    # 3. Magnetic Field Components & Current Density J_z = -nabla^2 A_z
    da_dy = (np.roll(a_total, -1, axis=0) - np.roll(a_total, 1, axis=0)) * 0.5
    da_dx = (np.roll(a_total, -1, axis=1) - np.roll(a_total, 1, axis=1)) * 0.5
    bx = -da_dy
    by = da_dx
    b_mag = np.sqrt(bx * bx + by * by + 1e-4)

    d2a_dx2 = np.roll(a_total, -1, axis=1) - 2.0 * a_total + np.roll(a_total, 1, axis=1)
    d2a_dy2 = np.roll(a_total, -1, axis=0) - 2.0 * a_total + np.roll(a_total, 1, axis=0)
    jz = -(d2a_dx2 + d2a_dy2)
    current_intensity = np.power(np.clip(np.abs(jz) / 1.7, 0.0, 1.0), 1.6)

    # 4. Hall-MHD Quadrupolar B_z field (anti-symmetric in x and y around X-points)
    hall_bz = 0.70 * np.sin(2.4 * x - tau * 2.2) * (y / delta_sheet) * np.exp(-(y * y) / (1.6 * delta_sheet * delta_sheet))

    # 5. Upstream Alfvénic Waves in Inflow
    turb_wave = (
        0.35 * np.sin(0.8 * x + 1.2 * y - tau * 1.5)
        + 0.25 * np.sin(1.7 * x - 0.9 * y + tau * 2.1)
        + 0.18 * np.sin(2.5 * x + 2.1 * y - tau * 3.0)
    ) * np.clip(np.abs(y) / 2.5, 0.0, 1.0)

    # 6. Flux Surface Contours restricted to near-sheet region
    flux_freq = 8.0
    flux_phase = a_total * flux_freq
    flux_lines = np.power(np.clip(np.cos(flux_phase) * 0.5 + 0.5, 0.0, 1.0), 8.0) * np.exp(-(y * y) / 5.0)

    # 7. Alfvénic Outflow Jets
    outflow_jet = np.clip((np.abs(x) / 6.5) * sheet_envelope * (1.0 - np.clip(np.abs(y) / (1.5 * delta_sheet), 0.0, 1.0)), 0.0, 1.0)

    # 8. Specular Normal Mapping
    h_field = (
        0.50 * current_intensity
        + 0.30 * flux_lines
        + 0.28 * np.abs(hall_bz)
        + 0.20 * outflow_jet
        + 0.15 * np.abs(turb_wave)
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

    hall_pos = np.clip(hall_bz * 1.8, 0.0, 1.0)
    hall_neg = np.clip(-hall_bz * 1.8, 0.0, 1.0)
    norm_fl = np.clip(flux_lines * 1.5, 0.0, 1.0)
    norm_curr = np.clip(current_intensity * 1.6, 0.0, 1.0)
    norm_jet = np.clip(outflow_jet * 1.5, 0.0, 1.0)
    bg_field_ambient = (0.2 + 0.15 * turb_wave) * np.clip(np.abs(y) / 5.4, 0.0, 1.0)

    red = (
        2.0
        + 18.0 * bg_field_ambient
        + 255.0 * norm_curr
        + 240.0 * hall_neg
        + 20.0 * hall_pos
        + 180.0 * norm_jet
        + 200.0 * norm_fl * sheet_envelope
        + spec1 * 255.0
        + spec2 * 180.0 * 0.8
    )
    green = (
        4.0
        + 45.0 * bg_field_ambient
        + 170.0 * norm_curr
        + 15.0 * hall_neg
        + 220.0 * hall_pos
        + 110.0 * norm_jet
        + 130.0 * norm_fl * sheet_envelope
        + spec1 * 255.0 * 0.95
        + spec2 * 140.0 * 0.5
    )
    blue = (
        18.0
        + 120.0 * bg_field_ambient
        + 20.0 * norm_curr
        + 205.0 * hall_neg
        + 245.0 * hall_pos
        + 20.0 * norm_jet
        + 245.0 * norm_fl * sheet_envelope
        + spec1 * 255.0
        + spec2 * 40.0 * 0.2
    )

    vig = np.clip(1.0 - (np.abs(x) / 9.4)**8.0, 0.0, 1.0) * np.clip(1.0 - (np.abs(y) / 5.25)**8.0, 0.0, 1.0)
    red = np.clip(red * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.86 * vig + 0.14), 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


def to_screen(x, y):
    """Maps physical coordinates (-9.6..9.6, -5.4..5.4) to screen pixels."""
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

    # 1. Background Plasma & Magnetic MHD Fluid
    bg_rgb = compute_plasmoid_mhd(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Dynamic Reconnected Separatrix Curves
    for sign_y in [-1.0, 1.0]:
        py5.no_fill()
        py5.stroke(255, 230, 80, 210)
        py5.stroke_weight(2.2)
        py5.begin_shape()
        for x_step in np.linspace(-9.5, 9.5, 140):
            wobble = 0.09 * np.sin(2.4 * x_step - tau * 3.0)
            y_sep = sign_y * (0.28 + 0.06 * (x_step**2) / 10.0 + wobble)
            sx, sy = to_screen(x_step, y_sep)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 3. Inflow Magnetic Field Streamlines (funneling into reconnection layer)
    for row in range(-6, 7):
        if row == 0:
            continue
        py5.no_fill()
        py5.stroke(0, 180, 255, 70)
        py5.stroke_weight(1.2)
        py5.begin_shape()
        y_val = row * 0.72
        for x_step in np.linspace(-9.5, 9.5, 80):
            dy = -np.sign(y_val) * 0.22 * np.exp(-((x_step / 2.5)**2))
            sx, sy = to_screen(x_step, y_val + dy)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 4. 3,800 Particles: Inflow + Gyro Spirals + Exhaust Jets
    for p in range(3800):
        seed = p * 0.61803398875
        phase_offset = seed * 100.0
        t_part = (t_norm * 3.2 + phase_offset) % 1.0

        side = -1.0 if (p % 2 == 0) else 1.0
        inflow_y_init = (((p * 17) % 100) / 100.0 * 4.6 + 0.4) * side
        inflow_x_init = (((p * 31) % 100) / 100.0 * 8.0 - 4.0)

        # Gyro-radius spiral
        r_larmor = 0.05 * (1.0 + np.abs(inflow_y_init) / 3.0)
        theta_gyro = tau * 8.0 + p * 2.1

        if t_part < 0.45:
            prog = t_part / 0.45
            cur_y = inflow_y_init * (1.0 - 0.88 * (prog**1.4)) + r_larmor * np.sin(theta_gyro)
            cur_x = inflow_x_init + 0.35 * np.sin(inflow_x_init * 1.8 + tau * 2.0) * prog + r_larmor * np.cos(theta_gyro)
        else:
            prog = (t_part - 0.45) / 0.55
            dir_x = np.sign(inflow_x_init + 1e-3)
            cur_x = inflow_x_init + dir_x * (prog**1.7) * 9.0
            cur_y = 0.20 * side * (1.0 - prog) * np.cos(prog * 10.0 + p) + 0.03 * np.sin(theta_gyro)

        sx, sy = to_screen(cur_x, cur_y)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if p % 9 == 0:
                py5.stroke(255, 255, 255, 240)
                py5.stroke_weight(2.5)
            elif p % 3 == 0:
                py5.stroke(255, 205, 50, 190)
                py5.stroke_weight(1.7)
            elif p % 2 == 0:
                py5.stroke(0, 240, 255, 180)
                py5.stroke_weight(1.4)
            else:
                py5.stroke(255, 50, 130, 170)
                py5.stroke_weight(1.3)
            py5.point(sx, sy)

    # Save frame image
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Plasmoid reconnection preview captured: {PREVIEW_FILE}")

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

"""
kinetic_taylor_couette_wavy_vortices_2d
----------------------------------------
Kinetic 2D simulation of Taylor-Couette centrifugal hydrodynamic instability,
wavy vortex flow (WVF), and rheoscopic mica platelet reflectance between concentric
rotating cylinders.

Features:
- 8 stacked counter-rotating toroidal Taylor vortex cells with m=4 azimuthal traveling wave mode.
- Inflow and outflow boundary dynamics: sharp, high-shear convergence zones (inflow jets)
  and divergent plume expansions (outflow boundaries).
- Rheoscopic calligraphic reflectance modeling: anisotropic optical reflectance of microscopic
  mica flakes aligning with the principal rate-of-strain tensor eigenvectors.
- Dual-light Blinn-Phong specular liquid chrome sheen.
- 360 Lagrangian tracer ribbons continuously circulating within the Taylor rolls.
- 2800 glittering mica micro-platelets advecting with Couette shear.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_taylor_couette_wavy_vortices_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

# Rendering parameters
SIZE = (1920, 1080)
TOTAL_FRAMES = 900
FPS = 60

# Domain & Grid configuration
GRID_W, GRID_H = 384, 216
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Directional lighting vectors for Blinn-Phong specular sheen
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)

# WVF Physics parameters
M_WAVE = 4               # 4-fold azimuthal wavy mode
DZ_CELL = 1.35            # Axial height per vortex roll (8 cells in [-5.4, 5.4])
NUM_RIBBONS = 360         # Lagrangian streamline ribbons
NUM_PLATELETS = 2800      # Micro-scale mica flakes

# Pre-seeded Lagrangian particles
np.random.seed(842)
RIBBON_X0 = np.random.uniform(-9.4, 9.4, NUM_RIBBONS).astype(np.float32)
RIBBON_Z0 = np.random.uniform(-5.0, 5.0, NUM_RIBBONS).astype(np.float32)
RIBBON_PHASE = np.random.uniform(0.0, 2.0 * np.pi, NUM_RIBBONS).astype(np.float32)


def compute_taylor_couette_field(t_norm):
    """
    Computes 2D WVF velocity field, shear tensor, rheoscopic mica reflectance,
    and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    omega_wave = 2.0 * tau
    th = GX * (np.pi / 9.6)
    z = GY

    # Azimuthal traveling wave phase & spatial undulation
    phase_wave = M_WAVE * th - omega_wave
    w_disp = 0.36 * np.sin(phase_wave) + 0.11 * np.sin(2.0 * phase_wave + 0.8)

    # Axial coordinate relative to wavy cell centers
    z_rel = (z + w_disp) / DZ_CELL
    cell_idx = np.floor(z_rel).astype(np.int32)
    z_frac = (z_rel - cell_idx) * np.pi  # [0, pi] within each cell
    sign_roll = np.where(cell_idx % 2 == 0, 1.0, -1.0).astype(np.float32)

    # Counter-rotating vortex streamfunction
    psi = np.sin(z_frac) * sign_roll

    # Azimuthal velocity (mean Couette flow + wavy modulation)
    u_th = 1.55 + 0.45 * np.cos(z_frac) * np.cos(phase_wave)
    # Axial velocity (circulation within roll + wavy tilt advection)
    u_z = sign_roll * np.cos(z_frac) * 1.25 + 0.36 * M_WAVE * np.cos(phase_wave) * u_th * 0.22

    # Inflow and outflow boundary metrics
    # Inflow boundaries: rolls push fluid inwards, steep velocity gradients
    # Outflow boundaries: rolls eject fluid outward, broader plumes
    boundary_dist = np.abs(np.sin(z_frac))
    inflow_mask = np.where(cell_idx % 2 == 0, (1.0 - np.cos(z_frac)) * 0.5, (1.0 + np.cos(z_frac)) * 0.5)
    inflow_sharpness = np.power(1.0 - boundary_dist, 5.5) * inflow_mask
    outflow_sharpness = np.power(1.0 - boundary_dist, 3.2) * (1.0 - inflow_mask)

    # Shear strain rate tensor magnitude
    shear = np.sqrt(u_th * u_th + u_z * u_z)

    # Rheoscopic mica platelet orientation
    # Microscopic flakes orient tangent to local streamline direction
    alpha = np.arctan2(u_z, u_th)
    rheo_reflect1 = np.power(np.abs(np.cos(alpha - 0.45)), 3.6)
    rheo_reflect2 = np.power(np.abs(np.sin(alpha + 0.35)), 2.8)

    # Micro-scale striations representing sub-vortex shear sheets
    micro_filaments = np.power(0.5 + 0.5 * np.sin(z_rel * 30.0 + phase_wave * 1.5), 4.0)

    # Specular normal height field
    h_field = (
        0.35 * np.tanh(shear * 0.75)
        + 0.48 * inflow_sharpness
        + 0.22 * psi * psi
        + 0.16 * micro_filaments
    )
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * (0.5 * GRID_W / 19.2)
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * (0.5 * GRID_H / 10.8)
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    # Blinn-Phong specular highlights
    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(dot1, 26.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(dot2, 14.0)

    # Curated Color Grading:
    # Deep background: Midnight Obsidian (#020412)
    # Vortex rolls: Electric Cyan (#00f0ff) & Deep Cobalt (#0a2566)
    # Inflow boundaries: Laser Magenta (#ff0080) & Neon Violet (#9d00ff)
    # Outflow boundaries: Molten Topaz (#ffb300) & Iridescent Silk
    # Specular Sheen: Platinum Diamond White (#ffffff)

    roll_core = np.clip(np.abs(psi), 0.0, 1.0)

    red = (
        2.0
        + 195.0 * inflow_sharpness
        + 60.0 * outflow_sharpness
        + 25.0 * rheo_reflect1
        + spec1 * 255.0
        + spec2 * 215.0 * 0.8
        + micro_filaments * 42.0
    )
    green = (
        4.0
        + 165.0 * roll_core
        + 22.0 * inflow_sharpness
        + 75.0 * outflow_sharpness
        + 48.0 * rheo_reflect2
        + spec1 * 255.0 * 0.96
        + spec2 * 145.0 * 0.5
        + micro_filaments * 68.0
    )
    blue = (
        18.0
        + 235.0 * roll_core
        + 130.0 * inflow_sharpness
        + 20.0 * outflow_sharpness
        + 75.0 * rheo_reflect1
        + spec1 * 255.0
        + spec2 * 65.0 * 0.2
        + micro_filaments * 92.0
    )

    # Vignette framing
    cyl_vignette = (
        np.clip(1.0 - (np.abs(th) / (np.pi * 0.97))**10.0, 0.0, 1.0)
        * np.clip(1.0 - (np.abs(z) / 5.25)**8.0, 0.0, 1.0)
    )
    red = np.clip(red * (0.88 * cyl_vignette + 0.12), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.88 * cyl_vignette + 0.12), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.88 * cyl_vignette + 0.12), 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


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
    omega_wave = 2.0 * tau

    # 1. Background Hydrodynamic & Rheoscopic Field
    bg_rgb = compute_taylor_couette_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Inflow and Outflow Vortex Boundary Separatrices
    z_boundaries = np.arange(-4.725, 5.0, DZ_CELL)
    for idx, zb in enumerate(z_boundaries):
        is_inflow = (idx % 2 == 0)
        py5.no_fill()
        if is_inflow:
            py5.stroke(255, 30, 160, 210)
            py5.stroke_weight(2.4)
        else:
            py5.stroke(0, 230, 255, 140)
            py5.stroke_weight(1.5)

        py5.begin_shape()
        for x_step in np.linspace(-9.5, 9.5, 180):
            th_step = x_step * (np.pi / 9.6)
            ph = M_WAVE * th_step - omega_wave
            w_disp = 0.36 * np.sin(ph) + 0.11 * np.sin(2.0 * ph + 0.8)
            sx, sy = to_screen(x_step, zb - w_disp)
            py5.vertex(sx, sy)
        py5.end_shape()

    # 3. Lagrangian Tracer Streamline Ribbons
    for i in range(NUM_RIBBONS):
        px = (RIBBON_X0[i] + tau * 2.8) % 18.8 - 9.4
        pz = RIBBON_Z0[i]

        pts = []
        for step in range(22):
            pts.append(to_screen(px, pz))
            th_i = px * (np.pi / 9.6)
            ph_i = M_WAVE * th_i - omega_wave
            w_d = 0.36 * np.sin(ph_i) + 0.11 * np.sin(2.0 * ph_i + 0.8)
            z_rel = (pz + w_d) / DZ_CELL
            c_idx = int(np.floor(z_rel))
            z_f = (z_rel - c_idx) * np.pi
            sgn = 1.0 if c_idx % 2 == 0 else -1.0

            u_th = 1.55 + 0.45 * np.cos(z_f) * np.cos(ph_i)
            u_z = sgn * np.cos(z_f) * 1.25 + 0.36 * M_WAVE * np.cos(ph_i) * u_th * 0.22

            px += u_th * 0.075
            pz += u_z * 0.075

        # Render streamline ribbon with glowing alpha gradient
        is_even = ((i // 3) % 2 == 0)
        for s in range(len(pts) - 1):
            progress = s / float(len(pts))
            alpha_val = int(210 * progress)
            if is_even:
                py5.stroke(0, 240, 255, alpha_val)
            else:
                py5.stroke(255, 60, 180, alpha_val)
            py5.stroke_weight(0.9 + 1.2 * progress)
            py5.line(pts[s][0], pts[s][1], pts[s + 1][0], pts[s + 1][1])

    # 4. Lagrangian Mica Platelet Flakes (2800 anisotropic glittering reflectors)
    py5.stroke_weight(1.8)
    for p in range(NUM_PLATELETS):
        seed_p = p * 0.61803398875
        base_x = ((seed_p * 100.0 + tau * 4.2) % 19.0) - 9.5
        th_p = base_x * (np.pi / 9.6)
        ph_p = M_WAVE * th_p - omega_wave
        w_d = 0.36 * np.sin(ph_p) + 0.11 * np.sin(2.0 * ph_p + 0.8)
        base_z = ((p / float(NUM_PLATELETS)) * 10.2 - 5.1) - w_d

        z_rel = (base_z + w_d) / DZ_CELL
        c_idx = int(np.floor(z_rel))
        z_f = (z_rel - c_idx) * np.pi
        sgn = 1.0 if c_idx % 2 == 0 else -1.0
        u_th = 1.55 + 0.45 * np.cos(z_f) * np.cos(ph_p)
        u_z = sgn * np.cos(z_f) * 1.25

        alpha_flk = np.arctan2(u_z, u_th)
        refl = (np.cos(alpha_flk * 2.0 - 0.5) + 1.0) * 0.5

        sx, sy = to_screen(base_x, base_z)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if refl > 0.62:
                py5.stroke(255, 255, 255, int(225 * refl))
                py5.stroke_weight(2.2)
            else:
                py5.stroke(int(40 + 215 * refl), int(180 + 75 * refl), 255, int(155 * refl))
                py5.stroke_weight(1.4)
            py5.point(sx, sy)

    # 5. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] Taylor-Couette preview captured: {PREVIEW_PNG}")

    if frame % 60 == 0:
        pct = (frame / float(TOTAL_FRAMES)) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 6. Completion and Video Encoding
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

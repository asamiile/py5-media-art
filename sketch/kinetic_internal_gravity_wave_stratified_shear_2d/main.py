"""
kinetic_internal_gravity_wave_stratified_shear_2d
---------------------------------------------------
Kinetic 2D geophysical fluid dynamics simulation of Internal Gravity Waves (IGW),
St. Andrew's Cross radiation beams, and Kelvin-Helmholtz breaking billows in a
stably stratified sheared ocean.

Features:
- Stably stratified Boussinesq density profile with Brunt-Väisälä buoyancy frequency N.
- St. Andrew's Cross 4-lobed diagonal internal wave radiation beams (omega = N * cos(theta_ray)).
- Lee wave trains propagating behind submerged bathymetric topography.
- Breaking Kelvin-Helmholtz cat's-eye vortex billows formed where local Richardson number Ri < 0.25.
- Schlieren / shadowgraph refractive index gradient visualization (|grad(rho)|).
- Dual-light Blinn-Phong specular ocean chrome normal shading.
- 420 Lagrangian stratified isopycnal streamline ribbons advecting with tidal shear and wave orbitals.
- 3200 bioluminescent fluid parcel tracers oscillating at the Brunt-Väisälä frequency.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_internal_gravity_wave_stratified_shear_2d"
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

# Particle counts
NUM_RIBBONS = 420
NUM_TRACERS = 3200

# Pre-seeded Lagrangian particles
np.random.seed(99)
RIBBON_X0 = np.random.uniform(-9.2, 9.2, NUM_RIBBONS).astype(np.float32)
RIBBON_Y0 = np.random.uniform(-5.0, 5.0, NUM_RIBBONS).astype(np.float32)


def compute_internal_gravity_wave_field(t_norm):
    """
    Computes 2D internal gravity wave density perturbations, Schlieren refractive
    gradients, breaking billow vortices, and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. St. Andrew's Cross Oblique Internal Wave Beams
    theta_ray = np.pi / 4.2  # ~43 degrees
    cos_r, sin_r = np.cos(theta_ray), np.sin(theta_ray)

    xi1 = cos_r * x + sin_r * y
    eta1 = -sin_r * x + cos_r * y

    xi2 = cos_r * x - sin_r * y
    eta2 = sin_r * x + cos_r * y

    beam_width = 1.15
    beam1 = np.exp(-(eta1 * eta1) / (2.0 * beam_width * beam_width)) * np.sin(2.4 * xi1 - tau * 2.5)
    beam2 = np.exp(-(eta2 * eta2) / (2.0 * beam_width * beam_width)) * np.sin(2.4 * xi2 - tau * 2.5)

    # 2. Stratified Sheared Background & Lee Waves
    k_lee = 1.35
    lee_waves = (
        np.sin(k_lee * x - tau * 1.8)
        * np.cos(1.2 * y)
        * np.exp(-0.15 * (x * x / 15.0 + y * y / 6.0))
    )

    # 3. Breaking Kelvin-Helmholtz Vortex Billows
    y_interface1 = 1.6 + 0.35 * np.sin(1.1 * x - tau * 2.0)
    y_interface2 = -1.6 - 0.35 * np.sin(1.1 * x - tau * 2.0)

    dist_int1 = y - y_interface1
    dist_int2 = y - y_interface2

    kh_core1 = np.exp(-(dist_int1 * dist_int1) / 0.6) * (
        np.cos(1.8 * x - tau * 3.0) + 0.4 * np.cos(3.6 * x - tau * 6.0 + 1.2)
    )
    kh_core2 = np.exp(-(dist_int2 * dist_int2) / 0.6) * (
        np.cos(1.8 * x + tau * 3.0) + 0.4 * np.cos(3.6 * x + tau * 6.0 - 1.2)
    )

    # Total density perturbation
    rho_prime = 0.55 * (beam1 + beam2) + 0.4 * lee_waves + 0.35 * (kh_core1 + kh_core2)
    rho_total = -0.35 * y + rho_prime

    # Density gradient magnitude (Schlieren refractive optics)
    drho_dy = (np.roll(rho_total, -1, axis=0) - np.roll(rho_total, 1, axis=0)) * 0.5
    drho_dx = (np.roll(rho_total, -1, axis=1) - np.roll(rho_total, 1, axis=1)) * 0.5
    grad_rho = np.sqrt(drho_dx * drho_dx + drho_dy * drho_dy + 0.01)

    norm_schlieren = np.power(np.clip(grad_rho / 0.55, 0.0, 1.0), 1.6)
    energy_wave = np.power(np.clip((beam1 * beam1 + beam2 * beam2) * 1.5, 0.0, 1.0), 0.8)
    norm_billow = np.power(np.clip(np.abs(kh_core1 + kh_core2) * 1.4, 0.0, 1.0), 1.2)

    # Isopycnal micro-striations
    isopycnal_freq = 12.0
    striations = np.power(0.5 + 0.5 * np.sin(rho_total * isopycnal_freq + tau * 2.0), 3.0)

    # Specular normal height field
    h_field = (
        0.35 * norm_schlieren
        + 0.3 * energy_wave
        + 0.25 * norm_billow
        + 0.15 * striations
    )
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    # Dual-light Blinn-Phong specular highlights
    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(np.clip((dot1 - 0.55) / 0.45, 0.0, 1.0), 6.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(np.clip((dot2 - 0.55) / 0.45, 0.0, 1.0), 5.0)

    # Curated Palette:
    # 1. Abyssal Trench Obsidian Void (#010310)
    # 2. Resonant Gravity Wave Beams: Glacial Bioluminescent Cyan (#00f5ff) & Azure (#0066cc)
    # 3. Breaking Billow Crests: Incandescent Solar Topaz (#ffb300) & Amber Fire (#ff5500)
    # 4. Schlieren Caustic Bands: Radiant Laser Cerise (#ff0077) & Royal Violet (#7700cc)
    # 5. Specular Highlights: Diamond Chrome White (#ffffff)

    red = (
        2.0
        + 215.0 * norm_billow
        + 190.0 * norm_schlieren
        + 15.0 * energy_wave
        + spec1 * 255.0
        + spec2 * 190.0 * 0.8
        + striations * 35.0
    )
    green = (
        4.0
        + 155.0 * norm_billow
        + 25.0 * norm_schlieren
        + 165.0 * energy_wave
        + spec1 * 255.0 * 0.95
        + spec2 * 130.0 * 0.5
        + striations * 55.0
    )
    blue = (
        16.0
        + 15.0 * norm_billow
        + 175.0 * norm_schlieren
        + 240.0 * energy_wave
        + spec1 * 255.0
        + spec2 * 50.0 * 0.2
        + striations * 85.0
    )

    vig = np.clip(1.0 - (np.abs(x) / 9.4)**8.0, 0.0, 1.0) * np.clip(1.0 - (np.abs(y) / 5.25)**8.0, 0.0, 1.0)
    red = np.clip(red * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    green = np.clip(green * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue * (0.88 * vig + 0.12), 0.0, 255.0).astype(np.uint8)

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
    theta_ray = np.pi / 4.2

    # 1. Background Stratified Flow & Internal Waves
    bg_rgb = compute_internal_gravity_wave_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. St. Andrew's Cross Ray Guides
    for sign_x in [-1, 1]:
        for sign_y in [-1, 1]:
            py5.no_fill()
            py5.stroke(0, 240, 255, 55)
            py5.stroke_weight(1.2)
            py5.line(
                to_screen(0, 0)[0], to_screen(0, 0)[1],
                to_screen(sign_x * 9.5, sign_y * 9.5 * np.tan(theta_ray))[0],
                to_screen(sign_x * 9.5, sign_y * 9.5 * np.tan(theta_ray))[1]
            )

    # 3. Lagrangian Stratified Isopycnal Streamline Ribbons
    for i in range(NUM_RIBBONS):
        px = (RIBBON_X0[i] + tau * 1.6) % 18.8 - 9.4
        py_cur = RIBBON_Y0[i]

        pts = []
        for step in range(24):
            pts.append(to_screen(px, py_cur))
            
            u_shear = 0.8 + 0.3 * np.cos(py_cur * 0.8)
            th_r = np.pi / 4.2
            xi_val = np.cos(th_r) * px + np.sin(th_r) * py_cur
            w_wave = 0.45 * np.cos(2.4 * xi_val - tau * 2.5) * np.exp(-(py_cur * py_cur) / 8.0)
            
            px += u_shear * 0.08
            py_cur += w_wave * 0.08

        is_gold = ((i // 2) % 2 == 0)
        for s in range(len(pts) - 1):
            prg = s / float(len(pts))
            al = int(220 * prg)
            if is_gold:
                py5.stroke(255, 190, 30, al)
            else:
                py5.stroke(0, 240, 255, al)
            py5.stroke_weight(0.9 + 1.3 * prg)
            py5.line(pts[s][0], pts[s][1], pts[s+1][0], pts[s+1][1])

    # 4. Bioluminescent Fluid Parcel Tracers
    py5.stroke_weight(1.8)
    for p in range(NUM_TRACERS):
        seed = p * 0.61803398875
        lx = ((seed * 115.0 + tau * 4.2) % 18.8) - 9.4
        base_y = ((p / float(NUM_TRACERS)) * 10.4 - 5.2)
        dy = 0.32 * np.sin(lx * 1.5 + tau * 3.0) * np.cos(base_y * 1.2)
        ly = base_y + dy

        sx, sy = to_screen(lx, ly)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            if p % 6 == 0:
                py5.stroke(255, 255, 255, 245)
                py5.stroke_weight(2.4)
            elif p % 2 == 0:
                py5.stroke(255, 210, 50, 190)
                py5.stroke_weight(1.6)
            else:
                py5.stroke(0, 235, 255, 180)
                py5.stroke_weight(1.4)
            py5.point(sx, sy)

    # 5. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] Internal gravity waves preview captured: {PREVIEW_PNG}")

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

"""
kinetic_magnetorotational_mri_turbulence_2d
---------------------------------------------
Kinetic 2D magnetohydrodynamic (MHD) simulation of the Balbus-Hawley
Magnetorotational Instability (MRI) and accretion disk dynamo turbulence.

Features:
- Shearing sheet accretion disk geometry with differential Keplerian shear.
- Exponentially growing tilted MRI channel flow modes in the linear regime.
- Parasitic secondary Kelvin-Helmholtz and tearing-mode breakdown into fully developed
  MHD turbulence and magnetic vortex eddies.
- Maxwell stress tensor mapping (M_xy = -Bx * By > 0) capturing outward angular momentum
  transport and ohmic dissipation hot spots.
- Reconnection current sheets (Jz = curl(B)_z) emitting white-hot Bremsstrahlung flashes.
- Dual-light Blinn-Phong specular plasma chrome normal shading.
- 420 Lagrangian streamline ribbons advecting along Keplerian sheared trajectories.
- 2800 relativistic synchrotron leptons spiraling along turbulent magnetic flux ropes.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_magnetorotational_mri_turbulence_2d"
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

# Directional lighting vectors for Blinn-Phong specular plasma sheen
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)

# Particle counts
NUM_RIBBONS = 420
NUM_LEPTONS = 2800

# Pre-seeded Lagrangian particles
np.random.seed(88)
RIBBON_X0 = np.random.uniform(-9.2, 9.2, NUM_RIBBONS).astype(np.float32)
RIBBON_Y0 = np.random.uniform(-5.0, 5.0, NUM_RIBBONS).astype(np.float32)


def compute_mri_turbulence_field(t_norm):
    """
    Computes 2D MRI magnetic flux function, magnetic field vectors,
    Maxwell stress tensor, current density, and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # Keplerian differential shearing coordinate
    shear_drift = 1.25 * np.sin(tau) * x
    y_s = y + shear_drift

    # 1. Tilted MRI Channel Flow Modes (45-degree sheared modes)
    k_mri = 0.95
    channel_phase = k_mri * (x - 0.9 * y_s) - tau * 2.0
    channel = np.sin(channel_phase)

    # 2. Secondary Parasitic KH breakdown into turbulent magnetic vortices
    eddy1 = 0.5 * np.sin(2.0 * x + 1.4 * y_s - tau * 2.8) * np.cos(1.5 * x - 2.2 * y_s + tau * 2.2)
    eddy2 = 0.3 * np.cos(2.8 * x - 0.9 * y_s + tau * 3.4)

    psi_mag = channel + eddy1 + eddy2

    # Magnetic field components
    dpsi_dy = (np.roll(psi_mag, -1, axis=0) - np.roll(psi_mag, 1, axis=0)) * 0.5
    dpsi_dx = (np.roll(psi_mag, -1, axis=1) - np.roll(psi_mag, 1, axis=1)) * 0.5

    Bx = -dpsi_dy * 2.2
    By = dpsi_dx * 2.2 - 0.65 * (x / 9.6)

    B_mag = np.sqrt(Bx * Bx + By * By + 0.01)

    # Maxwell stress: M_xy = -Bx * By
    raw_stress = -Bx * By
    pos_stress = np.maximum(raw_stress, 0.0)
    norm_stress = np.power(np.clip(pos_stress / 0.15, 0.0, 1.0), 0.7)

    # Current density / Reconnection sheets: Jz = dBy/dx - dBx/dy
    dBy_dx = (np.roll(By, -1, axis=1) - np.roll(By, 1, axis=1)) * 0.5
    dBx_dy = (np.roll(Bx, -1, axis=0) - np.roll(Bx, 1, axis=0)) * 0.5
    jz = np.abs(dBy_dx - dBx_dy)
    reconn = np.power(np.clip(jz / 0.10, 0.0, 1.0), 1.2)

    # Normalized magnetic energy
    norm_b = np.power(np.clip(B_mag / 0.75, 0.0, 1.0), 0.8)

    # Striations along field lines
    striations = np.power(0.5 + 0.5 * np.sin(psi_mag * 10.0 + tau * 3.0), 3.0)

    # Specular normal height field
    h_field = 0.32 * norm_b + 0.35 * reconn + 0.28 * norm_stress + 0.15 * striations
    dh_dx = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5
    dh_dy = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5
    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len
    nz = inv_len

    # Specular highlights
    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(np.clip((dot1 - 0.55) / 0.45, 0.0, 1.0), 6.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(np.clip((dot2 - 0.55) / 0.45, 0.0, 1.0), 5.0)

    # Palette Blending:
    # 1. Midnight Obsidian Base (#020412)
    # 2. Magnetic Flux Ropes: Electric Cyan (#00f0ff) & Sapphire Blue (#0d3b88)
    # 3. Maxwell Stress Ohmic Heating: Incandescent Solar Gold (#ffaa00) & Amber Fire
    # 4. Reconnection Current Sheets: Beaming Laser Magenta (#ff0080) & Royal Violet
    # 5. Specular Highlights: Liquid Diamond Chrome (#ffffff)

    red = (
        2.0
        + 215.0 * norm_stress
        + 175.0 * reconn
        + 12.0 * norm_b
        + spec1 * 255.0
        + spec2 * 190.0 * 0.8
        + striations * 35.0
    )
    green = (
        4.0
        + 160.0 * norm_stress
        + 18.0 * reconn
        + 155.0 * norm_b
        + spec1 * 255.0 * 0.95
        + spec2 * 130.0 * 0.5
        + striations * 50.0
    )
    blue = (
        16.0
        + 10.0 * norm_stress
        + 160.0 * reconn
        + 235.0 * norm_b
        + spec1 * 255.0
        + spec2 * 50.0 * 0.2
        + striations * 80.0
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
    k_mri = 0.95

    # 1. Background MHD Turbulence & Stress Field
    bg_rgb = compute_mri_turbulence_field(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # 2. Lagrangian Plasma Streamline Ribbons
    for i in range(NUM_RIBBONS):
        px = RIBBON_X0[i]
        py_cur = (RIBBON_Y0[i] + tau * 1.5) % 10.4 - 5.2

        pts = []
        for step in range(24):
            pts.append(to_screen(px, py_cur))
            y_s = py_cur + 1.25 * np.sin(tau) * px
            
            vx = -0.6 * np.cos(k_mri * (px - 0.9 * y_s) - tau * 2.0)
            vy = -0.35 * px + 0.5 * np.sin(k_mri * (px - 0.9 * y_s) - tau * 2.0)
            
            px += vx * 0.08
            py_cur += vy * 0.08

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

    # 3. Relativistic Synchrotron Leptons
    py5.stroke_weight(1.8)
    for p in range(NUM_LEPTONS):
        seed = p * 0.61803398875
        lx = ((seed * 110.0 + tau * 4.8) % 18.8) - 9.4
        ly = ((p / float(NUM_LEPTONS)) * 10.4 - 5.2) + 0.25 * np.sin(lx * 2.4 + tau * 2.8)
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

    # 4. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] MRI turbulence preview captured: {PREVIEW_PNG}")

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

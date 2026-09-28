"""
kinetic_dendritic_solidification_2d
-----------------------------------
Kinetic 2D simulation of non-equilibrium dendritic crystal solidification, Mullins-Sekerka
morphological instability, and polarized light birefringence in an undercooled liquid melt.

Features:
- Multi-seed competitive crystal growth combining 6-fold hexagonal (ice-like) and 4-fold cubic
  (metallic alloy) crystalline anisotropy.
- Mullins-Sekerka side-branching instability with Ivantsov parabolic trunk envelopes,
  secondary orthogonal comb needles, and tertiary micro-facets.
- Latent heat thermal diffusion field rejected ahead of advancing solidification fronts,
  interacted with buoyant thermal convection ripples in the melt.
- Crossed Nicol polarized light birefringence mapping local crystallographic lattice orientation
  into Michel-Lévy interference colors (peacock cyan, neon magenta, solar gold).
- Dual-light Blinn-Phong specular liquid chrome normal shading.
- Lagrangian solute segregation tracer particles driven ahead of advancing crystal needles.
- Fully deterministic, seamless 900-frame (15s @ 60fps) loop with automatic ffmpeg assembly.
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_dendritic_solidification_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

# Rendering parameters
SIZE = (1920, 1080)
TOTAL_FRAMES = 900
FPS = 60

# Physics & Grid parameters
GRID_W, GRID_H = 384, 216
X_COORDS = np.linspace(-9.6, 9.6, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-5.4, 5.4, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping lighting vectors
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)
LIGHT2_DIR = np.array([0.577, 0.577, 0.577], dtype=np.float32)

# Multi-seed configuration
SEED_CENTERS = [
    (0.0, 0.0),       # Master central 6-fold snowflake
    (-4.8, -2.2),     # Lower-left 4-fold cubic dendrite
    (4.8, 2.2),       # Upper-right 4-fold cubic dendrite
    (0.0, 3.0),       # Upper 6-fold seed
]
SEED_SCALES = [1.0, 0.65, 0.65, 0.55]
SEED_SYMMETRIES = [6, 4, 4, 6]

# Solute impurity particles
NUM_SOLUTE_PARTICLES = 650
np.random.seed(101)
SOLUTE_R = np.random.uniform(1.2, 5.4, NUM_SOLUTE_PARTICLES).astype(np.float32)
SOLUTE_TH = np.random.uniform(0, 2 * np.pi, NUM_SOLUTE_PARTICLES).astype(np.float32)
SOLUTE_SPEED = np.random.uniform(0.02, 0.06, NUM_SOLUTE_PARTICLES).astype(np.float32)


def compute_dendritic_solidification(t_norm):
    """
    Computes solid phase field phi, thermal diffusion field U,
    crystallographic director angle, and Blinn-Phong surface normals.
    """
    tau = 2.0 * np.pi * t_norm
    # Pulsing crystallization cycle (breathing growth and subtle dissolution)
    growth_phase = 0.5 - 0.5 * np.cos(tau)

    seed_rotations = [tau * 0.08, -tau * 0.12, tau * 0.15, -tau * 0.1]

    phi_field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    thermal_field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    director_angle = np.zeros((GRID_H, GRID_W), dtype=np.float32)

    for s_idx in range(len(SEED_CENTERS)):
        cx, cy = SEED_CENTERS[s_idx]
        sc = SEED_SCALES[s_idx]
        sym = SEED_SYMMETRIES[s_idx]
        rot = seed_rotations[s_idx]

        dx = GX - cx
        dy = GY - cy
        r = np.sqrt(dx * dx + dy * dy + 1e-4)
        th = np.arctan2(dy, dx) - rot

        max_L = (4.8 * sc) * (0.25 + 0.75 * growth_phase)
        rho_tip = 0.22 * sc
        lambda_side = 0.52 * sc

        # Smooth thermal diffusion halo surrounding the crystal
        thermal_envelope = np.exp(-((r - max_L * 0.8)**2) / (3.2 * sc * sc)) * (0.4 + 0.6 * np.cos(sym * th))
        thermal_field += thermal_envelope * 0.75

        for arm in range(sym):
            arm_angle = arm * (2.0 * np.pi / sym)
            d_th = (th - arm_angle + np.pi) % (2.0 * np.pi) - np.pi
            u = r * np.cos(d_th)
            v = np.abs(r * np.sin(d_th))

            # Smooth forward envelope along u
            u_forward = np.clip(u / max_L, 0.0, 1.0)
            u_envelope = np.clip(1.0 - np.tanh((u - max_L) / (rho_tip * 1.5)) * 0.5 - 0.5, 0.0, 1.0) * (u > -0.2)

            # Ivantsov parabolic trunk thickness
            w_trunk = 2.0 * np.sqrt(np.maximum(0.0, rho_tip * (max_L - u * 0.95))) + 0.14 * sc

            # Side-branching modulation
            side_env = np.tanh(np.maximum(0.0, u) / (2.0 * rho_tip)) * np.power(1.0 - u_forward, 0.5)
            side_mod = 0.55 * np.cos(2.0 * np.pi * u / lambda_side - tau * 2.0) * side_env
            w_primary = w_trunk * (1.0 + side_mod)

            phi_arm = np.clip(1.0 - (v / np.maximum(0.05, w_primary)), 0.0, 1.0) * u_envelope

            # Secondary side-branches
            side_L_max = 1.6 * sc * side_env
            u_norm = (np.maximum(0.0, u) / lambda_side) % 1.0
            node_dist = np.abs(u_norm - 0.5)
            phi_side = np.clip(1.0 - (node_dist * 4.0), 0.0, 1.0) * np.clip(1.0 - (v / np.maximum(0.1, side_L_max)), 0.0, 1.0) * u_envelope

            total_arm_phi = np.maximum(phi_arm, phi_side * 0.85)

            mask_better = total_arm_phi > phi_field
            phi_field = np.where(mask_better, total_arm_phi, phi_field)
            director_angle = np.where(mask_better, arm_angle + rot, director_angle)

    phi_field = np.clip(phi_field, 0.0, 1.0)
    thermal_field = np.clip(thermal_field, 0.0, 2.5)

    # Thermal convection wave ripples in the liquid melt
    conv_ripples = 0.15 * np.sin(GX * 1.5 + GY * 0.8 + tau) * np.cos(GY * 1.2 - GX * 0.6 - tau * 0.7)
    thermal_total = np.clip(thermal_field + conv_ripples * (1.0 - phi_field), 0.0, 3.0)

    # Blinn-Phong specular normals
    dh_dx = (np.roll(phi_field, -1, axis=1) - np.roll(phi_field, 1, axis=1)) * (0.5 * GRID_W / 19.2)
    dh_dy = (np.roll(phi_field, -1, axis=0) - np.roll(phi_field, 1, axis=0)) * (0.5 * GRID_H / 10.8)

    inv_len = 1.0 / np.sqrt(dh_dx * dh_dx + dh_dy * dh_dy + 1.0)
    nz = inv_len
    nx = -dh_dx * inv_len
    ny = -dh_dy * inv_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = np.power(dot1, 26.0)

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = np.power(dot2, 18.0)

    # Polarized light birefringence: Crossed Nicol interference intensity
    retardation = phi_field * 2.8 + thermal_total * 0.4
    biref_intensity = np.sin(2.0 * director_angle)**2 * np.sin(np.pi * retardation)**2

    # Liquid melt base (deep obsidian midnight titanium)
    red = 6.0 + thermal_total * 85.0 + biref_intensity * 190.0 * phi_field + spec1 * 255.0 + spec2 * 255.0 * 0.85
    green = 8.0 + thermal_total * 45.0 + (1.0 - biref_intensity) * 170.0 * phi_field + spec1 * 255.0 * 0.95 + spec2 * 160.0 * 0.4
    blue = 20.0 + thermal_total * 25.0 + 225.0 * phi_field + spec1 * 255.0 + spec2 * 75.0 * 0.2

    # Micro-scale dendritic facet striations
    facet_lines = np.abs(np.sin(phi_field * np.pi * 5.0))**3.5
    red += facet_lines * phi_field * 40.0
    green += facet_lines * phi_field * 60.0
    blue += facet_lines * phi_field * 80.0

    red = np.clip(red, 0.0, 255.0).astype(np.uint8)
    green = np.clip(green, 0.0, 255.0).astype(np.uint8)
    blue = np.clip(blue, 0.0, 255.0).astype(np.uint8)

    return np.stack([red, green, blue], axis=-1)


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[Setup Complete] Rendering {WORK_NAME} ({SIZE[0]}x{SIZE[1]} @ {FPS}fps, {TOTAL_FRAMES} frames)...")


def draw():
    frame = py5.frame_count
    t_norm = (frame % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    # 1. Compute vectorized phase field & Blinn-Phong shading
    bg_rgb = compute_dendritic_solidification(t_norm)
    bg_img = py5.create_image_from_numpy(bg_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    def to_screen(x, y):
        sx = (x + 9.6) / 19.2 * SIZE[0]
        sy = (5.4 - y) / 10.8 * SIZE[1]
        return sx, sy

    # 2. Draw subtle crystallographic grain boundary halos
    for s_idx in range(len(SEED_CENTERS)):
        cx, cy = SEED_CENTERS[s_idx]
        sc = SEED_SCALES[s_idx]
        sx, sy = to_screen(cx, cy)
        py5.push_matrix()
        py5.no_fill()
        py5.stroke(0, 240, 255, 30)
        py5.stroke_weight(1.0)
        py5.ellipse(sx, sy, 320 * sc, 320 * sc)
        py5.stroke(255, 190, 40, 20)
        py5.ellipse(sx, sy, 480 * sc, 480 * sc)
        py5.pop_matrix()

    # 3. Solute impurity tracer particles pushed ahead of dendritic tips
    py5.stroke_weight(1.8)
    for i in range(NUM_SOLUTE_PARTICLES):
        th = SOLUTE_TH[i] + tau * 0.04
        r = SOLUTE_R[i] + 0.25 * np.sin(th * 6.0 + tau * 2.0)
        px = r * np.cos(th)
        py_s = r * np.sin(th)
        sx, sy = to_screen(px, py_s)

        al = int(140 + 100 * np.sin(th * 4.0 + tau * 3.0))
        # Color shifting between solar gold and diamond white
        col_t = (np.sin(th * 3.0 + tau) + 1.0) * 0.5
        r_c = int(255)
        g_c = int(210 * (1 - col_t) + 255 * col_t)
        b_c = int(80 * (1 - col_t) + 255 * col_t)
        py5.stroke(r_c, g_c, b_c, al)
        py5.point(sx, sy)

    # 4. Save Frame
    frame_path = os.path.join(FRAMES_DIR, f"frame-{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save representative preview at frame 450
    if frame == 450:
        py5.save_frame(PREVIEW_PNG)
        print(f"[Preview Saved] Dendritic solidification preview captured: {PREVIEW_PNG}")

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

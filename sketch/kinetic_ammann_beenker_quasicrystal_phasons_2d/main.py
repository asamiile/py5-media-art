"""
kinetic_ammann_beenker_quasicrystal_phasons_2d
Aperiodic octagonal Ammann-Beenker quasicrystal tessellation dancing through
non-periodic phason strain waves and topological tile-flip bifurcations on deep midnight basalt vellum.

Anti-Clustering Compliance:
- Genre: Mathematical / Abstract Topology (Zero physics particle tracers / zero organic growth)
- Background: Deep Midnight Basalt & Obsidian Drafting Ground (#090c14)
- Primitives: Solid geometric cloisonné polygonal tiles (45-degree rhombuses & squares),
  concentric faceted insets, 8-fold star rosette cabochons, Ammann coordinate grids. NO particles.
- Palette: Deep Midnight Basalt (#090c12), Royal Cobalt (#142858), Electric Sapphire (#2563eb),
  Platinum White-Gold (#e2e8f0 / #f8fafc), Warm Copper Vermilion (#ea580c), Solar Amber Gold (#fbbf24).
- Anonymity: Strictly 100% autonomous algorithmic art with ZERO signatures, name seals (落款), or personal marks.

Format: 720 frames @ 60 FPS (12.0s seamless loop)
Native Output: 3840x2160 (4K master)
"""

import os
import shutil
import subprocess
import sys
import time
import numpy as np
import py5

# Master 4K Canvas Resolution
WIDTH, HEIGHT = 3840, 2160
TOTAL_FRAMES = 720
FPS = 60

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_NAME = os.path.basename(WORK_DIR)
FRAMES_DIR = os.path.join(WORK_DIR, "frames")
PREVIEW_PATH = os.path.join(WORK_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_VIDEO = os.path.join(WORK_DIR, f"{WORK_NAME}.mp4")

# Quasicrystal Geometry Parameters
CX = WIDTH * 0.5
CY = HEIGHT * 0.5
D_GRID = 158.0   # 4-grid line spacing
S_TILE = 90.0    # Tile edge size in 4K pixels

# Base angles of the 4 grid families: 0, 45, 90, 135 degrees
BASE_ANGLES = np.array([0, 1, 2, 3], dtype=np.float64) * (np.pi / 4.0)

# Precomputed integer line indices for multigrid evaluation
N_RANGE = np.arange(-14, 15)
NJ_GRID, NK_GRID = np.meshgrid(N_RANGE, N_RANGE)
NJ_FLAT = NJ_GRID.ravel()
NK_FLAT = NK_GRID.ravel()


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)


def compute_tiling(frame_idx):
    """
    Evaluates de Bruijn's dual multigrid for Ammann-Beenker octagonal quasicrystal.
    Returns categorized quadrilaterals (outer bodies, inner insets, centroids, star vertices).
    """
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phase = 2.0 * np.pi * t_norm

    # Harmonic 4D phason orbit (strictly periodic over TOTAL_FRAMES)
    amp1 = 0.26
    amp2 = 0.08
    gamma = np.array([
        amp1 * np.cos(phase) + amp2 * np.sin(2.0 * phase),
        amp1 * np.cos(phase + np.pi * 0.5) - amp2 * np.cos(2.0 * phase),
        amp1 * np.cos(phase + np.pi) + amp2 * np.sin(2.0 * phase),
        amp1 * np.cos(phase + np.pi * 1.5) - amp2 * np.cos(2.0 * phase),
    ], dtype=np.float64)

    # Subtle harmonic rotational breathing: +/- 1.4 degrees
    rot_angle = 0.024 * np.sin(phase)
    angles_rot = BASE_ANGLES + rot_angle
    e = np.stack([np.cos(angles_rot), np.sin(angles_rot)], axis=-1)  # (4, 2)

    # Subtle dynamic scale breathing: +/- 2.5%
    s_tile_dyn = S_TILE * (1.0 + 0.025 * np.cos(phase))

    sq_quads = []
    sq_insets = []
    sq_centers = []

    rh_quads = []
    rh_insets = []
    rh_centers = []

    for j in range(4):
        for k in range(j + 1, 4):
            det = e[j, 0] * e[k, 1] - e[j, 1] * e[k, 0]
            if abs(det) < 1e-6:
                continue

            inv_00 = e[k, 1] / det
            inv_01 = -e[j, 1] / det
            inv_10 = -e[k, 0] / det
            inv_11 = e[j, 0] / det

            diff = (k - j) % 4
            is_square = (diff == 2)

            c_j = (NJ_FLAT - gamma[j]) * D_GRID
            c_k = (NK_FLAT - gamma[k]) * D_GRID

            # Intersection points p in multigrid plane
            px = inv_00 * c_j + inv_01 * c_k
            py = inv_10 * c_j + inv_11 * c_k

            # Dual 4D lattice index K_m for m=0..3
            K = np.zeros((len(px), 4), dtype=np.float64)
            for m in range(4):
                if m == j:
                    K[:, m] = NJ_FLAT
                elif m == k:
                    K[:, m] = NK_FLAT
                else:
                    val = (px * e[m, 0] + py * e[m, 1]) / D_GRID + gamma[m]
                    K[:, m] = np.ceil(val)

            # Dual vertex position V = sum(K_m * e_m) * s_tile
            vx = (K @ e[:, 0]) * s_tile_dyn + CX
            vy = (K @ e[:, 1]) * s_tile_dyn + CY

            # Centroid of tile
            cent_x = vx + 0.5 * (e[j, 0] + e[k, 0]) * s_tile_dyn
            cent_y = vy + 0.5 * (e[j, 1] + e[k, 1]) * s_tile_dyn

            # Generous bounding box filter to ensure airtight coverage across all angles
            mask = (cent_x > -260) & (cent_x < WIDTH + 260) & (cent_y > -260) & (cent_y < HEIGHT + 260)

            vx_m = vx[mask]
            vy_m = vy[mask]
            cx_m = cent_x[mask]
            cy_m = cent_y[mask]

            v0 = np.stack([vx_m, vy_m], axis=-1)
            v1 = v0 + e[j] * s_tile_dyn
            v2 = v0 + (e[j] + e[k]) * s_tile_dyn
            v3 = v0 + e[k] * s_tile_dyn

            quads = np.stack([v0, v1, v2, v3], axis=1)  # (M, 4, 2)

            # Inset facet: 28% contraction toward centroid
            c_stacked = np.stack([cx_m, cy_m], axis=-1)[:, np.newaxis, :]
            insets = quads * 0.72 + c_stacked * 0.28

            if is_square:
                sq_quads.append(quads)
                sq_insets.append(insets)
                sq_centers.append(np.stack([cx_m, cy_m], axis=-1))
            else:
                rh_quads.append(quads)
                rh_insets.append(insets)
                rh_centers.append(np.stack([cx_m, cy_m], axis=-1))

    sq_all = np.concatenate(sq_quads, axis=0)
    sq_in_all = np.concatenate(sq_insets, axis=0)
    sq_c_all = np.concatenate(sq_centers, axis=0)

    rh_all = np.concatenate(rh_quads, axis=0)
    rh_in_all = np.concatenate(rh_insets, axis=0)
    rh_c_all = np.concatenate(rh_centers, axis=0)

    return sq_all, sq_in_all, sq_c_all, rh_all, rh_in_all, rh_c_all, rot_angle, phase


def draw_frame(frame_idx):
    sq_all, sq_in_all, sq_c_all, rh_all, rh_in_all, rh_c_all, rot_angle, phase = compute_tiling(frame_idx)

    # 1. PASS 1: Midnight Basalt Canvas & Ambient Deep Sapphire Glow
    py5.background(9, 12, 18)

    # Radial ambient sapphire glow
    py5.no_stroke()
    for r_step in range(14, 0, -1):
        rad = r_step * 150.0
        alpha = int(7.0 * (1.0 - r_step / 14.0))
        py5.fill(24, 48, 108, alpha)
        py5.circle(CX, CY, rad * 2)

    # Octagonal calibration geometry rings & radian tick marks
    py5.no_fill()
    py5.stroke(56, 189, 248, 26)  # Glacial Cyan
    py5.stroke_weight(1.0)
    for ring_r in [320, 680, 1080, 1500]:
        py5.circle(CX, CY, ring_r * 2)
        for a_idx in range(8):
            ang = a_idx * (np.pi / 4.0) + rot_angle
            x1 = CX + (ring_r - 14) * np.cos(ang)
            y1 = CY + (ring_r - 14) * np.sin(ang)
            x2 = CX + (ring_r + 14) * np.cos(ang)
            y2 = CY + (ring_r + 14) * np.sin(ang)
            py5.line(x1, y1, x2, y2)

    # 2. PASS 2: Outer Chamfered Tile Bodies
    # Squares: Royal Celestial Cobalt (#142858)
    py5.fill(18, 38, 88, 240)
    py5.stroke(10, 18, 42, 220)
    py5.stroke_weight(2.4)
    py5.begin_shape(py5.QUADS)
    for q in sq_all:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()

    # Rhombuses: Platinum White-Gold (#e2e8f0)
    py5.fill(228, 233, 242, 250)
    py5.stroke(51, 65, 85, 220)
    py5.stroke_weight(2.4)
    py5.begin_shape(py5.QUADS)
    for q in rh_all:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()

    # 3. PASS 3: Inner Inset Jewelry Facets
    # Squares Inset: Electric Sapphire (#2563eb)
    py5.fill(37, 99, 235, 235)
    py5.stroke(96, 165, 250, 180)
    py5.stroke_weight(1.4)
    py5.begin_shape(py5.QUADS)
    for q in sq_in_all:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()

    # Rhombuses Inset: Lustrous Mother-of-Pearl Silver (#f8fafc)
    py5.fill(248, 250, 252, 245)
    py5.stroke(203, 213, 225, 200)
    py5.stroke_weight(1.4)
    py5.begin_shape(py5.QUADS)
    for q in rh_in_all:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()

    # 4. PASS 4: Central Solar Amber & Copper Vermilion Cabochon Nodes on Squares
    dists_sq = np.hypot(sq_c_all[:, 0] - CX, sq_c_all[:, 1] - CY)
    mask_dots = dists_sq < 1450.0
    py5.no_stroke()
    for pt, d_val in zip(sq_c_all[mask_dots], dists_sq[mask_dots]):
        fade = np.clip(1.0 - d_val / 1450.0, 0.0, 1.0)
        # Pulse brightness with local phason wave
        pulse = 0.85 + 0.15 * np.sin(phase * 2.0 + d_val * 0.004)
        alpha_base = int(240 * fade * pulse)

        # Outer copper-vermilion ring
        py5.fill(234, 88, 12, int(alpha_base * 0.75))
        py5.circle(pt[0], pt[1], 13.0)

        # Inner solar amber gold core
        py5.fill(251, 191, 36, alpha_base)
        py5.circle(pt[0], pt[1], 7.5)

        # Incandescent diamond center pearl
        if fade > 0.4:
            py5.fill(255, 255, 255, int(alpha_base * 0.9))
            py5.circle(pt[0], pt[1], 3.0)

    # 5. PASS 5: Subtle Optical Border Vignette
    py5.no_fill()
    for v_idx in range(16):
        v_rad = 1450.0 + v_idx * 50.0
        v_alpha = int(10 + v_idx * 15)
        py5.stroke(9, 12, 18, v_alpha)
        py5.stroke_weight(52.0)
        py5.circle(CX, CY, v_rad * 2)


def draw():
    print(f"Starting 4K render: {TOTAL_FRAMES} frames @ {FPS} fps...")
    start_time = time.time()

    for frame_idx in range(TOTAL_FRAMES):
        t0 = time.time()
        draw_frame(frame_idx)
        frame_path = os.path.join(FRAMES_DIR, f"frame_{frame_idx:04d}.png")
        py5.save_frame(frame_path)

        # Save preview still at frame 360 (50% midpoint)
        if frame_idx == TOTAL_FRAMES // 2:
            py5.save_frame(PREVIEW_PATH)
            print(f"  [Preview] Saved preview still to {PREVIEW_PATH}")

        dt = time.time() - t0
        if frame_idx % 60 == 0 or frame_idx == TOTAL_FRAMES - 1:
            elapsed = time.time() - start_time
            fps_render = (frame_idx + 1) / elapsed if elapsed > 0 else 0
            eta = (TOTAL_FRAMES - frame_idx - 1) / fps_render if fps_render > 0 else 0
            print(f"  Frame {frame_idx + 1}/{TOTAL_FRAMES} ({dt:.2f}s) | Avg FPS: {fps_render:.2f} | ETA: {eta:.0f}s")

    total_time = time.time() - start_time
    print(f"Render completed in {total_time:.1f}s. Compiling MP4 video...")

    # Compile MP4 via FFmpeg with seamless loop flag
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Successfully generated video: {OUTPUT_VIDEO}")

    # Clean up frames directory to preserve disk space
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
        print("Cleaned up frames directory.")

    print("All tasks completed cleanly. Exiting.")
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

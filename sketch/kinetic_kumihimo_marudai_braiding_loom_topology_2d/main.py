"""
Kinetic Kumihimo Marudai Braiding Loom & Braid-Group Topology 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Textile / Calligraphy / Procedural Craft genre,
exploring traditional Japanese Kumihimo (Marudai 24-Tama silk-and-gold braiding) and
Emil Artin's Braid Group B_24 topological choreography (Heian-Edo Yusoku Kumihimo;
Domyo Kyoto; Emil Artin 1925 Theorie der Zopfe), executed on deep Kyoto Urushi
black-indigo lacquer (#060912).

Around the polished circular Kagami (mirror) disk of a traditional wooden Marudai stand,
24 weighted wooden bobbins (Tama) arranged in 8 counter-rotating triad groups orbit and
exchange slots along coupled epicyclic trajectories. Each Tama feeds a multi-ply twisted
silk or Kinshi (gold-leaf wrapped paper) cord radially inward across the Kagami edge and
down into the central Heso (navel) aperture under the tension of a suspended brass
Omori counterweight. By sorting the radial silk ribbons by their instantaneous Artin
generator crossing height z_i(r, tau) and rendering each cord as a 3D cylindrical
multi-filament ribbon with S/Z ply striations, the radial tension web condenses at the
center into an intricately interlocked 3D tubular Kongo-gumi & Karakumi brocade cord.

Completely free of human author signatures, seals (hanko), or watermarks.
"""

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import py5

# --- Artwork Constants ---
WORK_NAME = "kinetic_kumihimo_marudai_braiding_loom_topology_2d"
WIDTH = 3840
HEIGHT = 2160
FPS = 60
TOTAL_FRAMES = 720
DURATION_SEC = 12.0

SKETCH_DIR = Path(__file__).resolve().parent
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_FILE = SKETCH_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_MP4 = SKETCH_DIR / "output.mp4"

START_TIME = 0.0

# Non-fixed runtime phase seed (adhering to no-fixed-seed rule)
np.random.seed(int(time.time() * 1000) % 100000)
RND_BRAID_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_TENSION_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 22.0
LOOM_R = 805.0
KAGAMI_OUTER_R = 675.0
HESO_R = 238.0

# 24 Tama bobbins divided into two counter-rotating chiral families:
# S-family (+1 chirality, 12 bobbins) and Z-family (-1 chirality, 12 bobbins)
# With 6 traditional Kyoto Kusaki-zome & Kinshi silk dye colors:
# 0: Kinshi Burnished Gold Leaf (#f59e0b / #fde047)
# 1: Akane Madder Vermilion (#e11d48 / #fb7185)
# 2: Hon-Aizome Fermented Indigo (#2563eb / #60a5fa)
# 3: Neri-Ginu Degummed Pearl Silk (#cbd5e1 / #f8fafc)
# 4: Rokusho Malachite Celadon (#059669 / #34d399)
# 5: Murasaki Gromwell Amethyst (#7c3aed / #c084fc)
SILK_PALETTE = [
    # (shadow_rgb, body_rgb, crest_rgb, ply_rgb, name)
    ((92, 52, 8), (234, 158, 22), (254, 240, 138), (168, 102, 12), "KINSHI GOLD FOIL"),
    ((88, 14, 32), (225, 38, 76), (253, 164, 175), (148, 22, 48), "AKANE MADDER VERMILION"),
    ((16, 44, 102), (42, 118, 228), (147, 197, 253), (24, 72, 158), "HON-AIZOME INDIGO"),
    ((78, 92, 112), (212, 224, 238), (255, 255, 255), (138, 154, 178), "NERI-GINU PEARL SILK"),
    ((10, 68, 52), (18, 168, 124), (134, 239, 172), (14, 112, 84), "ROKUSHO CELADON"),
    ((56, 22, 98), (148, 72, 232), (216, 180, 254), (96, 38, 158), "MURASAKI AMETHYST"),
]

N_TAMA = 24
# Assign colors symmetrically so opposing chiral threads weave a rich 8-fold Karakumi / Kongo-gumi pattern
TAMA_COLOR_IDX = [
    0, 1, 2, 3, 4, 5,
    0, 2, 1, 4, 3, 5,
    0, 1, 2, 3, 4, 5,
    0, 2, 1, 4, 3, 5,
]


def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)


def setup():
    global START_TIME
    START_TIME = time.time()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES)
    omega = 2.0 * math.pi

    # 1. Deep Kyoto Urushi Black-Indigo Lacquer Ground (#060912)
    py5.background(6, 9, 18)

    # 2. Architectural Loom Drafting Grid & Subtle Radial Glow
    draw_urushi_substrate_and_grid(tau)

    # 3. Central Monumental Marudai 24-Tama Braiding Loom & Braid-Group Web
    draw_central_marudai_loom(tau, omega)

    # 4. Eight Kumihimo & Braid-Group Topology Apparatuses Across Four Flank Cards
    draw_kumihimo_topology_apparatuses(tau, omega)

    # 5. Outer Museum Border & Scholarly Typography (Zero Personal Signatures/Seals)
    draw_museum_border_and_typography(tau, omega)

    # Save sequential frame
    frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at frame 0
    if frame == 0:
        py5.save_frame(str(PREVIEW_FILE))
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_FILE}")

    if (frame + 1) % 60 == 0 or frame + 1 == TOTAL_FRAMES:
        elapsed = time.time() - START_TIME
        fps_calc = (frame + 1) / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - (frame + 1)) / max(0.01, fps_calc)
        print(
            f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | "
            f"Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s"
        )


def draw_urushi_substrate_and_grid(tau: float):
    """Draws the deep Urushi lacquer ambient glow and subtle precision loom coordinate lines."""
    py5.no_stroke()
    for r_g, col_g in [
        (1150, (12, 18, 34, 90)),
        (920, (18, 26, 48, 85)),
        (830, (24, 34, 62, 95)),
    ]:
        py5.fill(*col_g)
        py5.circle(CX, CY, r_g * 2.0)

    py5.stroke(22, 30, 50, 130)
    py5.stroke_weight(1.1)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)


def compute_tama_state(idx: int, tau: float, omega: float):
    """
    Computes the instantaneous polar position (r_tama, theta_tama) and crossing phase
    of Tama bobbin `idx` in [0..23] around the Marudai Kagami perimeter.
    Even indices belong to the S-chiral family (+1), odd indices to the Z-chiral family (-1).
    """
    chirality = 1 if (idx % 2 == 0) else -1
    base_ang = (idx / float(N_TAMA)) * 2.0 * math.pi + RND_BRAID_PHASE

    # Counter-rotating harmonic braiding drift + figure-eight epicyclic handover
    # Loops seamlessly over tau in [0, 1] because 2 * omega * tau = 4 * pi
    theta_tama = (
        base_ang
        + chirality * (omega * tau / 3.0 * 3.0)  # Exactly 1 full rotation per loop
        + 0.14 * math.sin(2.0 * omega * tau + idx * math.pi / 3.0)
    )
    r_tama = (
        KAGAMI_OUTER_R
        + 44.0 * chirality * math.cos(2.0 * omega * tau + idx * math.pi / 4.0)
        + 12.0 * math.sin(4.0 * omega * tau - idx * math.pi / 6.0)
    )
    # Vertical over-under shed elevation at the Kagami rim
    z_shed = chirality * math.sin(2.0 * omega * tau + idx * math.pi / 4.0)
    return r_tama, theta_tama, chirality, z_shed


def draw_central_marudai_loom(tau: float, omega: float):
    """
    Renders the central Marudai Circular Braiding Loom:
    1. Outer Hinoki & Vermilion/Black Urushi Lacquer Kagami (mirror) ring with 24 Kiri-komi slots
    2. Four structural Marudai cylindrical legs (Ashi) seen in foreshortened plan perspective
    3. Deep central Heso well with brass Omori counterweight suspension ring
    4. 24 depth-sorted multi-ply silk and Kinshi gold cords spanning from the Tama bobbins
       into the central Heso aperture with authentic 2-up/2-down helical interlacing
    5. Central 3D tubular Kongo-gumi / Karakumi braided cord (Kumi-age) emerging in the well
    6. 24 turned wooden Tama bobbins wound with silk and lead bands orbiting the rim
    """
    # --- 1. OUTER URUSHI LACQUER & HINOKI WOOD KAGAMI (MIRROR) RING ---
    py5.no_stroke()
    # Outer dark bronze-gold rim bezel
    py5.fill(38, 30, 18, 255)
    py5.circle(CX, CY, (LOOM_R + 18.0) * 2.0)

    # Vermilion-edged Negoro-nuri Urushi lacquer outer ring
    py5.fill(118, 24, 32, 245)
    py5.circle(CX, CY, LOOM_R * 2.0)

    # Polished Roiro black Urushi lacquer Kagami mirror deck
    py5.fill(14, 18, 28, 255)
    py5.circle(CX, CY, (LOOM_R - 14.0) * 2.0)

    # Hinoki wood grain concentric turning rings on the Kagami surface
    py5.no_fill()
    for r_wood in range(260, int(LOOM_R - 22), 18):
        alpha_w = 55 if (r_wood % 36 == 0) else 28
        py5.stroke(88, 68, 44, alpha_w)
        py5.stroke_weight(1.4)
        py5.circle(CX, CY, r_wood * 2.0)

    # Warm Hinoki wood inner Kagami table band (between r = 540 and r = 695)
    n_ring = 120
    ang_r = np.linspace(0.0, 2.0 * math.pi, n_ring + 1)
    cr_r, sr_r = np.cos(ang_r), np.sin(ang_r)
    for r_in_b, r_out_b, col_b in [
        (555.0, 695.0, (42, 32, 22, 210)),
        (575.0, 675.0, (58, 44, 28, 195)),
    ]:
        q_b = np.empty((n_ring, 4, 2), dtype=np.float64)
        q_b[:, 0, 0] = CX + r_in_b * cr_r[:-1]
        q_b[:, 0, 1] = CY + r_in_b * sr_r[:-1]
        q_b[:, 1, 0] = CX + r_out_b * cr_r[:-1]
        q_b[:, 1, 1] = CY + r_out_b * sr_r[:-1]
        q_b[:, 2, 0] = CX + r_out_b * cr_r[1:]
        q_b[:, 2, 1] = CY + r_out_b * sr_r[1:]
        q_b[:, 3, 0] = CX + r_in_b * cr_r[1:]
        q_b[:, 3, 1] = CY + r_in_b * sr_r[1:]
        py5.no_stroke()
        py5.fill(*col_b)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_b.reshape(-1, 2))

    # 24 Radial Kiri-komi (bobbin rest notches) & 360-degree graduation ticks
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        is_slot = (deg % 15 == 0)
        is_5 = (deg % 5 == 0)
        r0 = LOOM_R - (34.0 if is_slot else (22.0 if is_5 else 14.0))
        r1 = LOOM_R - 5.0
        py5.stroke(*(245, 188, 66, 220) if is_slot else (138, 118, 88, 135))
        py5.stroke_weight(2.4 if is_slot else 1.1)
        py5.line(CX + r0 * ca, CY + r0 * sa, CX + r1 * ca, CY + r1 * sa)

    # Four Marudai structural pillar bosses (Ashi) at 45, 135, 225, 315 degrees
    for p_deg in [45, 135, 225, 315]:
        pr = math.radians(p_deg)
        px = CX + 625.0 * math.cos(pr)
        py = CY + 625.0 * math.sin(pr)
        py5.fill(26, 20, 14, 240)
        py5.stroke(198, 148, 52, 200)
        py5.stroke_weight(2.0)
        py5.circle(px, py, 44.0)
        py5.fill(184, 134, 42, 220)
        py5.no_stroke()
        py5.circle(px, py, 16.0)

    # --- 2. CENTRAL HESO (NAVEL) APERTURE & OMORI COUNTERWEIGHT WELL ---
    py5.fill(5, 7, 14, 255)
    py5.stroke(214, 162, 54, 235)
    py5.stroke_weight(3.2)
    py5.circle(CX, CY, HESO_R * 2.0)

    # Smoothly rounded Hinoki wood lip of the Heso opening (Tori-guchi)
    py5.no_fill()
    for d_r, a_lip in [(8.0, 190), (16.0, 120), (24.0, 70)]:
        py5.stroke(238, 192, 98, a_lip)
        py5.stroke_weight(2.2)
        py5.circle(CX, CY, (HESO_R + d_r) * 2.0)

    # Concentric brass Omori counterweight gauge rings inside the Heso well
    for r_w, col_w in [
        (HESO_R - 22.0, (72, 96, 138, 160)),
        (HESO_R - 54.0, (198, 148, 48, 155)),
        (HESO_R - 92.0, (56, 158, 138, 150)),
    ]:
        py5.stroke(*col_w)
        py5.stroke_weight(1.5)
        py5.circle(CX, CY, r_w * 2.0)

    # --- 3. COMPUTE & DEPTH-SORT 24 MULTI-PLY SILK RIBBON SEGMENTS ---
    # Each cord spans from its outer Tama bobbin (r_tama, theta_tama) inward to the
    # central braided cord periphery (r_core = 108 px), curving along an Archimedean
    # tension spiral with over-under crossing waves.
    n_seg = 26
    u_arr = np.linspace(0.0, 1.0, n_seg + 1)  # u=0 at Heso core, u=1 at Tama bobbin
    r_core = 106.0

    tama_states = []
    ribbon_segments = []  # List of (z_depth, color_idx, chirality, seg_quad, crest_line, ply_lines)

    for idx in range(N_TAMA):
        r_tama, theta_tama, chirality, z_shed = compute_tama_state(idx, tau, omega)
        col_idx = TAMA_COLOR_IDX[idx]
        tama_states.append((idx, r_tama, theta_tama, chirality, z_shed, col_idx))

        # Radial coordinate along the silk strand from r_core to r_tama
        r_pts = r_core + (r_tama - r_core) * (u_arr ** 0.92)

        # Angular twist: at the outer Tama (u=1), angle is theta_tama;
        # as the cord enters the braiding zone (u -> 0), chirality imparts a helical twist
        # and an alternating 2-up / 2-down wave undulation
        twist_ang = (
            theta_tama
            + chirality * 0.48 * ((1.0 - u_arr) ** 1.25)
            + 0.045 * chirality * np.sin(5.0 * math.pi * u_arr - 2.0 * omega * tau + idx * math.pi / 6.0)
        )

        cx_pts = CX + r_pts * np.cos(twist_ang)
        cy_pts = CY + r_pts * np.sin(twist_ang)

        # Tangent and normal vectors along the strand
        dx = np.gradient(cx_pts)
        dy = np.gradient(cy_pts)
        d_len = np.hypot(dx, dy) + 1e-8
        nx = -dy / d_len
        ny = dx / d_len

        # Strand half-width tapers from 8.5 px near the Tama to 5.8 px entering the tight Heso knot
        half_w = 5.6 + 3.4 * u_arr

        # Instantaneous over-under vertical height z(u) for topological braiding order:
        # Combines the outer shed z_shed with the radial 2-up/2-down crossing wave
        z_vals = np.sin(
            3.5 * math.pi * u_arr
            - chirality * 2.0 * omega * tau
            + idx * (2.0 * math.pi / 8.0)
        )

        for s in range(n_seg):
            z_mid = float(0.5 * (z_vals[s] + z_vals[s + 1]))
            w0, w1 = half_w[s], half_w[s + 1]
            # Quad vertices for this ribbon segment
            x0L, y0L = cx_pts[s] - nx[s] * w0, cy_pts[s] - ny[s] * w0
            x0R, y0R = cx_pts[s] + nx[s] * w0, cy_pts[s] + ny[s] * w0
            x1R, y1R = cx_pts[s + 1] + nx[s + 1] * w1, cy_pts[s + 1] + ny[s + 1] * w1
            x1L, y1L = cx_pts[s + 1] - nx[s + 1] * w1, cy_pts[s + 1] - ny[s + 1] * w1

            # Centerline specular silk highlight
            c_line = (cx_pts[s], cy_pts[s], cx_pts[s + 1], cy_pts[s + 1])

            # Oblique S/Z twist ply striation across the segment
            if chirality > 0:
                p_line = (x0L, y0L, x1R, y1R)
            else:
                p_line = (x0R, y0R, x1L, y1L)

            ribbon_segments.append((
                z_mid,
                col_idx,
                (x0L, y0L, x0R, y0R, x1R, y1R, x1L, y1L),
                c_line,
                p_line,
            ))

    # Sort all 24 * 26 = 624 ribbon segments back-to-front by z_mid for authentic over-under crossing
    ribbon_segments.sort(key=lambda item: item[0])

    # Batch-render sorted segments in 12 depth slabs so over-under crossings occlude cleanly
    n_total_segs = len(ribbon_segments)
    n_slabs = 12
    slab_size = (n_total_segs + n_slabs - 1) // n_slabs

    for slab_i in range(n_slabs):
        slab = ribbon_segments[slab_i * slab_size : (slab_i + 1) * slab_size]
        if not slab:
            continue

        # Group within slab by color_idx
        by_col = {}
        for z_m, c_idx, q_coords, c_ln, p_ln in slab:
            by_col.setdefault(c_idx, []).append((z_m, q_coords, c_ln, p_ln))

        for c_idx, items in by_col.items():
            sh_rgb, body_rgb, crest_rgb, ply_rgb, _ = SILK_PALETTE[c_idx]
            n_it = len(items)
            q_arr = np.empty((n_it, 4, 2), dtype=np.float64)
            c_segs = np.empty((n_it, 4), dtype=np.float64)
            p_segs = np.empty((n_it, 4), dtype=np.float64)

            for k, (z_m, qc, cl, pl) in enumerate(items):
                q_arr[k, 0, 0], q_arr[k, 0, 1] = qc[0], qc[1]
                q_arr[k, 1, 0], q_arr[k, 1, 1] = qc[2], qc[3]
                q_arr[k, 2, 0], q_arr[k, 2, 1] = qc[4], qc[5]
                q_arr[k, 3, 0], q_arr[k, 3, 1] = qc[6], qc[7]
                c_segs[k] = cl
                p_segs[k] = pl

            # Dark under-shadow border for tactile cord separation at crossings
            py5.stroke(6, 9, 18, 225)
            py5.stroke_weight(2.2)
            py5.fill(body_rgb[0], body_rgb[1], body_rgb[2], 248)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(q_arr.reshape(-1, 2))

            # Oblique S/Z ply twist line
            py5.stroke(ply_rgb[0], ply_rgb[1], ply_rgb[2], 210)
            py5.stroke_weight(1.5)
            py5.lines(p_segs)

            # Luminous silk specular spine
            py5.stroke(crest_rgb[0], crest_rgb[1], crest_rgb[2], 225)
            py5.stroke_weight(2.0)
            py5.lines(c_segs)

    # --- 4. CENTRAL 3D TUBULAR KONGO-GUMI / KARAKUMI BRAIDED CORD (KUMI-AGE) ---
    draw_central_braided_cord_rosette(tau, omega, r_core)

    # --- 5. 24 WEIGHTED WOODEN TAMA BOBBINS ORBITING THE KAGAMI PERIMETER ---
    draw_orbiting_tama_bobbins(tama_states, tau, omega)


def draw_central_braided_cord_rosette(tau: float, omega: float, r_core: float):
    """
    Renders the central emerging 3D Kongo-gumi / Karakumi braided cord inside the Heso well:
    - Outer brass tension collar with 24 micro-roller guides
    - 9 concentric interlocked diamond-chevron tiers representing the tubular braid descending
      downward into the counterweight well, shaded with 3D cylindrical foreshortening
    - Central suspended brass Omori hook spindle
    """
    # Brass Heso tension collar
    py5.no_fill()
    py5.stroke(234, 179, 58, 240)
    py5.stroke_weight(3.5)
    py5.circle(CX, CY, (r_core + 6.0) * 2.0)

    # 9 concentric tiers of 24 interlocking diamond braid facets (Kongo-gumi), batched by tier & color
    n_tiers = 9
    r_inner_well = 22.0
    s_indices = np.arange(N_TAMA, dtype=np.float64)
    da = math.pi / float(N_TAMA)

    for t_i in range(n_tiers):
        f0 = t_i / float(n_tiers)
        f1 = (t_i + 1) / float(n_tiers)
        r_out_t = r_core - (r_core - r_inner_well) * (f0 ** 0.85)
        r_mid_t = r_core - (r_core - r_inner_well) * (((f0 + f1) * 0.5) ** 0.85)
        r_in_t = r_core - (r_core - r_inner_well) * (f1 ** 0.85)

        rot_phase = omega * tau + t_i * (math.pi / 12.0)
        shade_scale = 1.0 - 0.52 * f0

        a_centers = (s_indices / float(N_TAMA)) * 2.0 * math.pi + rot_phase
        x_top = CX + r_out_t * np.cos(a_centers)
        y_top = CY + r_out_t * np.sin(a_centers)
        x_right = CX + r_mid_t * np.cos(a_centers + da)
        y_right = CY + r_mid_t * np.sin(a_centers + da)
        x_bot = CX + r_in_t * np.cos(a_centers)
        y_bot = CY + r_in_t * np.sin(a_centers)
        x_left = CX + r_mid_t * np.cos(a_centers - da)
        y_left = CY + r_mid_t * np.sin(a_centers - da)

        by_col_t = {}
        for s_i in range(N_TAMA):
            c_idx = TAMA_COLOR_IDX[(s_i + t_i) % N_TAMA]
            by_col_t.setdefault(c_idx, []).append(s_i)

        for c_idx, s_list in by_col_t.items():
            _, body_rgb, crest_rgb, _, _ = SILK_PALETTE[c_idx]
            cr = int(body_rgb[0] * shade_scale)
            cg = int(body_rgb[1] * shade_scale)
            cb = int(body_rgb[2] * shade_scale)

            q_t = np.empty((len(s_list), 4, 2), dtype=np.float64)
            for k_s, s_i in enumerate(s_list):
                q_t[k_s, 0, 0], q_t[k_s, 0, 1] = x_top[s_i], y_top[s_i]
                q_t[k_s, 1, 0], q_t[k_s, 1, 1] = x_right[s_i], y_right[s_i]
                q_t[k_s, 2, 0], q_t[k_s, 2, 1] = x_bot[s_i], y_bot[s_i]
                q_t[k_s, 3, 0], q_t[k_s, 3, 1] = x_left[s_i], y_left[s_i]

            py5.stroke(8, 12, 22, 235)
            py5.stroke_weight(1.4)
            py5.fill(cr, cg, cb, 250)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(q_t.reshape(-1, 2))

            if t_i < 5:
                l_segs = np.column_stack([x_left[s_list], y_left[s_list], x_right[s_list], y_right[s_list]])
                py5.stroke(crest_rgb[0], crest_rgb[1], crest_rgb[2], int(210 * shade_scale))
                py5.stroke_weight(1.4)
                py5.lines(l_segs)

    # Central brass Omori counterweight hook arbor
    py5.fill(28, 22, 14, 255)
    py5.stroke(245, 192, 68, 255)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, r_inner_well * 2.0)
    py5.fill(252, 218, 104, 255)
    py5.no_stroke()
    py5.circle(CX, CY, 12.0)


def draw_orbiting_tama_bobbins(tama_states: list, tau: float, omega: float):
    """
    Renders the 24 weighted wooden Tama (bobbins) around the outer Marudai Kagami rim.
    Each Tama features:
    - Drop shadow onto the polished Urushi Kagami surface
    - Turned boxwood/keyaki top and bottom flanges with lead weight band
    - Wound silk spool waist colored with the strand's Kusaki-zome / Kinshi dye
    - Chiral direction badge (+S clockwise / -Z counterclockwise)
    """
    for idx, r_tama, theta_tama, chirality, z_shed, col_idx in tama_states:
        tx = CX + r_tama * math.cos(theta_tama)
        ty = CY + r_tama * math.sin(theta_tama)
        _, body_rgb, crest_rgb, ply_rgb, _ = SILK_PALETTE[col_idx]

        # Scale slightly with z_shed (+1 upper handover vs -1 lower pass)
        bob_r = 26.5 + 3.2 * z_shed

        # Soft drop shadow on the Kagami deck
        py5.no_stroke()
        py5.fill(2, 4, 10, 175)
        py5.circle(tx + 5.0, ty + 6.0, bob_r * 2.15)

        # Outer turned Keyaki/Boxwood wooden flange
        py5.fill(188, 138, 76, 255)
        py5.stroke(42, 28, 14, 245)
        py5.stroke_weight(2.2)
        py5.circle(tx, ty, bob_r * 2.0)

        # Lead weight core ring (Namari-omori embedded inside the Tama)
        py5.no_fill()
        py5.stroke(94, 108, 128, 225)
        py5.stroke_weight(2.4)
        py5.circle(tx, ty, bob_r * 1.66)

        # Wound dyed silk spool band
        py5.fill(body_rgb[0], body_rgb[1], body_rgb[2], 255)
        py5.stroke(ply_rgb[0], ply_rgb[1], ply_rgb[2], 235)
        py5.stroke_weight(1.8)
        py5.circle(tx, ty, bob_r * 1.32)

        # Silk winding cross-striations on the bobbin waist
        for k_w in range(6):
            wa = theta_tama + k_w * (math.pi / 3.0) + chirality * omega * tau
            wx0 = tx + (bob_r * 0.34) * math.cos(wa)
            wy0 = ty + (bob_r * 0.34) * math.sin(wa)
            wx1 = tx + (bob_r * 0.64) * math.cos(wa + 0.35 * chirality)
            wy1 = ty + (bob_r * 0.64) * math.sin(wa + 0.35 * chirality)
            py5.stroke(crest_rgb[0], crest_rgb[1], crest_rgb[2], 215)
            py5.stroke_weight(1.6)
            py5.line(wx0, wy0, wx1, wy1)

        # Inner wooden spindle cap & brass pin
        py5.fill(228, 184, 118, 255)
        py5.stroke(62, 42, 20, 240)
        py5.stroke_weight(1.6)
        py5.circle(tx, ty, bob_r * 0.64)

        # Center chiral dot: gold for S-family (+1), cyan-white for Z-family (-1)
        py5.no_stroke()
        if chirality > 0:
            py5.fill(250, 204, 21, 255)
        else:
            py5.fill(56, 189, 248, 255)
        py5.circle(tx, ty, 7.5)


def draw_dark_card_frame(x: float, y: float, w: float, h: float):
    """Draws a museum-grade dark Urushi lacquer apparatus card with gold corner brackets."""
    py5.fill(10, 14, 26, 238)
    py5.stroke(86, 68, 38, 210)
    py5.stroke_weight(2.0)
    py5.rect(x, y, w, h, 8)

    py5.no_fill()
    py5.stroke(148, 114, 52, 125)
    py5.stroke_weight(1.1)
    py5.rect(x + 8, y + 8, w - 16, h - 16, 5)

    # Gold leaf corner brackets
    py5.stroke(234, 179, 58, 235)
    py5.stroke_weight(2.6)
    cl = 20.0
    for cx_c, cy_c, sx, sy in [
        (x, y, 1, 1),
        (x + w, y, -1, 1),
        (x, y + h, 1, -1),
        (x + w, y + h, -1, -1),
    ]:
        py5.line(cx_c, cy_c, cx_c + sx * cl, cy_c)
        py5.line(cx_c, cy_c, cx_c, cy_c + sy * cl)


def draw_kumihimo_topology_apparatuses(tau: float, omega: float):
    """
    Renders 8 Kumihimo & Braid-Group Topology apparatuses across 4 balanced flank cards.
    Strict non-overlapping coordinate geometry verified at 4K (3840x2160).
    """
    lx = 92.0
    rx = WIDTH - 92.0 - 796.0
    cw = 796.0
    ty = 175.0
    th = 835.0
    by = 1042.0
    bh = 855.0

    py5.text_align(py5.LEFT, py5.TOP)

    # =========================================================================
    # CARD 1 (TOP-LEFT): FIG. 01 ARTIN BRAID GROUP B_24 & FIG. 02 EPICYCLIC ORBITS
    # =========================================================================
    draw_dark_card_frame(lx, ty, cw, th)

    # --- FIG. 01: ARTIN BRAID GROUP B_n GENERATOR WORD & YANG-BAXTER RELATION ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 01 // ARTIN BRAID GROUP B_24 GENERATOR WORD & CROSSING TOPOLOGY", lx + 28, ty + 24)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("YANG-BAXTER BRAID RELATION: SIGMA_i * SIGMA_(i+1) * SIGMA_i = SIGMA_(i+1) * SIGMA_i * SIGMA_(i+1)", lx + 28, ty + 48)

    # 6-strand live braid diagram in x in [lx+38, lx+305], y in [ty+88, ty+355]
    bx0, by0, bw0, bh0 = lx + 38.0, ty + 88.0, 268.0, 262.0
    py5.fill(6, 9, 18, 240)
    py5.stroke(68, 84, 118, 195)
    py5.stroke_weight(1.5)
    py5.rect(bx0, by0, bw0, bh0, 5)

    u_b = np.linspace(0.0, 1.0, 90)
    yb_pts = by0 + 16.0 + u_b * (bh0 - 32.0)
    for s_b in range(6):
        _, body_rgb, crest_rgb, _, _ = SILK_PALETTE[s_b]
        phase_b = s_b * (math.pi / 3.0) + omega * tau * (1 if s_b % 2 == 0 else -1)
        xb_pts = (bx0 + bw0 * 0.5) + 98.0 * np.sin(2.2 * math.pi * u_b + phase_b)
        segs_b = np.column_stack([xb_pts[:-1], yb_pts[:-1], xb_pts[1:], yb_pts[1:]])
        py5.stroke(6, 9, 18, 240)
        py5.stroke_weight(7.2)
        py5.lines(segs_b)
        py5.stroke(body_rgb[0], body_rgb[1], body_rgb[2], 245)
        py5.stroke_weight(4.2)
        py5.lines(segs_b)

    tx1 = lx + 336.0
    ty1 = ty + 88.0
    f1_specs = [
        ("BRAID GROUP ORDER", ": B_24 (23 Elementary Generators)", (245, 184, 54)),
        ("ELEMENTARY CROSSING", ": sigma_i (+1 Over) / sigma_i^-1 (-1)", (56, 189, 248)),
        ("FAR COMMUTATIVITY", ": sigma_i * sigma_j = sigma_j * sigma_i", (52, 211, 153)),
        ("YANG-BAXTER IDENTITY", ": Artin Triple-Strand Isotopy", (244, 114, 182)),
        ("KONGO-GUMI WORD", ": Prod_(k=1..8) (sigma_2k * sigma_2k-1^-1)", (244, 240, 230)),
        ("WRITHE INVARIANT", ": W(B) = Sum eps(c) = 0 (Balanced)", (192, 132, 252)),
        ("CLOSURE LINK TYPE", ": 8-Component Torus Braid Link", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f1_specs):
        yy = ty1 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx1, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx1 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, ty + 390, lx + cw - 24, ty + 390)

    # --- FIG. 02: COUNTER-ROTATING TAMA HANDOVER EPICYCLES ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 02 // COUNTER-ROTATING TAMA BOBBIN HANDOVER EPICYCLES", lx + 28, ty + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("CHIRAL S-FAMILY (+CW GOLD) & Z-FAMILY (-CCW CYAN) FIGURE-EIGHT LOBE EXCHANGE", lx + 28, ty + 436)

    f2_cx = lx + 172.0
    f2_cy = ty + 625.0
    t_ep = np.linspace(0.0, 2.0 * math.pi, 180)
    for ch_sign, col_ep in [(1, (245, 184, 54, 230)), (-1, (56, 189, 248, 230))]:
        r_ep = 92.0 + 26.0 * ch_sign * np.cos(4.0 * t_ep + ch_sign * omega * tau)
        x_ep = f2_cx + r_ep * np.cos(t_ep)
        y_ep = f2_cy + r_ep * np.sin(t_ep)
        segs_ep = np.column_stack([x_ep[:-1], y_ep[:-1], x_ep[1:], y_ep[1:]])
        py5.stroke(*col_ep)
        py5.stroke_weight(2.4)
        py5.lines(segs_ep)

    # 8 moving bobbin phase markers on the epicycle diagram
    for m_i in range(8):
        ma = m_i * (math.pi / 4.0) + (1 if m_i % 2 == 0 else -1) * omega * tau
        mr = 92.0 + 26.0 * (1 if m_i % 2 == 0 else -1) * math.cos(4.0 * ma)
        py5.no_stroke()
        py5.fill(*(250, 204, 21, 255) if m_i % 2 == 0 else (56, 189, 248, 255))
        py5.circle(f2_cx + mr * math.cos(ma), f2_cy + mr * math.sin(ma), 10.5)

    tx2 = lx + 336.0
    ty2 = ty + 485.0
    f2_specs = [
        ("KAGAMI MIRROR SLOTS", ": 24 Notches (8 Triads x 3 Bobbins)", (245, 184, 54)),
        ("S-CHIRAL CARRIERS", ": 12 Tama // Clockwise (+omega)", (250, 204, 21)),
        ("Z-CHIRAL CARRIERS", ": 12 Tama // Counterclockwise (-omega)", (56, 189, 248)),
        ("OVER-UNDER CADENCE", ": 2-Over / 2-Under Helical Twill", (52, 211, 153)),
        ("HANDOVER SEQUENCE", ": North-South -> East-West -> Diag", (244, 114, 182)),
        ("HELIX INTERSECTION", ": alpha_braid = 38.5 DEG Bias Angle", (244, 240, 230)),
        ("TAMA BOBBIN MASS", ": m_tama = 70 g (18.7 Momme Keyaki)", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f2_specs):
        yy = ty2 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx2, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx2 + 178.0, yy)

    # =========================================================================
    # CARD 2 (BOTTOM-LEFT): FIG. 03 OMORI TENSION EQUILIBRIUM & FIG. 04 PALETTE
    # =========================================================================
    draw_dark_card_frame(lx, by, cw, bh)

    # --- FIG. 03: TENSILE EQUILIBRIUM: TAMA BOBBIN VS. OMORI COUNTERWEIGHT ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 03 // OMORI COUNTERWEIGHT & RADIAL CATENARY TENSION EQUILIBRIUM", lx + 28, by + 24)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("M_OMORI * g = SUM_(i=1..24) m_TAMA * g * SIN(ALPHA_i) GOVERNING STITCH PITCH DENSITY", lx + 28, by + 48)

    # Cross-section schematic of Marudai Kagami lip, Heso funnel, and suspended Omori weight
    f3_cx = lx + 172.0
    f3_y0 = by + 108.0
    # Left & Right Kagami wooden cross-section blocks
    py5.fill(148, 104, 54, 235)
    py5.stroke(234, 179, 58, 220)
    py5.stroke_weight(1.8)
    py5.rect(f3_cx - 125.0, f3_y0, 74.0, 26.0, 4)
    py5.rect(f3_cx + 51.0, f3_y0, 74.0, 26.0, 4)

    # Silk threads curving over the Tori-guchi lip down to the central Heso knot
    knot_y = f3_y0 + 96.0 + 10.0 * math.sin(2.0 * omega * tau + RND_TENSION_PHASE)
    py5.stroke(56, 189, 248, 235)
    py5.stroke_weight(2.6)
    py5.line(f3_cx - 115.0, f3_y0 + 80.0, f3_cx - 52.0, f3_y0 + 4.0)
    py5.line(f3_cx - 52.0, f3_y0 + 4.0, f3_cx, knot_y)
    py5.stroke(244, 63, 94, 235)
    py5.line(f3_cx + 115.0, f3_y0 + 80.0, f3_cx + 52.0, f3_y0 + 4.0)
    py5.line(f3_cx + 52.0, f3_y0 + 4.0, f3_cx, knot_y)

    # Hanging Tama weights on left & right + Central Omori brass cylinder
    py5.fill(234, 158, 22, 245)
    py5.stroke(254, 240, 138, 230)
    py5.stroke_weight(1.8)
    py5.circle(f3_cx - 115.0, f3_y0 + 94.0, 24.0)
    py5.circle(f3_cx + 115.0, f3_y0 + 94.0, 24.0)

    # Braided cord descending from knot_y to Omori brass weight
    py5.stroke(245, 184, 54, 245)
    py5.stroke_weight(5.0)
    py5.line(f3_cx, knot_y, f3_cx, knot_y + 82.0)
    py5.fill(214, 158, 38, 250)
    py5.stroke(254, 240, 138, 240)
    py5.stroke_weight(2.0)
    py5.rect(f3_cx - 28.0, knot_y + 82.0, 56.0, 44.0, 5)

    tx3 = lx + 336.0
    ty3 = by + 88.0
    t_force = 8.24 + 0.42 * math.sin(2.0 * omega * tau)
    f3_specs = [
        ("TOTAL TAMA MASS", ": 24 x 70 g = 1,680 g Perimeter Load", (245, 184, 54)),
        ("CENTRAL OMORI MASS", ": M_omori = 750 g (45% Equilibrium)", (56, 189, 248)),
        ("ACTIVE CORD TENSION", f": F_heso = {t_force:0.2f} N Axial Pull", (52, 211, 153)),
        ("HESO CONVERGENCE", ": alpha_0 = 26.4 DEG Dip Angle", (244, 114, 182)),
        ("TORI-GUCHI FRICTION", ": mu_hinoki = 0.14 (Polished Rim)", (244, 240, 230)),
        ("STITCH PITCH (ME)", ": 14.2 Crossings / cm (Tight Gauge)", (192, 132, 252)),
        ("ELASTIC MODULUS", ": E_silk = 10.4 GPa (Bombyx mori)", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f3_specs):
        yy = ty3 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx3, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx3 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(lx + 24, by + 390, lx + cw - 24, by + 390)

    # --- FIG. 04: KYOTO YUSOKU KUSAKI-ZOME & KINSHI GOLD SILK PALETTE ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 04 // KYOTO YUSOKU KUSAKI-ZOME BOTANICAL DYE & KINSHI PALETTE", lx + 28, by + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("BOMBYX MORI DEGUMMED SILK (NERI-GINU) & URUSHI-GILDED WASHI THREADS", lx + 28, by + 436)

    swatches = [
        ((234, 158, 22), "HON-KINSHI GOLD FOIL // URUSHI-LACQUERED KOZO WASHI GILDED WITH 24K GOLD LEAF"),
        ((225, 38, 76), "AKANE MADDER VERMILION // RUBIA AKANE ROOT ALIZARIN MORDANTED WITH CAMELLIA ASH"),
        ((42, 118, 228), "HON-AIZOME INDIGO // FERMENTED POLYGONUM TINCTORIUM SUKUMO VAT DYE"),
        ((212, 224, 238), "NERI-GINU PEARL SILK // SERICIN-DEGUMMED BOMBYX MORI FILAMENT (FIBROIN TRIANGULAR PRISM)"),
        ((18, 168, 124), "ROKUSHO CELADON EMERALD // KARIYASU GRASS OVER-DYED WITH AIZOME INDIGO"),
        ((148, 72, 232), "EDO-MURASAKI AMETHYST // LITHOSPERMUM ERYTHRORHIZON GROMWELL ROOT SHIKONIN"),
    ]
    for i, (rgb_s, desc_s) in enumerate(swatches):
        sy = by + 482.0 + i * 54.0
        py5.fill(*rgb_s)
        py5.stroke(234, 179, 58, 215)
        py5.stroke_weight(1.5)
        py5.rect(lx + 32, sy, 52, 34, 4)
        py5.no_stroke()
        py5.fill(236, 232, 224)
        py5.text_size(13)
        py5.text(desc_s, lx + 104, sy + 9)

    # =========================================================================
    # CARD 3 (TOP-RIGHT): FIG. 05 CROSS-SECTION TOPOLOGY & FIG. 06 CODEX LEDGER
    # =========================================================================
    draw_dark_card_frame(rx, ty, cw, th)

    # --- FIG. 05: CROSS-SECTIONAL BRAID TOPOLOGY (MARU, KAKU & HIRA-GUMI) ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 05 // BRAID CROSS-SECTION TOPOLOGY: MARU-GUMI VS. KARAKUMI", rx + 28, ty + 24)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("TUBULAR HELICAL SPIRAL (KONGO-GUMI) VS. INTERLOCKED DIAMOND TWILL (KARAKUMI)", rx + 28, ty + 48)

    # Left mini-diagram: 16-strand Kongo-gumi tubular ring; Right: Karakumi diamond lattice
    c5_x1, c5_y1 = rx + 115.0, ty + 215.0
    py5.no_fill()
    py5.stroke(245, 184, 54, 185)
    py5.stroke_weight(1.6)
    py5.circle(c5_x1, c5_y1, 118.0)
    for k5 in range(12):
        a5 = k5 * (math.pi / 6.0) + omega * tau
        py5.fill(*(245, 184, 54, 240) if k5 % 2 == 0 else (56, 189, 248, 240))
        py5.no_stroke()
        py5.circle(c5_x1 + 59.0 * math.cos(a5), c5_y1 + 59.0 * math.sin(a5), 14.0)

    c5_x2, c5_y2 = rx + 245.0, ty + 215.0
    py5.no_fill()
    py5.stroke(52, 211, 153, 215)
    py5.stroke_weight(2.0)
    for d5 in range(3):
        s5 = 24.0 + d5 * 18.0
        with py5.begin_shape(py5.QUADS):
            py5.vertex(c5_x2, c5_y2 - s5)
            py5.vertex(c5_x2 + s5, c5_y2)
            py5.vertex(c5_x2, c5_y2 + s5)
            py5.vertex(c5_x2 - s5, c5_y2)

    tx5 = rx + 336.0
    ty5 = ty + 88.0
    f5_specs = [
        ("KONGO-GUMI (MARU)", ": 16/24-Tama Cylindrical Spiral Core", (245, 184, 54)),
        ("EDO YATSU-GUMI", ": 8-Strand Hollow Tubular Braid", (56, 189, 248)),
        ("KAKU-YATSU-GUMI", ": Square Cross-Section Parallel Warp", (52, 211, 153)),
        ("KARAKUMI (TAKADAI)", ": Flat Interlocked Diamond Brocade", (244, 114, 182)),
        ("NAIKI-GUMI (CORE)", ": Double-Layer Concentric Sheath", (192, 132, 252)),
        ("PACKING FRACTION", ": phi_silk = 0.785 Hexagonal Bundle", (244, 240, 230)),
        ("TORSIONAL RIGIDITY", ": Balanced S/Z Zero-Torque Equilibrium", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f5_specs):
        yy = ty5 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx5, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx5 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, ty + 390, rx + cw - 24, ty + 390)

    # --- FIG. 06: HISTORICAL KUMIHIMO CODEX & BRAID TOPOLOGY LEDGER ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 06 // HISTORICAL YUSOKU KUMIHIMO & BRAID TOPOLOGY LEDGER", rx + 28, ty + 412)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("FROM NARA SHOSO-IN IMPERIAL REPOSITORY (756 CE) TO ARTIN BRAID GROUPS", rx + 28, ty + 436)

    rows = [
        ("SHOSO-IN KARAKUMI (756)", "Nara Todai-ji", "Flat Diamond Braid", "Imperial Sword Belt"),
        ("ITSUKUSHIMA ODOSHI (1180)", "Heian/Kamakura", "Yoroi Armor Lacing", "Shock-Absorbing Silk"),
        ("EDO SAGEO & OBIJIME (1652)", "Domyo Kyoto/Edo", "24-Tama Kongo-Gumi", "Marudai & Kakudai"),
        ("ARTIN BRAID GROUP (1925)", "Hamburg (Artin)", "B_n Presentation", "Theorie der Zopfe"),
        ("JONES POLYNOMIAL (1984)", "V.F.R. Jones", "Hecke Algebra Rep", "Knot Invariant V(t)"),
        ("ACTIVE MARUDAI SIMULATION", "24-Tama B_24 Loom", "2-Up / 2-Down Twill", "HARMONIC LIVE"),
    ]
    for r_i, (c_name, c_era, c_weave, c_note) in enumerate(rows):
        ry_row = ty + 478.0 + r_i * 55.0
        is_hi = (r_i == 2 or r_i == 5)
        py5.fill(*(28, 38, 64, 242) if is_hi else (14, 20, 36, 220))
        py5.stroke(*(245, 184, 54, 235) if is_hi else (68, 84, 118, 175))
        py5.stroke_weight(1.9 if is_hi else 1.1)
        py5.rect(rx + 28, ry_row, cw - 56, 44, 5)

        py5.no_stroke()
        py5.fill(244, 240, 230)
        py5.text_size(12)
        py5.text(c_name, rx + 44, ry_row + 15)
        py5.fill(56, 189, 248)
        py5.text(c_era, rx + 265, ry_row + 15)
        py5.fill(245, 184, 54)
        py5.text(c_weave, rx + 435, ry_row + 15)
        py5.fill(52, 211, 153)
        py5.text(c_note, rx + 595, ry_row + 15)

    # =========================================================================
    # CARD 4 (BOTTOM-RIGHT): FIG. 07 KINSHI PLY HELIX & FIG. 08 OSCILLOGRAM
    # =========================================================================
    draw_dark_card_frame(rx, by, cw, bh)

    # --- FIG. 07: MICROSCOPIC S-TWIST / Z-TWIST SILK PLY & KINSHI FOIL HELIX ---
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 07 // MICROSCOPIC 4-PLY SILK YARN & KINSHI GOLD FOIL HELIX", rx + 28, by + 24)
    py5.fill(245, 184, 54)
    py5.text_size(12)
    py5.text("TRIANGULAR BOMBYX MORI FIBROIN PRISM & HELICAL 24K GOLD-LEAF WASHI WRAP", rx + 28, by + 48)

    # Horizontal 3D twisted Kinshi gold-wrapped silk filament diagram
    f7_x0, f7_y0 = rx + 42.0, by + 195.0
    u7 = np.linspace(0.0, 1.0, 120)
    x7 = f7_x0 + u7 * 255.0
    for p_k in range(3):
        ph7 = p_k * (2.0 * math.pi / 3.0) + 2.0 * omega * tau
        y7 = f7_y0 + 28.0 * np.sin(3.5 * math.pi * u7 - ph7)
        segs7 = np.column_stack([x7[:-1], y7[:-1], x7[1:], y7[1:]])
        py5.stroke(*(245, 184, 54, 245) if p_k == 0 else ((56, 189, 248, 225) if p_k == 1 else (244, 63, 94, 225)))
        py5.stroke_weight(6.5 if p_k == 0 else 4.2)
        py5.lines(segs7)

    tx7 = rx + 336.0
    ty7 = by + 88.0
    f7_specs = [
        ("FILAMENT UNIT", ": 21 Denier Raw Silk x 16 Ends / Ply", (245, 184, 54)),
        ("PLY STRUCTURE", ": 4-Ply S-Twist over Z-Spun Core", (56, 189, 248)),
        ("FIBROIN CROSS-SECT", ": Rounded Equilateral Triangle Prism", (52, 211, 153)),
        ("KINSHI FOIL PITCH", ": 0.35 mm Washi Strip @ 42 DEG Helix", (244, 114, 182)),
        ("ADHESIVE BINDER", ": Filtered Ro-iro Raw Urushi Lacquer", (244, 240, 230)),
        ("SPECULAR LUSTER", ": Double Internal Refraction + Sheen", (192, 132, 252)),
        ("STRAND DIAMETER", ": d_cord = 1.45 mm -> 6.8 mm Braid", (245, 184, 54)),
    ]
    for i, (k_lbl, v_lbl, col_t) in enumerate(f7_specs):
        yy = ty7 + i * 33.0
        py5.fill(148, 163, 184)
        py5.text_size(12)
        py5.text(k_lbl, tx7, yy)
        py5.fill(*col_t)
        py5.text(v_lbl, tx7 + 178.0, yy)

    py5.stroke(68, 84, 118, 165)
    py5.stroke_weight(1.4)
    py5.line(rx + 24, by + 390, rx + cw - 24, by + 390)

    # --- FIG. 08: HARMONIC BOBBIN ANGULAR MOMENTUM & TENSION OSCILLOGRAM ---
    py5.no_stroke()
    py5.fill(244, 240, 230)
    py5.text_size(17)
    py5.text("FIG. 08 // HARMONIC TAMA ANGULAR MOMENTUM & RADIAL TENSION TRACE", rx + 28, by + 412)
    py5.fill(56, 189, 248)
    py5.text_size(12)
    py5.text("COUPLED S-CHIRAL / Z-CHIRAL CROSSING WAVES & OMORI VERTICAL OSCILLATION", rx + 28, by + 436)

    wx = rx + 36.0
    wy = by + 482.0
    ww = cw - 72.0
    wh = 285.0
    py5.fill(6, 9, 18, 242)
    py5.stroke(68, 84, 118, 200)
    py5.stroke_weight(1.6)
    py5.rect(wx, wy, ww, wh, 6)

    py5.stroke(24, 34, 56, 165)
    py5.stroke_weight(1.1)
    for g_i in range(1, 4):
        gy_w = wy + (wh / 4.0) * g_i
        py5.line(wx, gy_w, wx + ww, gy_w)
    for g_j in range(1, 6):
        gx_w = wx + (ww / 6.0) * g_j
        py5.line(gx_w, wy, gx_w, wy + wh)

    n_w = 200
    u_w = np.linspace(0.0, 1.0, n_w)
    xw_arr = wx + u_w * ww
    mid_y = wy + wh * 0.5

    for freq_w, amp_w, ph_w, col_w in [
        (3.0, 88.0, omega * tau, (245, 184, 54, 240)),
        (3.0, 88.0, -omega * tau + 0.8, (56, 189, 248, 240)),
        (6.0, 52.0, 2.0 * omega * tau, (244, 63, 94, 225)),
        (2.0, 38.0, -2.0 * omega * tau, (52, 211, 153, 225)),
    ]:
        yw_c = mid_y - amp_w * np.sin(freq_w * 2.0 * math.pi * u_w + ph_w) * np.cos(math.pi * u_w - 0.5 * omega * tau)
        segs_w = np.column_stack([xw_arr[:-1], yw_c[:-1], xw_arr[1:], yw_c[1:]])
        py5.stroke(*col_w)
        py5.stroke_weight(2.5)
        py5.lines(segs_w)

    py5.no_stroke()
    py5.fill(168, 182, 204)
    py5.text_size(12)
    py5.text(
        "GOLD: S-FAMILY (+CW)  //  CYAN: Z-FAMILY (-CCW)  //  CRIMSON: SHED CROSSING  //  EMERALD: OMORI PULSE",
        wx + 8,
        wy + wh + 18,
    )


def draw_museum_border_and_typography(tau: float, omega: float):
    """Draws the outer architectural Urushi-and-gold border, header, and telemetry footer."""
    py5.no_fill()
    py5.stroke(198, 148, 48, 225)
    py5.stroke_weight(3.2)
    py5.rect(52, 48, WIDTH - 104, HEIGHT - 96, 10)

    py5.stroke(112, 88, 42, 165)
    py5.stroke_weight(1.4)
    py5.rect(64, 60, WIDTH - 128, HEIGHT - 120, 6)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(248, 244, 234)
    py5.text_size(30)
    py5.text(
        "KUMIHIMO MARUDAI BRAIDING LOOM // ARTIN BRAID-GROUP B_24 TOPOLOGY",
        CX,
        82,
    )

    py5.fill(245, 184, 54)
    py5.text_size(15)
    py5.text(
        "24-TAMA COUNTER-ROTATING KONGO-GUMI & KARAKUMI SILK-AND-GOLD BROCADE KINEMATICS (KYOTO YUSOKU TRADITION)",
        CX,
        124,
    )

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(168, 182, 204)
    py5.text_size(14)
    py5.text(
        "BRAID GROUP B_24 // 12 S-CHIRAL (+CW) x 12 Z-CHIRAL (-CCW) TAMA BOBBINS // OMORI EQUILIBRIUM M = 750 g",
        96,
        HEIGHT - 74,
    )

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K PROCEDURAL TEXTILE CRAFT // HARMONIC PHASE TAU = {tau:0.3f} (12.0s @ 60FPS)",
        WIDTH - 96,
        HEIGHT - 74,
    )


def finish_and_encode():
    """Compiles the 720 rendered PNG frames into a 4K 60fps H.264 MP4 and cleans up frames/."""
    elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {elapsed:.1f}s (~{TOTAL_FRAMES/max(0.1, elapsed):.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "16",
        "-preset",
        "fast",
        str(OUTPUT_MP4),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and OUTPUT_MP4.exists():
        mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mb:.2f} MB)")
        shutil.rmtree(FRAMES_DIR, ignore_errors=True)
        print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
    else:
        print(f"[{WORK_NAME}] FFmpeg error: {res.stderr}", file=sys.stderr)

    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()


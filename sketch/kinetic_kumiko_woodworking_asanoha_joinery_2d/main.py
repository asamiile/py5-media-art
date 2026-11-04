"""
Kinetic Kumiko Woodworking Asanoha Joinery 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art in the Textile / Calligraphy / Procedural Craft genre,
exploring traditional Japanese Kumiko-zaiku precision micro-woodworking joinery
and Kiku-jutsu (Japanese architectural layout trigonometry) executed on warm
backlit Echizen kozo shoji paper (#f7f3ea).

Perfected in Hida-Takayama and Okawa without a single nail or drop of glue, Kumiko
artisans plane thin wood laths (ha-ita) to micron tolerances and bevel their ends
at exact trigonometric angles (15 deg, 22.5 deg, 30 deg, 45 deg, 60 deg) using angled
chisel blocks (katagi) and hand planes (kanna).

This simulation visualizes a monumental circular Kumiko transom (enso-ranma) combining:
1. Primary Mitsukude-Kikko three-way interlocking hexagonal/triangular grid.
2. Concentric rings of Kasane-Asanoha (layered hemp leaf), Goma-gara (sesame
   rosette), Sakura-Kikko (cherry tortoiseshell), and Kage-Asanoha infill pieces (tsukeko).
3. Synchronized 12.0s harmonic joinery breathing: infill pieces slide along their
   mortise tracks (tsugite) to demonstrate self-locking geometric compression, while
   a warm afternoon sunbeam sweeps across the 3D beveled wood facets, casting crisp
   layered drop shadows onto the glowing shoji paper substrate.
4. Four full-flank Kiku-jutsu carpentry blueprint apparatuses balancing all four quadrants.
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
WORK_NAME = "kinetic_kumiko_woodworking_asanoha_joinery_2d"
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

# Non-fixed runtime phase/angle variations
np.random.seed(int(time.time() * 1000) % 100000)
RND_SUN_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))
RND_WAVE_PHASE = float(np.random.uniform(0.0, 2.0 * math.pi))

# Center of the monumental Kumiko Enso-Ranma panel
CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 24.0

# Triangular / Hexagonal Lattice Parameters (Mitsukude Grid)
TRI_SIDE = 240.0
TRI_H = TRI_SIDE * math.sqrt(3.0) / 2.0
MAX_RADIUS = 815.0

# Wood Species Base Colors (RGB)
# 0: Akita Hinoki Cypress (Golden Pale Cream)
# 1: Keyaki Zelkova (Warm Amber Terracotta)
# 2: Jindai-Sugi Bog Cedar (Deep Smoked Walnut Umber)
# 3: Aizome Indigo-Dyed Cypress (Prussian Slate Indigo)
# 4: Hon-Shu Lacquered Vermilion Accent (Cinnabar Red)
# 5: Wakakusa Dyed Celadon Hinoki (Soft Moss Green)
WOOD_SPECIES = np.array([
    [234.0, 206.0, 160.0],  # 0: Hinoki Cypress
    [196.0, 124.0, 68.0],   # 1: Keyaki Zelkova
    [104.0, 78.0, 56.0],    # 2: Jindai-Sugi Bog Cedar
    [40.0, 68.0, 98.0],     # 3: Aizome Indigo Wood
    [188.0, 50.0, 38.0],    # 4: Vermilion Accent Wood
    [82.0, 118.0, 86.0],    # 5: Wakakusa Moss Cypress
], dtype=np.float64)

TRI_CELLS = []
HEX_NODES = []


def build_kumiko_lattice():
    nodes_dict = {}
    for j in range(-7, 8):
        for i in range(-9, 10):
            px = CX + (i + 0.5 * j) * TRI_SIDE
            py = CY + j * TRI_H
            dist = math.hypot(px - CX, py - CY)
            nodes_dict[(i, j)] = (px, py, dist)
            if dist <= MAX_RADIUS - 16.0:
                HEX_NODES.append((px, py, dist, i, j))

    for j in range(-6, 7):
        for i in range(-8, 8):
            for orient in (1, -1):
                if orient == 1:
                    k0, k1, k2 = (i, j), (i + 1, j), (i, j + 1)
                else:
                    k0, k1, k2 = (i + 1, j + 1), (i, j + 1), (i + 1, j)

                if k0 in nodes_dict and k1 in nodes_dict and k2 in nodes_dict:
                    p0 = nodes_dict[k0][:2]
                    p1 = nodes_dict[k1][:2]
                    p2 = nodes_dict[k2][:2]
                    tcx = (p0[0] + p1[0] + p2[0]) / 3.0
                    tcy = (p0[1] + p1[1] + p2[1]) / 3.0
                    tdist = math.hypot(tcx - CX, tcy - CY)
                    min_vdist = min(
                        math.hypot(p0[0] - CX, p0[1] - CY),
                        math.hypot(p1[0] - CX, p1[1] - CY),
                        math.hypot(p2[0] - CX, p2[1] - CY),
                    )
                    if tdist <= MAX_RADIUS + 95.0 and min_vdist <= MAX_RADIUS - 5.0:
                        t_angle = math.atan2(tcy - CY, tcx - CX)
                        if tdist < 165.0:
                            motif = 0  # Central Royal Kasane-Asanoha + Vermilion/Indigo Star
                        elif tdist < 365.0:
                            motif = 1  # Classic Asanoha with Double Goma-gara Sesame Lock
                        elif tdist < 565.0:
                            motif = 2  # Sakura-Kikko & Rindo Gentian Starburst
                        else:
                            motif = 3  # Outer Kage-Asanoha & Wakakusa Border Lattice
                        TRI_CELLS.append({
                            "cx": tcx,
                            "cy": tcy,
                            "dist": tdist,
                            "angle": t_angle,
                            "orient": orient,
                            "v": [p0, p1, p2],
                            "motif": motif,
                        })


build_kumiko_lattice()

PRIMARY_STRUTS = []


def build_primary_struts():
    angles = [0.0, math.pi / 3.0, 2.0 * math.pi / 3.0]
    for axis_idx, ang in enumerate(angles):
        dx = math.cos(ang)
        dy = math.sin(ang)
        nx = -dy
        ny = dx
        for k in range(-6, 7):
            offset = k * TRI_H
            if abs(offset) < MAX_RADIUS - 4.0:
                half_chord = math.sqrt(max(0.0, (MAX_RADIUS + 4.0) ** 2 - offset ** 2))
                mx = CX + nx * offset
                my = CY + ny * offset
                x1 = mx - dx * half_chord
                y1 = my - dy * half_chord
                x2 = mx + dx * half_chord
                y2 = my + dy * half_chord
                PRIMARY_STRUTS.append((x1, y1, x2, y2, ang, axis_idx, k))


build_primary_struts()

# Precompute Shoji Washi Paper Mulberry Fiber Texture Lines
NUM_FIBERS = 300
SH_X1 = np.random.uniform(70.0, WIDTH - 70.0, NUM_FIBERS)
SH_Y1 = np.random.uniform(70.0, HEIGHT - 70.0, NUM_FIBERS)
SH_ANG = np.random.uniform(0.0, math.pi, NUM_FIBERS)
SH_LEN = np.random.uniform(60.0, 240.0, NUM_FIBERS)
SH_X2 = SH_X1 + np.cos(SH_ANG) * SH_LEN
SH_Y2 = SH_Y1 + np.sin(SH_ANG) * SH_LEN
SH_FIB_SEGMENTS = np.column_stack([SH_X1, SH_Y1, SH_X2, SH_Y2])


def clip_segment_to_circle(x1, y1, x2, y2, radius):
    """Clips a 2D line segment (x1,y1)-(x2,y2) to the interior of circle(CX, CY, radius)."""
    dx = x2 - x1
    dy = y2 - y1
    fx = x1 - CX
    fy = y1 - CY
    a = dx * dx + dy * dy
    if a < 1e-6:
        return None
    b = 2.0 * (fx * dx + fy * dy)
    c = (fx * fx + fy * fy) - radius * radius
    disc = b * b - 4.0 * a * c
    if disc <= 0.0:
        return None
    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)
    t_start = max(0.0, t1)
    t_end = min(1.0, t2)
    if t_start >= t_end - 1e-4:
        return None
    nx1 = x1 + t_start * dx
    ny1 = y1 + t_start * dy
    nx2 = x1 + t_end * dx
    ny2 = y1 + t_end * dy
    return nx1, ny1, nx2, ny2


def build_beveled_lath_quads(x1, y1, x2, y2, half_w, wood_idx, sun_dx, sun_dy, clip_r=None):
    """
    Constructs a 3D beveled Kumiko wood strip (ha-ita) between (x1, y1) and (x2, y2)
    clipped cleanly to the circular Enso-Waku inner aperture, as two longitudinal
    chamfered facets (left bevel + right bevel) with mitred tips.
    """
    if clip_r is not None:
        clipped = clip_segment_to_circle(x1, y1, x2, y2, clip_r)
        if clipped is None:
            return None
        x1, y1, x2, y2 = clipped

    vx = x2 - x1
    vy = y2 - y1
    length = math.hypot(vx, vy)
    if length < 3.0:
        return None
    ux = vx / length
    uy = vy / length
    nx = -uy
    ny = ux

    tip = min(half_w * 1.15, length * 0.22)
    ax = x1 + ux * tip
    ay = y1 + uy * tip
    bx = x2 - ux * tip
    by = y2 - uy * tip

    l_ax = ax + nx * half_w
    l_ay = ay + ny * half_w
    l_bx = bx + nx * half_w
    l_by = by + ny * half_w

    r_ax = ax - nx * half_w
    r_ay = ay - ny * half_w
    r_bx = bx - nx * half_w
    r_by = by - ny * half_w

    dot_l = nx * sun_dx + ny * sun_dy
    # Quantize dot product into 3 lighting buckets (0: shaded, 1: mid, 2: sunlit) for ultra-fast batching
    b_l = 2 if dot_l > 0.32 else (0 if dot_l < -0.32 else 1)
    b_r = 2 if -dot_l > 0.32 else (0 if -dot_l < -0.32 else 1)

    q_left = [[x1, y1], [l_ax, l_ay], [l_bx, l_by], [x2, y2]]
    q_right = [[x1, y1], [x2, y2], [r_bx, r_by], [r_ax, r_ay]]
    q_full = [[l_ax, l_ay], [l_bx, l_by], [r_bx, r_by], [r_ax, r_ay]]

    return q_left, q_right, q_full, (wood_idx, b_l), (wood_idx, b_r), (x1, y1, x2, y2)


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

    sun_angle = omega * tau + RND_SUN_PHASE
    sun_dx = math.cos(sun_angle)
    sun_dy = math.sin(sun_angle)
    sh_ox = -sun_dx * 9.5
    sh_oy = -sun_dy * 9.5

    # 1. Warm Backlit Echizen Kozo Shoji Paper Substrate (#f7f3ea)
    py5.background(247, 243, 234)

    # 2. Backlit Shoji Warmth Glow & Architectural Grid
    py5.no_stroke()
    glow_cx = CX + 220.0 * math.cos(omega * tau)
    glow_cy = CY + 140.0 * math.sin(omega * tau)
    for r_glow, a_glow in [(1150, 22), (860, 28), (580, 34), (340, 40)]:
        py5.fill(255, 245, 212, a_glow)
        py5.circle(glow_cx, glow_cy, r_glow * 2.0)

    # Shoji Kozo Mulberry Fibers
    py5.stroke(226, 218, 202, 120)
    py5.stroke_weight(1.4)
    py5.lines(SH_FIB_SEGMENTS)

    # Kiku-jutsu Architectural Drafting Grid
    py5.stroke(222, 214, 198, 135)
    py5.stroke_weight(1.5)
    for gx in range(120, WIDTH, 120):
        py5.line(gx, 80, gx, HEIGHT - 80)
    for gy in range(120, HEIGHT, 120):
        py5.line(80, gy, WIDTH - 80, gy)

    # Shoji Kumiko Backing Sash Ribs behind the circular transom
    py5.stroke(218, 206, 184, 165)
    py5.stroke_weight(6.0)
    for sx in [CX - 720, CX - 480, CX - 240, CX, CX + 240, CX + 480, CX + 720]:
        py5.line(sx, 85, sx, HEIGHT - 85)
    for sy in [CY - 480, CY - 240, CY, CY + 240, CY + 480]:
        py5.line(85, sy, WIDTH - 85, sy)

    # Warm Inner Shoji Lantern Glow inside the circular Enso-Ranma aperture
    py5.no_stroke()
    py5.fill(255, 249, 232, 145)
    py5.circle(CX, CY, MAX_RADIUS * 2.0)

    # 3. Collect all Kumiko laths grouped by (wood_species, light_bucket) for ultra-fast batching
    shadow_quads = []
    buckets = {(w, b): [] for w in range(6) for b in range(3)}
    ridge_lines = []
    clip_rad = MAX_RADIUS - 2.0

    def add_lath(x1, y1, x2, y2, half_w, wood_idx):
        res = build_beveled_lath_quads(
            x1, y1, x2, y2, half_w, wood_idx, sun_dx, sun_dy, clip_r=clip_rad
        )
        if res is None:
            return
        ql, qr, qf, key_l, key_r, rline = res
        shadow_quads.append([
            [qf[0][0] + sh_ox, qf[0][1] + sh_oy],
            [qf[1][0] + sh_ox, qf[1][1] + sh_oy],
            [qf[2][0] + sh_ox, qf[2][1] + sh_oy],
            [qf[3][0] + sh_ox, qf[3][1] + sh_oy],
        ])
        buckets[key_l].extend(ql)
        buckets[key_r].extend(qr)
        ridge_lines.append(rline)

    # 3A. Build Infill Motifs (Tsukeko) inside every Triangular Cell
    for cell in TRI_CELLS:
        tcx = cell["cx"]
        tcy = cell["cy"]
        tdist = cell["dist"]
        tang = cell["angle"]
        v0, v1, v2 = cell["v"]
        motif = cell["motif"]

        wave_phase = omega * tau - (tdist / 250.0) + 3.0 * tang + RND_WAVE_PHASE
        breath = 0.5 + 0.5 * math.sin(wave_phase)
        breath2 = 0.5 + 0.5 * math.cos(wave_phase * 2.0)

        m01 = ((v0[0] + v1[0]) * 0.5, (v0[1] + v1[1]) * 0.5)
        m12 = ((v1[0] + v2[0]) * 0.5, (v1[1] + v2[1]) * 0.5)
        m20 = ((v2[0] + v0[0]) * 0.5, (v2[1] + v0[1]) * 0.5)
        mids = [m01, m12, m20]

        if motif == 0:
            for k in range(3):
                vk = cell["v"][k]
                vnext = cell["v"][(k + 1) % 3]
                mk = mids[k]
                add_lath(vk[0], vk[1], tcx, tcy, 5.2, 0)
                slide_t = 0.12 * (1.0 - breath)
                sx = mk[0] * (1.0 - slide_t) + tcx * slide_t
                sy = mk[1] * (1.0 - slide_t) + tcy * slide_t
                add_lath(sx, sy, tcx, tcy, 4.4, 4)
                r_in = 0.35 + 0.14 * breath
                p_a = (tcx + (vk[0] - tcx) * r_in, tcy + (vk[1] - tcy) * r_in)
                p_b = (tcx + (vnext[0] - tcx) * r_in, tcy + (vnext[1] - tcy) * r_in)
                add_lath(p_a[0], p_a[1], p_b[0], p_b[1], 4.2, 3)
                add_lath(p_a[0], p_a[1], mk[0], mk[1], 3.6, 1)
                add_lath(p_b[0], p_b[1], mk[0], mk[1], 3.6, 1)

        elif motif == 1:
            r_goma = 0.28 + 0.16 * breath
            for k in range(3):
                vk = cell["v"][k]
                vnext = cell["v"][(k + 1) % 3]
                mk = mids[k]
                add_lath(vk[0], vk[1], tcx, tcy, 4.8, 0)
                add_lath(mk[0], mk[1], tcx, tcy, 4.0, 1)
                g1 = (vk[0] + (tcx - vk[0]) * r_goma, vk[1] + (tcy - vk[1]) * r_goma)
                g2 = (vnext[0] + (tcx - vnext[0]) * r_goma, vnext[1] + (tcy - vnext[1]) * r_goma)
                add_lath(g1[0], g1[1], g2[0], g2[1], 3.8, 2)
                r_goma2 = 0.62 - 0.12 * breath2
                h1 = (vk[0] + (tcx - vk[0]) * r_goma2, vk[1] + (tcy - vk[1]) * r_goma2)
                h2 = (vnext[0] + (tcx - vnext[0]) * r_goma2, vnext[1] + (tcy - vnext[1]) * r_goma2)
                add_lath(h1[0], h1[1], h2[0], h2[1], 3.4, 3)

        elif motif == 2:
            r_star = 0.34 + 0.15 * breath
            for k in range(3):
                vk = cell["v"][k]
                vnext = cell["v"][(k + 1) % 3]
                mk = mids[k]
                mnext = mids[(k + 1) % 3]
                add_lath(vk[0], vk[1], tcx, tcy, 4.6, 1)
                add_lath(mk[0], mk[1], mnext[0], mnext[1], 4.2, 0)
                s_mid = (tcx + (mk[0] - tcx) * (0.55 + 0.20 * breath),
                         tcy + (mk[1] - tcy) * (0.55 + 0.20 * breath))
                s_v1 = (tcx + (vk[0] - tcx) * r_star, tcy + (vk[1] - tcy) * r_star)
                s_v2 = (tcx + (vnext[0] - tcx) * r_star, tcy + (vnext[1] - tcy) * r_star)
                add_lath(s_v1[0], s_v1[1], s_mid[0], s_mid[1], 3.6, 4 if (k == 0) else 5)
                add_lath(s_v2[0], s_v2[1], s_mid[0], s_mid[1], 3.6, 4 if (k == 0) else 5)

        else:
            r_ap = 0.24 + 0.14 * breath
            for k in range(3):
                vk = cell["v"][k]
                vnext = cell["v"][(k + 1) % 3]
                mk = mids[k]
                c_k = (tcx + (vk[0] - tcx) * r_ap, tcy + (vk[1] - tcy) * r_ap)
                c_next = (tcx + (vnext[0] - tcx) * r_ap, tcy + (vnext[1] - tcy) * r_ap)
                add_lath(vk[0], vk[1], c_k[0], c_k[1], 4.6, 0)
                add_lath(c_k[0], c_k[1], c_next[0], c_next[1], 4.2, 5)
                ap_mid = ((c_k[0] + c_next[0]) * 0.5, (c_k[1] + c_next[1]) * 0.5)
                add_lath(mk[0], mk[1], ap_mid[0], ap_mid[1], 3.8, 1)

    # 3B. Add Primary Mitsukude-Gumi Structural Lattice Struts
    for (x1, y1, x2, y2, ang, axis_idx, k_idx) in PRIMARY_STRUTS:
        w_species = 2 if (k_idx == 0) else 0
        add_lath(x1, y1, x2, y2, 7.6, w_species)

    # 4. Batch-Render All Drop Shadows, Beveled Wood Facets, and Center Ridge Lines
    sh_arr = np.array(shadow_quads, dtype=np.float64)
    rl_arr = np.array(ridge_lines, dtype=np.float64)

    # Pass 1: Soft Outer Penumbra Shadow onto Shoji Paper
    py5.no_stroke()
    py5.fill(48, 36, 24, 38)
    sh_penumbra = (sh_arr + np.array([sh_ox * 0.35, sh_oy * 0.35])).reshape(-1, 2)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(sh_penumbra)

    # Pass 2: Crisp Contact Drop Shadow onto Shoji Paper
    py5.fill(36, 26, 18, 68)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(sh_arr.reshape(-1, 2))

    # Pass 3: Vectorized Beveled Wood Facets grouped by (species, light_bucket)
    py5.stroke(62, 44, 28, 145)
    py5.stroke_weight(0.9)
    light_mults = (0.82, 0.98, 1.15)
    for (w_idx, b_idx), verts_list in buckets.items():
        if not verts_list:
            continue
        rgb = np.clip(WOOD_SPECIES[w_idx] * light_mults[b_idx], 15.0, 252.0)
        py5.fill(float(rgb[0]), float(rgb[1]), float(rgb[2]))
        v_np = np.array(verts_list, dtype=np.float64)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(v_np)

    # Pass 4: Specular Kanna-Planed Center Arrises (Ridge Highlights along every lath)
    py5.stroke(252, 242, 218, 175)
    py5.stroke_weight(1.2)
    py5.lines(rl_arr)

    # 5. Mitsukude Joint Rosette Pins at Hex Lattice Nodes
    for (nx, ny, ndist, ni, nj) in HEX_NODES:
        if ndist <= MAX_RADIUS - 20.0:
            pulse = 1.0 + 0.15 * math.sin(omega * tau - ndist / 200.0)
            r_cap = 9.5 * pulse
            py5.stroke(55, 38, 24, 220)
            py5.stroke_weight(1.6)
            if (ni - nj) % 3 == 0:
                py5.fill(188, 50, 38)
            else:
                py5.fill(242, 218, 174)
            with py5.begin_shape():
                for h_k in range(6):
                    ha = h_k * math.pi / 3.0 + math.pi / 6.0
                    py5.vertex(nx + math.cos(ha) * r_cap, ny + math.sin(ha) * r_cap)
            py5.end_shape(py5.CLOSE)

    # 6. Monumental Circular Jindai-Sugi / Hinoki Outer Ranma Frame (Enso-Waku)
    draw_ranma_outer_frame(sun_dx, sun_dy, sh_ox, sh_oy, tau)

    # 7. Four Quadrant Kiku-Jutsu Carpentry & Joinery Telemetry Apparatuses
    draw_kiku_jutsu_apparatuses(tau, sun_angle)

    # 8. Archival Architectural Border & Museum Typography (Zero Personal Signatures/Seals)
    draw_archival_border_and_typography(tau)

    # Save frame
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
        print(f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")


def draw_ranma_outer_frame(sun_dx, sun_dy, sh_ox, sh_oy, tau):
    """Draws the multi-tiered circular Jindai-Sugi and Hinoki Ranma border frame with 12 Chigiri butterfly keys."""
    n_seg = 120
    r_in = MAX_RADIUS - 14.0
    r_mid = MAX_RADIUS + 20.0
    r_out = MAX_RADIUS + 56.0

    py5.no_stroke()
    with py5.begin_shape(py5.QUAD_STRIP):
        py5.fill(32, 22, 14, 85)
        for i in range(n_seg + 1):
            a = i * 2.0 * math.pi / n_seg
            ca, sa = math.cos(a), math.sin(a)
            py5.vertex(CX + ca * r_in + sh_ox * 1.2, CY + sa * r_in + sh_oy * 1.2)
            py5.vertex(CX + ca * r_out + sh_ox * 1.2, CY + sa * r_out + sh_oy * 1.2)

    py5.stroke(70, 50, 32, 185)
    py5.stroke_weight(1.5)
    with py5.begin_shape(py5.QUAD_STRIP):
        for i in range(n_seg + 1):
            a = i * 2.0 * math.pi / n_seg
            ca, sa = math.cos(a), math.sin(a)
            dot = ca * sun_dx + sa * sun_dy
            c = np.clip(WOOD_SPECIES[0] * (0.98 + 0.18 * dot), 30, 252)
            py5.fill(float(c[0]), float(c[1]), float(c[2]))
            py5.vertex(CX + ca * r_in, CY + sa * r_in)
            py5.vertex(CX + ca * r_mid, CY + sa * r_mid)

    with py5.begin_shape(py5.QUAD_STRIP):
        for i in range(n_seg + 1):
            a = i * 2.0 * math.pi / n_seg
            ca, sa = math.cos(a), math.sin(a)
            dot = -(ca * sun_dx + sa * sun_dy)
            c = np.clip(WOOD_SPECIES[2] * (0.95 + 0.22 * dot), 20, 230)
            py5.fill(float(c[0]), float(c[1]), float(c[2]))
            py5.vertex(CX + ca * r_mid, CY + sa * r_mid)
            py5.vertex(CX + ca * r_out, CY + sa * r_out)

    for k in range(12):
        ang = k * math.pi / 6.0
        ca, sa = math.cos(ang), math.sin(ang)
        tx, ty = -sa, ca
        px = CX + ca * ((r_mid + r_out) * 0.5)
        py = CY + sa * ((r_mid + r_out) * 0.5)
        w1, w2, h = 11.5, 4.8, 14.0
        py5.stroke(40, 28, 18, 220)
        py5.stroke_weight(1.5)
        py5.fill(236, 210, 165) if k % 2 == 0 else py5.fill(188, 50, 38)
        with py5.begin_shape():
            py5.vertex(px - ca * h - tx * w1, py - sa * h - ty * w1)
            py5.vertex(px - ca * h + tx * w1, py - sa * h + ty * w1)
            py5.vertex(px - tx * w2, py - ty * w2)
            py5.vertex(px + ca * h + tx * w1, py + sa * h + ty * w1)
            py5.vertex(px + ca * h - tx * w1, py + sa * h - ty * w1)
            py5.vertex(px + tx * w2, py + ty * w2)
        py5.end_shape(py5.CLOSE)

    r_tick = r_out + 16.0
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        tlen = 16.0 if deg % 30 == 0 else (10.0 if deg % 15 == 0 else 5.0)
        py5.stroke(90, 72, 54, 190 if deg % 15 == 0 else 110)
        py5.stroke_weight(2.0 if deg % 30 == 0 else 1.2)
        py5.line(CX + ca * r_tick, CY + sa * r_tick,
                 CX + ca * (r_tick + tlen), CY + sa * (r_tick + tlen))


def draw_card_box(x, y, w, h, title, subtitle):
    """Draws a warm woodworking drafting apparatus card in a corner."""
    py5.no_stroke()
    py5.fill(60, 46, 32, 32)
    py5.rect(x + 8, y + 8, w, h, 8)
    py5.stroke(135, 110, 82, 210)
    py5.stroke_weight(2.2)
    py5.fill(250, 246, 238, 240)
    py5.rect(x, y, w, h, 8)
    py5.stroke(185, 162, 132, 150)
    py5.stroke_weight(1.2)
    py5.no_fill()
    py5.rect(x + 10, y + 10, w - 20, h - 20, 4)
    py5.fill(78, 58, 42)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(21)
    py5.text(title, x + 26, y + 22)
    py5.fill(168, 52, 40)
    py5.text_size(15)
    py5.text(subtitle, x + 26, y + 50)
    py5.stroke(170, 145, 115, 160)
    py5.stroke_weight(1.4)
    py5.line(x + 24, y + 76, x + w - 24, y + 76)


def draw_kiku_jutsu_apparatuses(tau, sun_angle):
    """Draws four balanced Kiku-jutsu Japanese carpentry & Kumiko joinery telemetry apparatuses."""
    omega = 2.0 * math.pi
    cw = 760
    ch_top = 835
    ch_bot = 845

    # --- Top-Left Card (y=210..1045): FIG. 01 MITSUKUDE-GUMI & FIG. 02 BEVEL GAUGE ---
    x1, y1 = 110, 210
    draw_card_box(x1, y1, cw, ch_top,
                  "FIG. 01 // MITSUKUDE-GUMI TRIPLE LAP JOINT",
                  "THREE-AXIS 60 DEG INTERLOCKING MORTISE-AND-TENON (SHIGUCHI)")

    jcx = x1 + 225
    jcy = y1 + 235
    sep = 28.0 * (0.5 + 0.5 * math.sin(omega * tau))
    angles = [0.0, math.pi / 3.0, 2.0 * math.pi / 3.0]
    species_cols = [(234, 206, 160), (196, 124, 68), (104, 78, 56)]
    labels = [
        "SHITA-ZAN (BASE LATH // 0.0 DEG)",
        "NAKA-ZAN  (MID LATH  // 60.0 DEG)",
        "UWA-ZAN   (CAP LATH  // 120.0 DEG)",
    ]

    for idx in range(3):
        ang = angles[idx]
        ox = math.cos(ang + math.pi / 2.0) * (idx - 1) * sep
        oy = math.sin(ang + math.pi / 2.0) * (idx - 1) * sep
        py5.push_matrix()
        py5.translate(jcx + ox, jcy + oy)
        py5.rotate(ang)
        py5.stroke(60, 42, 26, 220)
        py5.stroke_weight(1.8)
        c = species_cols[idx]
        py5.fill(c[0], c[1], c[2], 235)
        py5.rect(-135, -14, 270, 28, 2)
        py5.fill(40, 68, 98, 215)
        py5.rect(-16, -14 if idx < 2 else 0, 32, 14)
        py5.pop_matrix()

    tx = x1 + 425
    py5.fill(65, 50, 36)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(16)
    py5.text(f"NOTCH CLEARANCE : {sep * 0.08:.2f} mm", tx, y1 + 102)
    py5.text("KERF TOLERANCE  : +/- 0.03 mm", tx, y1 + 134)
    py5.text("LATH THICKNESS  : 3.60 mm (1 BU 2 RIN)", tx, y1 + 166)
    py5.text("LATH DEPTH      : 12.0 mm (4 BU)", tx, y1 + 198)
    for idx, lbl in enumerate(labels):
        c = species_cols[idx]
        py5.fill(c[0], c[1], c[2])
        py5.stroke(60, 42, 26)
        py5.rect(tx, y1 + 240 + idx * 35, 20, 18, 2)
        py5.fill(65, 50, 36)
        py5.no_stroke()
        py5.text(lbl, tx + 30, y1 + 240 + idx * 35)

    py5.stroke(170, 145, 115, 160)
    py5.stroke_weight(1.4)
    py5.line(x1 + 24, y1 + 405, x1 + cw - 24, y1 + 405)
    py5.fill(78, 58, 42)
    py5.text_size(20)
    py5.text("FIG. 02 // KATAGI & KANNA BEVEL CHISEL BLOCK", x1 + 26, y1 + 425)
    py5.fill(168, 52, 40)
    py5.text_size(15)
    py5.text("TRIGONOMETRIC MITRE CHAMFER SPECTRUM (15 / 22.5 / 30 / 45 / 60 DEG)", x1 + 26, y1 + 452)

    bcx = x1 + 225
    bcy = y1 + 765
    r_arc = 220.0
    py5.no_fill()
    py5.stroke(120, 96, 72, 180)
    py5.stroke_weight(2.0)
    py5.arc(bcx, bcy, r_arc * 2, r_arc * 2, -math.pi * 0.86, -math.pi * 0.14)

    bevel_angles = [
        (15.0, "15.0 DEG // RINDO STAR TIP", (188, 50, 38)),
        (22.5, "22.5 DEG // YAE-ASANOHA LEAF", (40, 68, 98)),
        (30.0, "30.0 DEG // ASANOHA SPINE", (196, 124, 68)),
        (45.0, "45.0 DEG // GOMA-GARA LOCK", (104, 78, 56)),
        (60.0, "60.0 DEG // MITSUKUDE FRAME", (82, 118, 86)),
    ]
    active_idx = int((tau * 5.0) % 5)
    for idx, (deg, name, col) in enumerate(bevel_angles):
        rad = -math.pi + math.radians(deg + 15.0)
        px = bcx + math.cos(rad) * r_arc
        py = bcy + math.sin(rad) * r_arc
        is_act = (idx == active_idx)
        py5.stroke(col[0], col[1], col[2], 240 if is_act else 150)
        py5.stroke_weight(4.0 if is_act else 2.0)
        py5.line(bcx, bcy, px, py)
        py5.fill(col[0], col[1], col[2])
        py5.no_stroke()
        py5.circle(px, py, 13 if is_act else 8)

        ly = y1 + 508 + idx * 54
        py5.fill(col[0], col[1], col[2], 240 if is_act else 160)
        py5.rect(x1 + 420, ly, 16, 30, 2)
        py5.fill(45, 32, 20 if is_act else 95)
        py5.text_size(16)
        py5.text(name, x1 + 448, ly + 6)

    # --- Bottom-Left Card (y=1085..1930): FIG. 03 KANNA HAND-PLANE & MOTIF TAXONOMY ---
    x2, y2 = 110, 1085
    draw_card_box(x2, y2, cw, ch_bot,
                  "FIG. 03 // KANNA SHAVING & HIKOKOMI JIG KINEMATICS",
                  "MICRON-THICK HINOKI SURFACE FINISHING & THICKNESS CALIBRATION")

    # Animated Kanna Hand-Plane Block sliding across a Hinoki Lath
    k_slide = 110.0 * math.sin(omega * tau)
    base_y = y2 + 250
    # Workbench planing board (Kezuridai)
    py5.stroke(78, 58, 42, 220)
    py5.stroke_weight(2.0)
    py5.fill(196, 124, 68, 220)
    py5.rect(x2 + 45, base_y + 18, 670, 32, 3)
    # Hinoki lath being planed
    py5.fill(234, 206, 160, 240)
    py5.rect(x2 + 85, base_y, 590, 18, 2)
    # Kanna wooden body (Dai) + Laminated Steel Blade (Kanna-ba)
    kx = x2 + 360 + k_slide
    py5.fill(104, 78, 56, 245)
    py5.rect(kx - 95, base_y - 46, 190, 46, 4)
    # Angled steel blade at 38 degrees
    py5.stroke(40, 68, 98, 240)
    py5.stroke_weight(5.0)
    py5.line(kx - 18, base_y, kx + 28, base_y - 64)
    # Curling translucent wood shaving ribbon (Kanna-kuzu) lifting from blade mouth
    py5.no_fill()
    py5.stroke(234, 206, 160, 230)
    py5.stroke_weight(2.6)
    with py5.begin_shape():
        for s_i in range(28):
            st = s_i / 27.0
            ang_curl = st * 2.4 * math.pi + tau * omega
            r_curl = 38.0 * (1.0 - 0.55 * st)
            cx_s = kx - 16 - 42.0 * st + math.cos(ang_curl) * r_curl * 0.4
            cy_s = base_y - 12 - 58.0 * st - abs(math.sin(ang_curl)) * r_curl
            py5.vertex(cx_s, cy_s)
    py5.end_shape()

    py5.no_stroke()
    py5.fill(65, 50, 36)
    py5.text_size(16)
    py5.text(f"KANNA STROKE VELOCITY : {abs(math.cos(omega*tau))*185.0:5.1f} mm/s   //   SHAVING THICKNESS : 8.5 microns", x2 + 48, base_y + 72)

    # Lower half of Bottom-Left Card: 4 Kumiko Motif Medallions
    py5.stroke(170, 145, 115, 160)
    py5.stroke_weight(1.4)
    py5.line(x2 + 24, y2 + 375, x2 + cw - 24, y2 + 375)
    py5.fill(78, 58, 42)
    py5.text_size(20)
    py5.text("FIG. 04 // TRADITIONAL TSUKEKO INFILL TAXONOMY", x2 + 26, y2 + 395)
    py5.fill(168, 52, 40)
    py5.text_size(15)
    py5.text("FOUR CONCENTRIC SYMMETRY RINGS OF THE ENSO-RANMA TRANSOM", x2 + 26, y2 + 422)

    motif_specs = [
        ("01. KASANE-ASANOHA", "LAYERED HEMP STAR", (188, 50, 38)),
        ("02. FUTAE-GOMA", "SESAME MORTISE LOCK", (40, 68, 98)),
        ("03. SAKURA-RINDO", "GENTIAN BLOSSOM", (196, 124, 68)),
        ("04. KAGE-ASANOHA", "SHADOW APERTURE", (82, 118, 86)),
    ]
    for m_i, (m_title, m_sub, m_col) in enumerate(motif_specs):
        mx = x2 + 112 + m_i * 178
        my = y2 + 575
        mr = 66.0
        py5.stroke(96, 74, 52, 210)
        py5.stroke_weight(2.2)
        py5.fill(245, 238, 224)
        py5.circle(mx, my, mr * 2)
        # Mini hexagonal Kumiko star inside medallion
        for k_s in range(6):
            sa = k_s * math.pi / 3.0 + tau * omega * 0.5
            sa2 = (k_s + 1) * math.pi / 3.0 + tau * omega * 0.5
            py5.stroke(104, 78, 56, 200)
            py5.stroke_weight(2.0)
            py5.line(mx, my, mx + math.cos(sa) * mr, my + math.sin(sa) * mr)
            r_in_m = mr * (0.35 + 0.12 * m_i)
            py5.stroke(m_col[0], m_col[1], m_col[2], 235)
            py5.stroke_weight(2.8)
            py5.line(mx + math.cos(sa) * r_in_m, my + math.sin(sa) * r_in_m,
                     mx + math.cos(sa2) * r_in_m, my + math.sin(sa2) * r_in_m)

        py5.no_stroke()
        py5.fill(58, 42, 28)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.text_size(14)
        py5.text(m_title, mx, my + mr + 18)
        py5.fill(m_col[0], m_col[1], m_col[2])
        py5.text_size(13)
        py5.text(m_sub, mx, my + mr + 40)

    py5.text_align(py5.LEFT, py5.TOP)

    # --- Top-Right Card (y=210..1045): FIG. 05 ASANOHA GEOMETRY & FIG. 06 TIMBER COMPASS ---
    x3, y3 = WIDTH - cw - 110, 210
    draw_card_box(x3, y3, cw, ch_top,
                  "FIG. 05 // ASANOHA TRIGONOMETRIC PROOF",
                  "SASHIGANE CARPENTER SQUARE RATIO: L1 : L2 : L3 = 1 : 1/SQRT(3) : 1/2")

    tcx3 = x3 + 215
    tcy3 = y3 + 250
    R3 = 132.0
    tv = [
        (tcx3 + R3 * math.cos(-math.pi / 2.0 + k * 2.0 * math.pi / 3.0),
         tcy3 + R3 * math.sin(-math.pi / 2.0 + k * 2.0 * math.pi / 3.0))
        for k in range(3)
    ]
    py5.stroke(78, 58, 42, 230)
    py5.stroke_weight(3.5)
    py5.fill(242, 232, 212, 160)
    py5.triangle(tv[0][0], tv[0][1], tv[1][0], tv[1][1], tv[2][0], tv[2][1])

    b_t = 0.5 + 0.5 * math.sin(omega * tau)
    for k in range(3):
        va = tv[k]
        vb = tv[(k + 1) % 3]
        vm = ((va[0] + vb[0]) * 0.5, (va[1] + vb[1]) * 0.5)
        py5.stroke(188, 50, 38, 220)
        py5.stroke_weight(2.6)
        py5.line(va[0], va[1], tcx3, tcy3)
        py5.stroke(40, 68, 98, 210)
        py5.stroke_weight(2.2)
        py5.line(vm[0], vm[1], tcx3, tcy3)
        r_g = 0.30 + 0.25 * b_t
        g1 = (va[0] + (tcx3 - va[0]) * r_g, va[1] + (tcy3 - va[1]) * r_g)
        g2 = (vb[0] + (tcx3 - vb[0]) * r_g, vb[1] + (tcy3 - vb[1]) * r_g)
        py5.stroke(104, 78, 56, 230)
        py5.stroke_weight(3.0)
        py5.line(g1[0], g1[1], g2[0], g2[1])

    rx3 = x3 + 390
    py5.fill(65, 50, 36)
    py5.no_stroke()
    py5.text_size(16)
    py5.text(f"MODULE PITCH (a)   : {TRI_SIDE:.1f} px", rx3, y3 + 102)
    py5.text(f"BISECTOR a/SQRT(3) : {TRI_SIDE/math.sqrt(3):.1f} px", rx3, y3 + 136)
    py5.text(f"APOTHEM a/2*SQRT(3): {TRI_SIDE/(2*math.sqrt(3)):.1f} px", rx3, y3 + 170)
    py5.text(f"GOMA SLIDE RATIO   : {0.30 + 0.25*b_t:.3f} a", rx3, y3 + 204)
    py5.fill(188, 50, 38)
    py5.text("DIHEDRAL MITRE     : 30.0 + 30.0 = 60.0 DEG", rx3, y3 + 246)
    py5.fill(40, 68, 98)
    py5.text("APEX CONVERGENCE   : 6 x 60.0 = 360.0 DEG", rx3, y3 + 280)
    py5.fill(78, 58, 42)
    py5.text("FASTENERS / GLUE   : 0 (SELF-LOCKING)", rx3, y3 + 314)

    py5.stroke(170, 145, 115, 160)
    py5.stroke_weight(1.4)
    py5.line(x3 + 24, y3 + 405, x3 + cw - 24, y3 + 405)
    py5.fill(78, 58, 42)
    py5.text_size(20)
    py5.text("FIG. 06 // TIMBER SPECIES & SHOJI SUNLIGHT COMPASS", x3 + 26, y3 + 425)
    py5.fill(168, 52, 40)
    py5.text_size(15)
    py5.text("HYGROSCOPIC GRAIN DENSITY & OBLIQUE SOLAR RELIEF ILLUMINATION", x3 + 26, y3 + 452)

    ccx = x3 + 195
    ccy = y3 + 640
    cr = 112.0
    py5.stroke(120, 96, 72, 190)
    py5.stroke_weight(2.0)
    py5.fill(245, 238, 224)
    py5.circle(ccx, ccy, cr * 2)
    py5.stroke(170, 148, 120, 140)
    py5.circle(ccx, ccy, cr * 1.35)
    py5.line(ccx - cr - 12, ccy, ccx + cr + 12, ccy)
    py5.line(ccx, ccy - cr - 12, ccx, ccy + cr + 12)

    sx_tip = ccx + math.cos(sun_angle) * (cr - 10)
    sy_tip = ccy + math.sin(sun_angle) * (cr - 10)
    py5.stroke(188, 50, 38, 240)
    py5.stroke_weight(4.0)
    py5.line(ccx, ccy, sx_tip, sy_tip)
    py5.fill(235, 165, 45)
    py5.stroke(120, 45, 25)
    py5.stroke_weight(1.8)
    py5.circle(sx_tip, sy_tip, 18)
    py5.fill(65, 48, 32)
    py5.circle(ccx, ccy, 10)

    timber_info = [
        (0, "AKITA HINOKI CYPRESS // S.G. 0.41"),
        (1, "KEYAKI ZELKOVA HEART // S.G. 0.62"),
        (2, "JINDAI-SUGI BOG CEDAR // S.G. 0.38"),
        (3, "AIZOME INDIGO HINOKI // DYED CORE"),
        (4, "HON-SHU VERMILION // LACQUER LATH"),
        (5, "WAKAKUSA CELADON // DYED CYPRESS"),
    ]
    tx4 = x3 + 345
    for idx, (s_idx, label) in enumerate(timber_info):
        by = y3 + 498 + idx * 50
        rgb = WOOD_SPECIES[s_idx]
        py5.stroke(65, 48, 32, 200)
        py5.stroke_weight(1.5)
        py5.fill(float(rgb[0]), float(rgb[1]), float(rgb[2]))
        py5.rect(tx4, by, 48, 25, 3)
        py5.stroke(255, 248, 230, 110)
        py5.line(tx4 + 4, by + 9, tx4 + 44, by + 9)
        py5.line(tx4 + 4, by + 17, tx4 + 44, by + 17)
        py5.no_stroke()
        py5.fill(60, 44, 30)
        py5.text_size(15)
        py5.text(label, tx4 + 62, by + 4)

    # --- Bottom-Right Card (y=1085..1930): FIG. 07 SASHIGANE SQUARE & LOCK WAVEFORM ---
    x4, y4 = WIDTH - cw - 110, 1085
    draw_card_box(x4, y4, cw, ch_bot,
                  "FIG. 07 // SASHIGANE CARPENTER SQUARE & URA-ME SCALE",
                  "SQRT(2) & SQRT(3) TRIGONOMETRIC LAYOUT RULE FOR HEXAGONAL MITRES")

    # Draw L-shaped steel Sashigane carpenter's square with graduation ticks
    sq_x = x4 + 55
    sq_y = y4 + 115
    py5.stroke(45, 55, 68, 230)
    py5.stroke_weight(2.0)
    py5.fill(215, 222, 228, 240)
    # Horizontal arm (Omote-me) and vertical arm (Ura-me)
    py5.rect(sq_x, sq_y, 640, 34, 2)
    py5.rect(sq_x, sq_y + 34, 34, 210, 2)
    for t_i in range(0, 620, 20):
        t_h = 18 if t_i % 100 == 0 else (12 if t_i % 50 == 0 else 7)
        py5.line(sq_x + 15 + t_i, sq_y, sq_x + 15 + t_i, sq_y + t_h)
    for t_j in range(0, 190, 20):
        t_w = 18 if t_j % 100 == 0 else 9
        py5.line(sq_x, sq_y + 45 + t_j, sq_x + t_w, sq_y + 45 + t_j)

    # Animated trigonometric pitch chord across the Sashigane arms
    chord_x = sq_x + 180 + 380 * (0.5 + 0.5 * math.cos(omega * tau))
    chord_y = sq_y + 220
    py5.stroke(188, 50, 38, 230)
    py5.stroke_weight(3.2)
    py5.line(sq_x + 34, chord_y, chord_x, sq_y + 34)
    py5.fill(188, 50, 38)
    py5.no_stroke()
    py5.circle(chord_x, sq_y + 34, 11)
    py5.circle(sq_x + 34, chord_y, 11)

    py5.fill(65, 50, 36)
    py5.text_size(16)
    py5.text(f"KIKU-JUTSU KOU-BAI (PITCH) : {math.degrees(math.atan2(186.0, chord_x - sq_x - 34)):5.2f} DEG", sq_x + 65, sq_y + 72)
    py5.text("URA-ME SCALE FACTOR        : 1.41421356 (SQRT 2) / 1.73205081 (SQRT 3)", sq_x + 65, sq_y + 104)
    py5.text("SHOJI ACOUSTIC DAMPING     : -14.2 dB @ 1.0 kHz (OPEN-CELL KOZO FIBER)", sq_x + 65, sq_y + 136)
    py5.text("STRUCTURAL REDUNDANCY      : 546 INTERLOCKING BEVEL CONTACTS", sq_x + 65, sq_y + 168)

    # Lower half of Bottom-Right Card: Radial Mortise Compression Harmonic Waveform
    py5.stroke(170, 145, 115, 160)
    py5.stroke_weight(1.4)
    py5.line(x4 + 24, y4 + 375, x4 + cw - 24, y4 + 375)
    py5.fill(78, 58, 42)
    py5.text_size(20)
    py5.text("FIG. 08 // RADIAL TSUKEKO COMPRESSION WAVEFORM", x4 + 26, y4 + 395)
    py5.fill(168, 52, 40)
    py5.text_size(15)
    py5.text("HARMONIC ELASTIC STRAIN FIELD SIGMA(r, t) ACROSS FOUR LATTICE RINGS", x4 + 26, y4 + 422)

    wx0, wy0, ww, wh = x4 + 55, y4 + 475, 650, 260
    py5.stroke(145, 122, 95, 180)
    py5.stroke_weight(1.6)
    py5.fill(245, 239, 228)
    py5.rect(wx0, wy0, ww, wh, 4)
    # Grid lines inside plot
    py5.stroke(210, 195, 175, 140)
    py5.stroke_weight(1.0)
    for gy_i in range(1, 4):
        py5.line(wx0, wy0 + gy_i * wh / 4.0, wx0 + ww, wy0 + gy_i * wh / 4.0)
    for gx_i in range(1, 6):
        py5.line(wx0 + gx_i * ww / 6.0, wy0, wx0 + gx_i * ww / 6.0, wy0 + wh)

    # Plot 3 harmonic curves (Asanoha Spine, Goma Lock, Rindo Star)
    curve_cols = [(188, 50, 38), (40, 68, 98), (82, 118, 86)]
    for c_idx, col in enumerate(curve_cols):
        py5.no_fill()
        py5.stroke(col[0], col[1], col[2], 230)
        py5.stroke_weight(3.0)
        with py5.begin_shape():
            for p_i in range(66):
                u = p_i / 65.0
                px_w = wx0 + u * ww
                val = math.sin(omega * tau - u * 5.0 + c_idx * 1.1) * math.cos(u * 2.5 - omega * tau * 0.5)
                py_w = wy0 + wh * 0.5 - val * (wh * 0.36)
                py5.vertex(px_w, py_w)
        py5.end_shape()

    py5.no_stroke()
    py5.fill(65, 50, 36)
    py5.text_size(15)
    py5.text("RING 01: KASANE CORE (RED)   //   RING 02: GOMA LOCK (INDIGO)   //   RING 04: KAGE BORDER (MOSS)", wx0, wy0 + wh + 22)


def draw_archival_border_and_typography(tau):
    """Draws double-ruled museum border and scholarly typography using clean ASCII glyphs."""
    py5.no_fill()
    py5.stroke(96, 74, 52, 215)
    py5.stroke_weight(3.5)
    py5.rect(64, 64, WIDTH - 128, HEIGHT - 128, 6)

    py5.stroke(148, 122, 92, 165)
    py5.stroke_weight(1.5)
    py5.rect(78, 78, WIDTH - 156, HEIGHT - 156, 4)

    py5.fill(58, 42, 28)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(38)
    py5.text("KUMIKO-ZAIKU // TRADITIONAL JAPANESE MICRO-WOODWORKING JOINERY", WIDTH / 2.0, 98)

    py5.fill(168, 52, 40)
    py5.text_size(21)
    py5.text("MITSUKUDE-KIKKO LATTICE - ASANOHA & GOMA-GARA INFILL - KIKU-JUTSU TRIGONOMETRIC CARPENTRY", WIDTH / 2.0, 150)

    py5.fill(78, 58, 42)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(20)
    py5.text("SPECIES: AKITA HINOKI CYPRESS / JINDAI-SUGI BOG CEDAR / KEYAKI ZELKOVA / AIZOME INDIGO // FASTENERS: NONE", 108, HEIGHT - 88)

    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(f"4K GENERATIVE PROCEDURAL CRAFT // HARMONIC PHASE TAU = {tau:.3f} (12.0s @ 60FPS)", WIDTH - 108, HEIGHT - 88)


def finish_and_encode():
    global START_TIME
    total_elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        str(OUTPUT_MP4)
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")

    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

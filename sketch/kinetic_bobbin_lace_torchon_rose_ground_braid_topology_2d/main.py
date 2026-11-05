# py5 Media Art — Autonomous Animation
# Work: kinetic_bobbin_lace_torchon_rose_ground_braid_topology_2d
# Genre: Textile / Calligraphy / Procedural Craft (Genre 5)
# Background Polarity: Dark (#060912 Deep Bruges Kantkussen Velvet & Venetian Lace Obsidian)

from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import py5

WORK_NAME = "kinetic_bobbin_lace_torchon_rose_ground_braid_topology_2d"
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC  # 720 frames

OUT_DIR = Path(__file__).parent
FRAMES_DIR = OUT_DIR / "frames"
PREVIEW_PATH = OUT_DIR / f"{WORK_NAME}_p1.png"
VIDEO_PATH = OUT_DIR / "output.mp4"

# Palette — Deep Bruges Kantkussen Velvet & Venetian Merletto Obsidian (#060912)
BG_OBSIDIAN = (6, 9, 18)
CARD_BG = (11, 16, 30)
CARD_HEADER_BG = (17, 25, 45)
PILLOW_BG = (9, 14, 27)
PILLOW_RIM = (24, 34, 58)

# Silk, Metallic Thread & OIDFA Stitch Chromatics
GOLD_CORDONNET = (250, 198, 66)
GOLD_BRIGHT = (255, 232, 136)
LINEN_IVORY = (238, 242, 250)
SILK_CRIMSON = (246, 56, 132)
SILK_CERULEAN = (42, 212, 254)
SILK_EMERALD = (24, 232, 166)
SILK_VIOLET = (174, 88, 252)
BOBBIN_WOOD = (214, 152, 78)
BRASS_PIN = (252, 208, 84)

INK_IVORY = (236, 240, 248)
INK_SILVER = (166, 178, 204)
INK_MUTED = (106, 120, 148)
GRID_LINE = (24, 36, 62)
BORDER_SLATE = (48, 64, 102)

# Layout Geometry (3840 x 2160)
W, H = SIZE
CX, CY = 1920.0, 1052.0
MEDALLION_R = 735.0
INNER_R = 678.0

LEFT_X = 84.0
RIGHT_X = 2736.0
CARD_W = 1020.0
TOP_CARD_Y = 178.0
TOP_CARD_H = 884.0
BOT_CARD_Y = 1102.0
BOT_CARD_H = 884.0

SEED_OFFSET = 0
FONT_MONO = None
FONT_SANS = None

# Precomputed D_16 polar symmetry tables for fast vectorized bobbin lace rendering
N_SYM = 16
N_RING_PTS = 160
THETA_RING = np.linspace(0.0, 2.0 * np.pi, N_RING_PTS + 1, dtype=np.float32)


def setup():
    global SEED_OFFSET, FONT_MONO, FONT_SANS
    py5.size(W, H, py5.P2D)
    py5.pixel_density(1)
    py5.smooth(8)
    SEED_OFFSET = int(time.time() * 1000) % 100000
    FONT_MONO = py5.create_font("Menlo", 18)
    FONT_SANS = py5.create_font("Helvetica", 20)

    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


def draw_frame_border_and_header(phi: float, active_word_idx: int):
    py5.no_fill()
    py5.stroke(*BORDER_SLATE, 220)
    py5.stroke_weight(2.0)
    py5.rect(42, 36, W - 84, H - 72, 8)
    py5.stroke(*GOLD_CORDONNET, 130)
    py5.stroke_weight(1.0)
    py5.rect(50, 44, W - 100, H - 88, 6)

    py5.fill(*CARD_HEADER_BG, 238)
    py5.stroke(*BORDER_SLATE, 210)
    py5.stroke_weight(1.5)
    py5.rect(84, 58, W - 168, 94, 6)

    py5.text_font(FONT_SANS)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(27)
    py5.text(
        "BOBBIN LACE TORCHON & ROSE GROUND BRAID TOPOLOGY // MERLETTO A FUSELLI & KANTWERK",
        114,
        72,
    )

    braid_words = [
        ("CLOTH STITCH (TOILE)", "W = C * T * C = sigma_2^-1 (sigma_1 sigma_3) sigma_2^-1"),
        ("HALF-STITCH (GRILLE)", "W = C * T = sigma_2^-1 (sigma_1 sigma_3)"),
        ("WHOLE-STITCH (POINT ENTIER)", "W = C * T * C * T = (sigma_2^-1 sigma_1 sigma_3)^2"),
        ("ROSE GROUND (FOND VIERGE)", "W = (C*T)^2 [PIN] (C*T)^2 // D_4 ROSETTE CELL"),
    ]
    w_name, w_alg = braid_words[active_word_idx % len(braid_words)]

    py5.text_font(FONT_MONO)
    py5.fill(*INK_SILVER)
    py5.text_size(16)
    py5.text(
        f"SYMMETRY: D_16 CONTINUOUS-THREAD GUIPURE   |   ACTIVE STITCH: {w_name}   |   BRAID WORD: {w_alg}",
        114,
        114,
    )

    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*SILK_CERULEAN)
    py5.text_size(17)
    py5.text("LE POMPE (VENICE, 1557) // BRUGES KANT // IRVINE-RUSKEY BRAID GRAPH (2014)", W - 114, 76)
    py5.fill(*SILK_CRIMSON)
    py5.text_size(15)
    py5.text(
        f"BOBBINS: 32 PAIRS (64 SPINDLES)   |   PINS: 192 BRASS   |   PHASE = {phi / (2.0 * np.pi) * 100.0:05.1f}%",
        W - 114,
        114,
    )


def draw_flank_card(x: float, y: float, w: float, h: float, code1: str, title1: str, code2: str, title2: str):
    py5.fill(*CARD_BG, 242)
    py5.stroke(*BORDER_SLATE, 220)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, y + 2, w - 4, 42, 6)
    py5.stroke(*BORDER_SLATE, 180)
    py5.stroke_weight(1.0)
    py5.line(x, y + 44, x + w, y + 44)

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*GOLD_CORDONNET)
    py5.text_size(16)
    py5.text(code1, x + 18, y + 23)
    py5.fill(*INK_IVORY)
    py5.text_size(16)
    py5.text(title1, x + 112, y + 23)

    mid_y = y + h * 0.5
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, mid_y, w - 4, 42)
    py5.stroke(*BORDER_SLATE, 180)
    py5.stroke_weight(1.0)
    py5.line(x, mid_y, x + w, mid_y)
    py5.line(x, mid_y + 42, x + w, mid_y + 42)

    py5.fill(*GOLD_CORDONNET)
    py5.text(code2, x + 18, mid_y + 21)
    py5.fill(*INK_IVORY)
    py5.text(title2, x + 112, mid_y + 21)


def draw_central_bobbin_lace_medallion(phi: float):
    # Outer turned mahogany & brass Kantkussen bezel
    py5.fill(*PILLOW_RIM)
    py5.stroke(*BORDER_SLATE, 240)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    # Inner dark indigo velvet lace pillow
    py5.fill(*PILLOW_BG)
    py5.stroke(*GOLD_CORDONNET, 215)
    py5.stroke_weight(2.2)
    py5.circle(CX, CY, INNER_R * 2.0)

    # Subtle pricked parchment polar grid rings & 32 radial guidelines
    py5.no_fill()
    py5.stroke(*GRID_LINE, 155)
    py5.stroke_weight(1.0)
    for r_grid in (110.0, 210.0, 315.0, 420.0, 520.0):
        py5.circle(CX, CY, r_grid * 2.0)

    rad_ang = np.linspace(0.0, 2.0 * np.pi, 32, endpoint=False)
    rad_segs = np.zeros((32, 4), dtype=np.float32)
    rad_segs[:, 0] = CX + 48.0 * np.cos(rad_ang)
    rad_segs[:, 1] = CY + 48.0 * np.sin(rad_ang)
    rad_segs[:, 2] = CX + 545.0 * np.cos(rad_ang)
    rad_segs[:, 3] = CY + 545.0 * np.sin(rad_ang)
    py5.lines(rad_segs)

    # 1. Draw 32 Swinging Wooden Bobbins (Fuselli / Klosjes) around the outer cushion ring (r = 548..652 px)
    n_bobbins = 32
    bob_base_angles = np.linspace(0.0, 2.0 * np.pi, n_bobbins, endpoint=False)
    bob_quads_wood = []
    bob_quads_spool = []
    thread_segs = []
    bead_centers = []

    for b_i, b_ang in enumerate(bob_base_angles):
        # Alternating pairs cross & twist harmonically!
        pair_sign = 1.0 if (b_i % 2 == 0) else -1.0
        swing = 0.038 * pair_sign * np.sin(2.0 * phi + (b_i // 2) * 0.785)
        ang = b_ang + swing
        ca, sa = np.cos(ang), np.sin(ang)
        pa, qa = -sa, ca  # tangent vector

        # Anchor pin on outer scallop ring (r = 515)
        pin_x = CX + 515.0 * ca
        pin_y = CY + 515.0 * sa
        neck_x = CX + 566.0 * ca
        neck_y = CY + 566.0 * sa
        thread_segs.append([pin_x, pin_y, neck_x, neck_y])

        # Spool wound with silk/gold thread (r = 566..598, half-width = 4.5)
        r_s0, r_s1, hw_s = 566.0, 598.0, 4.5
        bob_quads_spool.append(
            [
                [CX + r_s0 * ca - hw_s * pa, CY + r_s0 * sa - hw_s * qa],
                [CX + r_s1 * ca - hw_s * pa, CY + r_s1 * sa - hw_s * qa],
                [CX + r_s1 * ca + hw_s * pa, CY + r_s1 * sa + hw_s * qa],
                [CX + r_s0 * ca + hw_s * pa, CY + r_s0 * sa + hw_s * qa],
            ]
        )

        # Turned boxwood barrel handle (r = 598..642, half-width = 6.2)
        r_w0, r_w1, hw_w = 598.0, 642.0, 6.2
        bob_quads_wood.append(
            [
                [CX + r_w0 * ca - hw_w * pa, CY + r_w0 * sa - hw_w * qa],
                [CX + r_w1 * ca - hw_w * pa, CY + r_w1 * sa - hw_w * qa],
                [CX + r_w1 * ca + hw_w * pa, CY + r_w1 * sa + hw_w * qa],
                [CX + r_w0 * ca + hw_w * pa, CY + r_w0 * sa + hw_w * qa],
            ]
        )
        bead_centers.append((CX + 650.0 * ca, CY + 650.0 * sa, b_i))

    py5.stroke(*LINEN_IVORY, 210)
    py5.stroke_weight(1.6)
    py5.lines(np.array(thread_segs, dtype=np.float32))

    py5.no_stroke()
    py5.fill(*GOLD_CORDONNET, 240)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(bob_quads_spool, dtype=np.float32).reshape(-1, 2))

    py5.fill(*BOBBIN_WOOD, 245)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(bob_quads_wood, dtype=np.float32).reshape(-1, 2))

    # Venetian glass spangle beads at tail of each bobbin
    for bx_p, by_p, b_i in bead_centers:
        b_col = SILK_CRIMSON if (b_i % 3 == 0) else (SILK_CERULEAN if (b_i % 3 == 1) else SILK_EMERALD)
        py5.fill(*b_col)
        py5.stroke(*GOLD_BRIGHT, 200)
        py5.stroke_weight(1.2)
        py5.circle(bx_p, by_p, 11.0)

    # 2. Draw 16 Outer Torchon Coquille (Scallop Fan) Edge Arches (r = 420..515 px)
    fan_segs_ivory = []
    fan_segs_gold = []
    fan_pins = []
    for s_i in range(N_SYM):
        ang_c = (s_i + 0.5) * (2.0 * np.pi / N_SYM)
        pivot_x = CX + 420.0 * np.cos(ang_c)
        pivot_y = CY + 420.0 * np.sin(ang_c)
        # 9 fan ribs radiating from pivot to scallop arc at r = 490..518
        for k_rib in range(-4, 5):
            a_rib = ang_c + k_rib * 0.042
            r_rib = 516.0 - 3.2 * (k_rib**2) + 4.0 * np.sin(phi + s_i)
            rx_p = CX + r_rib * np.cos(a_rib)
            ry_p = CY + r_rib * np.sin(a_rib)
            fan_segs_ivory.append([pivot_x, pivot_y, rx_p, ry_p])
            fan_pins.append((rx_p, ry_p))
        # Cross-weft arcs across the fan
        for r_frac in (0.35, 0.65, 0.90):
            pts_arc = []
            for k_rib in range(-4, 5):
                a_rib = ang_c + k_rib * 0.042
                r_rib = 516.0 - 3.2 * (k_rib**2) + 4.0 * np.sin(phi + s_i)
                px_a = pivot_x + r_frac * (CX + r_rib * np.cos(a_rib) - pivot_x)
                py_a = pivot_y + r_frac * (CY + r_rib * np.sin(a_rib) - pivot_y)
                pts_arc.append([px_a, py_a])
            for m in range(len(pts_arc) - 1):
                fan_segs_gold.append([pts_arc[m][0], pts_arc[m][1], pts_arc[m + 1][0], pts_arc[m + 1][1]])

    py5.stroke(*LINEN_IVORY, 210)
    py5.stroke_weight(1.7)
    py5.lines(np.array(fan_segs_ivory, dtype=np.float32))

    py5.stroke(*GOLD_CORDONNET, 235)
    py5.stroke_weight(2.2)
    py5.lines(np.array(fan_segs_gold, dtype=np.float32))

    # 3. Draw Torchon Diamond & Rose Ground (Fond Vierge) Interlaced Lattice (r = 210..420 px)
    # Counter-rotating logarithmic-polar braid strands weaving through 3 concentric pin rings
    n_strands = 32
    u_rad = np.linspace(0.0, 1.0, 72, dtype=np.float32)
    r_vals = 205.0 + u_rad * 215.0
    segs_cw = []
    segs_ccw = []
    for k_s in range(n_strands):
        base_a = k_s * (2.0 * np.pi / n_strands)
        # CW spiral strand with local Cross-Twist (C-T-C-T) ripple
        theta_cw = base_a + 0.58 * u_rad + 0.024 * np.sin(8.0 * np.pi * u_rad - phi)
        pts_cw = np.column_stack((CX + r_vals * np.cos(theta_cw), CY + r_vals * np.sin(theta_cw)))
        segs_cw.append(np.hstack((pts_cw[:-1], pts_cw[1:])))

        # CCW conjugate spiral strand
        theta_ccw = base_a - 0.58 * u_rad - 0.024 * np.sin(8.0 * np.pi * u_rad + phi)
        pts_ccw = np.column_stack((CX + r_vals * np.cos(theta_ccw), CY + r_vals * np.sin(theta_ccw)))
        segs_ccw.append(np.hstack((pts_ccw[:-1], pts_ccw[1:])))

    py5.stroke(*SILK_CERULEAN, 205)
    py5.stroke_weight(1.9)
    py5.lines(np.vstack(segs_cw))

    py5.stroke(*LINEN_IVORY, 215)
    py5.stroke_weight(1.9)
    py5.lines(np.vstack(segs_ccw))

    # 4. Draw 16 Bruges Rose-Ground Spider Medallions (at r = 312 px) & Toile Guipure Petals (r = 85..205 px)
    spider_segs = []
    petal_quads_crimson = []
    petal_quads_gold = []
    rose_pins = []

    for s_i in range(N_SYM):
        ang0 = s_i * (2.0 * np.pi / N_SYM)
        # Spider cell at r = 312 px
        sx = CX + 312.0 * np.cos(ang0)
        sy = CY + 312.0 * np.sin(ang0)
        r_sp = 26.0 + 3.0 * np.cos(phi + s_i)
        for leg in range(8):
            la = ang0 + leg * (np.pi / 4.0)
            lx = sx + r_sp * np.cos(la)
            ly = sy + r_sp * np.sin(la)
            spider_segs.append([sx, sy, lx, ly])
        rose_pins.append((sx, sy))

        # Inner dense Cloth-Stitch (Toile) petal blade spanning r = 82..205 px
        u_p = np.linspace(0.0, 1.0, 18, dtype=np.float32)
        r_p = 82.0 + u_p * 123.0
        w_p = 0.115 * np.sin(np.pi * u_p) * (1.0 + 0.08 * np.sin(phi + s_i))
        for m in range(len(u_p) - 1):
            r_a, r_b = r_p[m], r_p[m + 1]
            wa, wb = w_p[m], w_p[m + 1]
            q_pet = [
                [CX + r_a * np.cos(ang0 - wa), CY + r_a * np.sin(ang0 - wa)],
                [CX + r_b * np.cos(ang0 - wb), CY + r_b * np.sin(ang0 - wb)],
                [CX + r_b * np.cos(ang0 + wb), CY + r_b * np.sin(ang0 + wb)],
                [CX + r_a * np.cos(ang0 + wa), CY + r_a * np.sin(ang0 + wa)],
            ]
            if (s_i + m) % 2 == 0:
                petal_quads_crimson.append(q_pet)
            else:
                petal_quads_gold.append(q_pet)

    py5.no_stroke()
    py5.fill(*SILK_CRIMSON, 225)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(petal_quads_crimson, dtype=np.float32).reshape(-1, 2))

    py5.fill(*GOLD_CORDONNET, 235)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(petal_quads_gold, dtype=np.float32).reshape(-1, 2))

    py5.stroke(*SILK_EMERALD, 235)
    py5.stroke_weight(2.0)
    py5.lines(np.array(spider_segs, dtype=np.float32))

    # Heavy braided Gold Cordonnet (Gimp) contour thread weaving around the rosette & central wheel
    t_gimp = np.linspace(0.0, 2.0 * np.pi, 320, dtype=np.float32)
    r_gimp1 = 198.0 + 22.0 * np.cos(16.0 * t_gimp)
    pts_g1 = np.column_stack((CX + r_gimp1 * np.cos(t_gimp), CY + r_gimp1 * np.sin(t_gimp)))
    r_gimp2 = 418.0 + 18.0 * np.cos(16.0 * t_gimp + np.pi)
    pts_g2 = np.column_stack((CX + r_gimp2 * np.cos(t_gimp), CY + r_gimp2 * np.sin(t_gimp)))
    py5.stroke(*GOLD_BRIGHT, 250)
    py5.stroke_weight(3.0)
    py5.lines(np.hstack((pts_g1[:-1], pts_g1[1:])))
    py5.lines(np.hstack((pts_g2[:-1], pts_g2[1:])))

    # Central Point de Venise raised ring wheel (r = 0..82 px)
    py5.fill(*PILLOW_BG)
    py5.stroke(*GOLD_BRIGHT, 250)
    py5.stroke_weight(3.0)
    py5.circle(CX, CY, 164.0)
    py5.stroke(*SILK_CRIMSON, 230)
    py5.stroke_weight(2.0)
    py5.circle(CX, CY, 108.0)
    py5.fill(*GOLD_BRIGHT)
    py5.circle(CX, CY, 28.0)

    # 5. Render gleaming Brass Lace Pin Heads at all key topological vertices
    py5.fill(*BRASS_PIN)
    py5.stroke(*PILLOW_BG)
    py5.stroke_weight(1.0)
    for px_f, py_f in fan_pins[::2]:
        py5.circle(px_f, py_f, 6.0)
    for px_r, py_r in rose_pins:
        py5.circle(px_r, py_r, 9.5)

    # Bottom viewport telemetry pill inside the medallion
    badge_w = 540.0
    badge_y = CY + INNER_R - 138.0
    py5.fill(*CARD_HEADER_BG, 238)
    py5.stroke(*GOLD_CORDONNET, 210)
    py5.stroke_weight(1.5)
    py5.rect(CX - badge_w * 0.5, badge_y, badge_w, 44.0, 6)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        "D_16 KANTKUSSEN PILLOW  |  32 BOBBIN PAIRS  |  GIMP CORDONNET + ROSE GROUND",
        CX,
        badge_y + 22.0,
    )


def draw_left_top_card(phi: float):
    x, y, w, h = LEFT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 01",
        "ELEMENTARY 4-STRAND BRAID GENERATORS: CROSS (C) & TWIST (T)",
        "FIG. 02",
        "IRVINE-RUSKEY TORUS GRAPH G(V,E) OF ROSE GROUND (2014)",
    )

    # --- FIG. 01: 3 Animated 4-Strand Braid Diagrams (Cloth CTC, Half CT, Whole CTCT) ---
    bx, by, bw, bh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(bx, by, bw, bh, 6)

    stitches = [
        ("1. CLOTH / TOILE (W = C * T * C)", SILK_VIOLET, ["C", "T", "C"]),
        ("2. HALF / GRILLE (W = C * T)", SILK_EMERALD, ["C", "T", "C", "T"]),
        ("3. WHOLE / ENTIER (W = C * T * C * T)", SILK_CRIMSON, ["C", "T", "C", "T"]),
    ]
    col_w = (bw - 48.0) / 3.0
    for s_idx, (s_title, s_col, ops) in enumerate(stitches):
        sx0 = bx + 24.0 + s_idx * col_w
        cx_s = sx0 + col_w * 0.5

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.fill(*s_col)
        py5.text_size(12)
        py5.text(s_title, cx_s, by + 16.0)

        # Draw 4 vertical strands undergoing sequential C (swap 2,3) and T (swap 1,2 and 3,4)
        lane_xs = [cx_s - 72.0, cx_s - 24.0, cx_s + 24.0, cx_s + 72.0]
        strand_cols = [GOLD_CORDONNET, GOLD_BRIGHT, SILK_CERULEAN, LINEN_IVORY]
        perm = [0, 1, 2, 3]
        y_top = by + 52.0
        step_h = 58.0

        for step_i, op in enumerate(ops):
            y0_s = y_top + step_i * step_h
            y1_s = y0_s + step_h
            next_perm = list(perm)
            if op == "C":
                next_perm[1], next_perm[2] = perm[2], perm[1]
            else:
                next_perm[0], next_perm[1] = perm[1], perm[0]
                next_perm[2], next_perm[3] = perm[3], perm[2]

            # Draw strands for this step
            for lane_k in range(4):
                s_id = perm[lane_k]
                next_lane = next_perm.index(s_id)
                py5.stroke(*strand_cols[s_id], 240)
                py5.stroke_weight(3.2)
                py5.line(lane_xs[lane_k], y0_s, lane_xs[next_lane], y1_s)

            # Operation badge on left of column
            py5.fill(*CARD_HEADER_BG)
            py5.stroke(*s_col, 190)
            py5.stroke_weight(1.2)
            py5.rect(sx0 + 10.0, 0.5 * (y0_s + y1_s) - 11.0, 28.0, 22.0, 4)
            py5.fill(*INK_IVORY)
            py5.text_align(py5.CENTER, py5.CENTER)
            py5.text_size(12)
            py5.text(op, sx0 + 24.0, 0.5 * (y0_s + y1_s))
            perm = next_perm

        # Central brass pin below the crossing word
        py5.fill(*BRASS_PIN)
        py5.stroke(*GOLD_BRIGHT)
        py5.stroke_weight(1.8)
        py5.circle(cx_s, by + bh - 36.0, 14.0)

    # --- FIG. 02: Irvine-Ruskey Torus Digraph G(V, E) on [0,1]^2 Fundamental Domain ---
    mid_y = y + h * 0.5
    gx, gy, gw, gh = x + 36.0, mid_y + 62.0, 520.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(gx, gy, gw, gh, 6)

    # Draw periodic torus square boundary [u, v] in [-130..+130]
    tcx, tcy = gx + gw * 0.5, gy + gh * 0.5
    sq = 126.0
    py5.no_fill()
    py5.stroke(*GOLD_CORDONNET, 210)
    py5.stroke_weight(2.0)
    py5.rect(tcx - sq, tcy - sq, sq * 2.0, sq * 2.0)

    # 4 Rose-Ground 4-valent vertices inside the torus cell + directed pair edges
    v_nodes = [
        (tcx, tcy - 68.0, "v1 (CT)"),
        (tcx - 68.0, tcy, "v2 (CT)"),
        (tcx + 68.0, tcy, "v3 (CT)"),
        (tcx, tcy + 68.0, "v4 (CT)"),
    ]
    edges_torus = [
        (tcx - sq, tcy - sq, tcx, tcy - 68.0, SILK_CERULEAN),
        (tcx + sq, tcy - sq, tcx, tcy - 68.0, GOLD_CORDONNET),
        (tcx, tcy - 68.0, tcx - 68.0, tcy, GOLD_CORDONNET),
        (tcx, tcy - 68.0, tcx + 68.0, tcy, SILK_CERULEAN),
        (tcx - 68.0, tcy, tcx, tcy + 68.0, SILK_CRIMSON),
        (tcx + 68.0, tcy, tcx, tcy + 68.0, SILK_EMERALD),
        (tcx - 68.0, tcy, tcx - sq, tcy + sq, SILK_CERULEAN),
        (tcx + 68.0, tcy, tcx + sq, tcy + sq, GOLD_CORDONNET),
        (tcx, tcy + 68.0, tcx - sq, tcy + sq, SILK_EMERALD),
        (tcx, tcy + 68.0, tcx + sq, tcy + sq, SILK_CRIMSON),
    ]
    for x1, y1, x2, y2, ecol in edges_torus:
        py5.stroke(*ecol, 235)
        py5.stroke_weight(2.8)
        py5.line(x1, y1, x2, y2)
        # Animated traveling pulse along each directed edge
        frac_p = (phi / (2.0 * np.pi)) % 1.0
        px_e = x1 + frac_p * (x2 - x1)
        py_e = y1 + frac_p * (y2 - y1)
        py5.fill(*GOLD_BRIGHT)
        py5.no_stroke()
        py5.circle(px_e, py_e, 8.0)

    for vx, vy, v_lbl in v_nodes:
        py5.fill(*BRASS_PIN)
        py5.stroke(*INK_IVORY)
        py5.stroke_weight(1.8)
        py5.circle(vx, vy, 16.0)
        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.fill(*INK_IVORY)
        py5.text_size(11)
        py5.text(v_lbl, vx + 14.0, vy)

    # Right explanatory column for FIG. 02
    rx2 = gx + gw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(15)
    py5.text("TORUS GRAPH AXIOMS", rx2, gy + 8.0)
    axioms = [
        ("MANIFOLD", "Flat Torus T^2 = R^2 / Z^2"),
        ("VERTEX DEG", "deg+(v) = deg-(v) = 2"),
        ("BRAID GROUP", "B_4 = <sigma_1, sigma_2, sigma_3>"),
        ("YANG-BAXTER", "s1*s2*s1 = s2*s1*s2"),
        ("FAR COMMUTE", "s1 * s3 = s3 * s1 (Twist)"),
        ("CROSS OP", "C = sigma_2^-1"),
        ("TWIST OP", "T = sigma_1 * sigma_3"),
        ("PRIME LACE", "Non-separable 2-connected"),
        ("GROUND CELL", "4 Vertices / 8 Directed Arcs"),
    ]
    for i, (k_a, v_a) in enumerate(axioms):
        yy = gy + 44.0 + i * 32.0
        py5.fill(*INK_MUTED)
        py5.text_size(13)
        py5.text(k_a, rx2, yy)
        py5.fill(*(SILK_CERULEAN if i in (2, 5, 6) else INK_IVORY))
        py5.text(v_a, rx2 + 148.0, yy)


def draw_left_bottom_card(phi: float):
    x, y, w, h = LEFT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 03",
        "TURNED BOBBIN (FUSEAU / KLOSJE) & HALF-HITCH TENSION ANATOMY",
        "FIG. 04",
        "BRUGES & VENETIAN MERLETTO A FUSELLI PALETTE",
    )

    # --- FIG. 03: Horizontal Anatomical Elevation of a Turned Lace Bobbin & Murano Spangle ---
    bx, by, bw, bh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(bx, by, bw, bh, 6)

    cy_b = by + bh * 0.46
    # Draw turned boxwood & bone bobbin silhouette horizontally across bx+90 .. bx+bw-140
    # 1. Head (Kop): bx+120..165
    # 2. Neck (Hals + wound gold thread + half-hitch loop): bx+165..340
    # 3. Collar & Turned Barrel (Schacht with decorative bone rings): bx+340..710
    # 4. Tail + Brass Spangle Ring with 7 Murano glass beads: bx+710..840
    py5.stroke(*GOLD_BRIGHT, 235)
    py5.stroke_weight(2.8)
    # Thread rising to pillow pin at top-left
    py5.line(bx + 210.0, cy_b - 18.0, bx + 95.0, by + 28.0)
    py5.fill(*BRASS_PIN)
    py5.circle(bx + 95.0, by + 28.0, 12.0)

    # Wound gold thread spool on Neck
    py5.fill(*GOLD_CORDONNET)
    py5.stroke(*GOLD_BRIGHT)
    py5.stroke_weight(1.8)
    py5.rect(bx + 165.0, cy_b - 18.0, 175.0, 36.0, 6)
    # Thread winding ribs
    py5.stroke(*PILLOW_BG, 140)
    py5.stroke_weight(1.4)
    for wx in np.linspace(bx + 175.0, bx + 330.0, 22):
        py5.line(wx, cy_b - 18.0, wx, cy_b + 18.0)

    # Turned wooden Head, Collar, and Barrel
    py5.fill(*BOBBIN_WOOD)
    py5.stroke(*GOLD_BRIGHT, 210)
    py5.stroke_weight(2.0)
    py5.rect(bx + 118.0, cy_b - 28.0, 47.0, 56.0, 12)  # Head
    py5.rect(bx + 340.0, cy_b - 32.0, 38.0, 64.0, 8)  # Collar
    py5.rect(bx + 378.0, cy_b - 24.0, 330.0, 48.0, 10)  # Barrel shaft

    # Decorative inlaid bone & crimson lacquer bands on the barrel
    for rx_band, b_col in ((430.0, LINEN_IVORY), (510.0, SILK_CRIMSON), (590.0, LINEN_IVORY), (660.0, SILK_CERULEAN)):
        py5.fill(*b_col)
        py5.no_stroke()
        py5.rect(bx + rx_band, cy_b - 24.0, 18.0, 48.0)

    # Brass Wire Spangle Ring + 7 Venetian Glass Beads at right end (bx + 765)
    sp_cx = bx + 775.0
    sp_cy = cy_b + 12.0 + 6.0 * np.sin(phi * 2.0)
    py5.no_fill()
    py5.stroke(*GOLD_BRIGHT, 235)
    py5.stroke_weight(2.5)
    py5.circle(sp_cx, sp_cy, 96.0)

    bead_cols = [SILK_CRIMSON, GOLD_BRIGHT, SILK_CERULEAN, SILK_EMERALD, SILK_VIOLET, GOLD_BRIGHT, SILK_CRIMSON]
    for k_b, b_col in enumerate(bead_cols):
        ba = -0.35 * np.pi + k_b * (0.28 * np.pi)
        bx_k = sp_cx + 48.0 * np.cos(ba)
        by_k = sp_cy + 48.0 * np.sin(ba)
        py5.fill(*b_col)
        py5.stroke(*INK_IVORY)
        py5.stroke_weight(1.4)
        py5.circle(bx_k, by_k, 18.0)

    # Callout labels along bottom of FIG. 03 (evenly spaced with angled leader lines)
    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.CENTER, py5.TOP)
    callouts_f3 = [
        (bx + 142.0, bx + 118.0, "HEAD (KOP)", "Hitch Loop"),
        (bx + 252.0, bx + 305.0, "NECK & SPOOL", "Wound Silk / Gold"),
        (bx + 540.0, bx + 540.0, "TURNED BARREL", "Boxwood & Bone"),
        (bx + 775.0, bx + 785.0, "MURANO SPANGLE", "Tension Weight"),
    ]
    for target_x, lbl_x, top_s, bot_s in callouts_f3:
        py5.stroke(*BORDER_SLATE, 180)
        py5.stroke_weight(1.2)
        py5.line(target_x, cy_b + 38.0, lbl_x, by + bh - 68.0)
        py5.fill(*GOLD_BRIGHT)
        py5.text(top_s, lbl_x, by + bh - 62.0)
        py5.fill(*INK_SILVER)
        py5.text(bot_s, lbl_x, by + bh - 40.0)

    # --- FIG. 04: 6 Chromatic Swatches ---
    mid_y = y + h * 0.5
    swatches = [
        (GOLD_CORDONNET, "FIL D'OR CORDONNET", "#FAC642 // GIMP OUTLINE"),
        (LINEN_IVORY, "BRABANT FLAX LINEN", "#EEF2FA // TOILE GROUND"),
        (SILK_CRIMSON, "VENETIAN CRIMSON SILK", "#F63884 // WHOLE STITCH"),
        (SILK_CERULEAN, "ANTWERP CERULEAN", "#2AD4FE // TWIST PAIR"),
        (SILK_EMERALD, "OIDFA HALF-STITCH", "#18E8A6 // GRILLE CT"),
        (SILK_VIOLET, "OIDFA CLOTH STITCH", "#AE58FC // TOILE CTC"),
    ]
    sw_w = (w - 96.0) / 3.0
    sw_h = 152.0
    for i, (scol, sname, sdesc) in enumerate(swatches):
        col_i = i % 3
        row_i = i // 3
        bx_s = x + 36.0 + col_i * (sw_w + 12.0)
        by_s = mid_y + 62.0 + row_i * (sw_h + 18.0)
        py5.fill(*PILLOW_BG)
        py5.stroke(*BORDER_SLATE, 190)
        py5.stroke_weight(1.4)
        py5.rect(bx_s, by_s, sw_w, sw_h, 6)

        py5.fill(*scol)
        py5.no_stroke()
        py5.rect(bx_s + 14.0, by_s + 14.0, sw_w - 28.0, 66.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*INK_IVORY)
        py5.text_size(13)
        py5.text(sname, bx_s + 14.0, by_s + 92.0)
        py5.fill(*INK_SILVER)
        py5.text_size(12)
        py5.text(sdesc, bx_s + 14.0, by_s + 116.0)


def draw_right_top_card(phi: float):
    x, y, w, h = RIGHT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 05",
        "INTERNATIONAL OIDFA COLOUR-CODED WORKING DIAGRAM",
        "FIG. 06",
        "EUROPEAN BOBBIN LACE (MERLETTO / KANT) TAXONOMY (1557-2014)",
    )

    # --- FIG. 05: 4 OIDFA Color-Coded Stitch Working Diagrams ---
    ox, oy, ow, oh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(ox, oy, ow, oh, 6)

    oidfa_cells = [
        ("PURPLE: CLOTH STITCH (CTC)", SILK_VIOLET, "Worker pair passes flat through passives"),
        ("GREEN: HALF-STITCH (CT)", SILK_EMERALD, "Diagonal grille mesh; 1 pair left, 1 right"),
        ("RED: WHOLE & TWIST (CTCT)", SILK_CRIMSON, "Locked torchon stitch around brass pin"),
        ("BLUE: EXTRA TWIST (T^n)", SILK_CERULEAN, "Ticks show right-over-left twist count"),
    ]
    cw_cell = (ow - 42.0) * 0.5
    ch_cell = (oh - 42.0) * 0.5
    for idx_c, (c_title, c_col, c_desc) in enumerate(oidfa_cells):
        ci = idx_c % 2
        ri = idx_c // 2
        cx0 = ox + 14.0 + ci * (cw_cell + 14.0)
        cy0 = oy + 14.0 + ri * (ch_cell + 14.0)
        py5.fill(*CARD_HEADER_BG, 180)
        py5.stroke(*c_col, 210)
        py5.stroke_weight(1.5)
        py5.rect(cx0, cy0, cw_cell, ch_cell, 5)

        # Mini geometric stitch glyph on left of cell
        gx_c = cx0 + 64.0
        gy_c = cy0 + ch_cell * 0.54
        py5.stroke(*c_col, 250)
        py5.stroke_weight(3.0)
        py5.line(gx_c - 38.0, gy_c - 32.0, gx_c + 38.0, gy_c + 32.0)
        py5.line(gx_c - 38.0, gy_c + 32.0, gx_c + 38.0, gy_c - 32.0)
        py5.line(gx_c - 42.0, gy_c, gx_c + 42.0, gy_c)
        py5.fill(*BRASS_PIN)
        py5.stroke(*INK_IVORY)
        py5.stroke_weight(1.4)
        py5.circle(gx_c, gy_c, 12.0)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*c_col)
        py5.text_size(13)
        py5.text(c_title, cx0 + 124.0, cy0 + 24.0)
        py5.fill(*INK_IVORY)
        py5.text_size(11)
        py5.text(c_desc, cx0 + 124.0, cy0 + 56.0)
        py5.fill(*GOLD_BRIGHT)
        py5.text("OIDFA / IEC STANDARD NOTATION", cx0 + 124.0, cy0 + 88.0)

    # --- FIG. 06: Historical Bobbin Lace Ledger ---
    mid_y = y + h * 0.5
    tx, ty, tw, th = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(tx, ty, tw, th, 6)

    headers = ["YEAR", "TRADITION / TREATISE", "GROUND TOPOLOGY", "BRAID WORD SIGNATURE"]
    col_xs = [tx + 20, tx + 96, tx + 410, tx + 685]
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(tx + 2, ty + 2, tw - 4, 38, 4)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(13)
    for cx_h, h_str in zip(col_xs, headers):
        py5.text(h_str, cx_h, ty + 21)

    rows = [
        ("1557", "Le Pompe (Sessa Bros., Venice)", "Merletto a Piombini Plaits", "(C * T)^2 Four-Strand Plait"),
        ("1561", "Nüw Modelbuch (R.M., Zurich)", "Geometric Guipure & Picots", "CTC Cloth + T^3 Picot Loop"),
        ("1685", "Binche & Valenciennes (Flanders)", "Fond de Neige (Snow Ground)", "Continuous 8-Pair Star Mesh"),
        ("1720", "Mechlin / Malines (Antwerp)", "Hexagonal Eisgrond + Gimp", "CT*T [Pin] CT*T + Cordonnet"),
        ("1780", "Chantilly & Bayeux (Normandy)", "Point de Paris (Fond Kat)", "6-Pointed Star Wire Ground"),
        ("2014", "Irvine & Ruskey (Victoria)", "2-Regular Torus Digraphs", "Exhaustive {C,T}* Enumeration"),
    ]
    for r_i, r_vals in enumerate(rows):
        ry_row = ty + 52.0 + r_i * 47.0
        if r_i % 2 == 1:
            py5.fill(*CARD_HEADER_BG, 110)
            py5.no_stroke()
            py5.rect(tx + 8, ry_row - 8, tw - 16, 40, 3)
        for c_i, (cx_c, val_str) in enumerate(zip(col_xs, r_vals)):
            py5.fill(*(GOLD_CORDONNET if c_i == 0 else (SILK_CERULEAN if r_i == 5 else INK_IVORY)))
            py5.text_size(12)
            py5.text(val_str, cx_c, ry_row + 12)


def draw_right_bottom_card(phi: float, active_word_idx: int):
    x, y, w, h = RIGHT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 07",
        "PRICKING CARD (PRIKKING) DIAGONAL GRID & CORDONNET ROUTING",
        "FIG. 08",
        "16-PAIR CROSS/TWIST BIT MATRIX & BOBBIN MOMENTUM OSCILLOGRAM",
    )

    # --- FIG. 07: Torchon 52-deg Diagonal Pricking Grid + Heavy Gold Cordonnet Gimp Path ---
    px, py, pw, ph = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(px, py, pw, ph, 6)

    # Diagonal lattice lines inside FIG. 07
    n_cols_p = 13
    n_rows_p = 5
    dx_p = (pw - 120.0) / (n_cols_p - 1)
    dy_p = (ph - 96.0) / (n_rows_p - 1)
    x0_p = px + 60.0
    y0_p = py + 48.0

    diag_segs = []
    pin_pts = []
    for r_p in range(n_rows_p):
        for c_p in range(n_cols_p):
            if (r_p + c_p) % 2 == 0:
                xp = x0_p + c_p * dx_p
                yp = y0_p + r_p * dy_p
                pin_pts.append((xp, yp))
                if r_p + 1 < n_rows_p and c_p + 1 < n_cols_p:
                    diag_segs.append([xp, yp, x0_p + (c_p + 1) * dx_p, y0_p + (r_p + 1) * dy_p])
                if r_p + 1 < n_rows_p and c_p - 1 >= 0:
                    diag_segs.append([xp, yp, x0_p + (c_p - 1) * dx_p, y0_p + (r_p + 1) * dy_p])

    py5.stroke(*SILK_CERULEAN, 155)
    py5.stroke_weight(1.6)
    py5.lines(np.array(diag_segs, dtype=np.float32))

    # Heavy gold Cordonnet gimp outlining diamond motifs across the pricking grid
    u_g = np.linspace(0.0, 1.0, 180, dtype=np.float32)
    xg_arr = x0_p + u_g * (pw - 120.0)
    yg1 = py + ph * 0.5 + 92.0 * np.sin(4.0 * np.pi * u_g - phi)
    yg2 = py + ph * 0.5 - 92.0 * np.sin(4.0 * np.pi * u_g - phi)
    pts_c1 = np.column_stack((xg_arr, yg1))
    pts_c2 = np.column_stack((xg_arr, yg2))
    py5.stroke(*GOLD_BRIGHT, 250)
    py5.stroke_weight(3.6)
    py5.lines(np.hstack((pts_c1[:-1], pts_c1[1:])))
    py5.stroke(*SILK_CRIMSON, 235)
    py5.stroke_weight(2.8)
    py5.lines(np.hstack((pts_c2[:-1], pts_c2[1:])))

    # Brass pin heads at every pricking hole
    py5.fill(*BRASS_PIN)
    py5.stroke(*INK_IVORY)
    py5.stroke_weight(1.2)
    for xp, yp in pin_pts:
        py5.circle(xp, yp, 9.0)

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        "TORCHON PRIKKING GRID (ALPHA = 52.0 DEG)   |   GOLD CORDONNET GIMP ENCLOSING ROSE GROUND CELLS",
        px + 24.0,
        py + ph - 12.0,
    )

    # --- FIG. 08: 16-Pair Cross/Twist State Matrix + Bobbin Momentum Oscillogram ---
    mid_y = y + h * 0.5
    ox, oy, ow, oh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PILLOW_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(ox, oy, ow, oh, 6)

    # Top row: 16 Bobbin Pair Operator Cells (showing active C or T generator)
    cell_w = (ow - 48.0) / 16.0
    step_k = int((phi / (2.0 * np.pi)) * 32)
    for p_i in range(16):
        bx_i = ox + 24.0 + p_i * cell_w
        by_i = oy + 18.0
        is_cross = ((p_i + step_k) % 2 == 0)
        py5.fill(*(SILK_CRIMSON if is_cross else SILK_CERULEAN), 220)
        py5.stroke(*GOLD_BRIGHT if p_i == (step_k % 16) else BORDER_SLATE)
        py5.stroke_weight(1.8 if p_i == (step_k % 16) else 1.2)
        py5.rect(bx_i + 2.0, by_i, cell_w - 4.0, 52.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*INK_IVORY)
        py5.text_size(16)
        py5.text("C" if is_cross else "T", bx_i + cell_w * 0.5, by_i + 20.0)
        py5.fill(*INK_SILVER)
        py5.text_size(10)
        py5.text(f"P{p_i:02d}", bx_i + cell_w * 0.5, by_i + 41.0)

    # Lower half: 3-trace Bobbin Pendulum & Thread Tension Oscillogram
    osc_cy = oy + 204.0
    py5.stroke(*GRID_LINE, 180)
    py5.stroke_weight(1.0)
    py5.line(ox + 24.0, osc_cy, ox + ow - 24.0, osc_cy)

    u_o = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_o = ox + 24.0 + u_o * (ow - 48.0)
    w1 = 68.0 * np.sin(8.0 * np.pi * u_o - 3.0 * phi) * np.cos(2.0 * np.pi * u_o + phi)
    w2 = 54.0 * np.cos(12.0 * np.pi * u_o - 4.0 * phi)
    w3 = 40.0 * np.sin(16.0 * np.pi * u_o + 5.0 * phi)

    for w_arr, w_col in ((w1, GOLD_CORDONNET), (w2, SILK_CERULEAN), (w3, SILK_CRIMSON)):
        pts_o = np.column_stack((x_o, osc_cy - w_arr))
        py5.stroke(*w_col, 235)
        py5.stroke_weight(2.2)
        py5.lines(np.hstack((pts_o[:-1], pts_o[1:])))

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        "BRAID GENERATOR STREAM: {C = sigma_2^-1, T = sigma_1*sigma_3}   |   SPANGLE TENSION T_0 = 0.42 N",
        ox + 26.0,
        oy + oh - 12.0,
    )


def draw():
    frame_idx = py5.frame_count - 1
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phi = 2.0 * np.pi * t_norm

    py5.background(*BG_OBSIDIAN)

    active_word_idx = (int(t_norm * 8) + SEED_OFFSET) % 4

    draw_frame_border_and_header(phi, active_word_idx)
    draw_central_bobbin_lace_medallion(phi)
    draw_left_top_card(phi)
    draw_left_bottom_card(phi)
    draw_right_top_card(phi)
    draw_right_bottom_card(phi, active_word_idx)

    # Save frame 0 as preview PNG
    if frame_idx == 0:
        py5.save_frame(str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_PATH}")

    # Save sequential frame for FFmpeg MP4 assembly
    frame_file = FRAMES_DIR / f"frame_{frame_idx:04d}.png"
    py5.save_frame(str(frame_file))

    if (frame_idx + 1) % 60 == 0 or (frame_idx + 1) == TOTAL_FRAMES:
        elapsed = time.time() - START_TIME
        fps_actual = (frame_idx + 1) / max(elapsed, 1e-6)
        eta = (TOTAL_FRAMES - (frame_idx + 1)) / max(fps_actual, 1e-6)
        print(
            f"[{WORK_NAME}] Frame {frame_idx + 1:03d}/{TOTAL_FRAMES} "
            f"({(frame_idx + 1) / TOTAL_FRAMES * 100:.1f}%) | "
            f"Speed: {fps_actual:.2f} fps | ETA: {eta:.1f}s"
        )

    if frame_idx + 1 >= TOTAL_FRAMES:
        total_elapsed = time.time() - START_TIME
        print(
            f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s "
            f"(~{TOTAL_FRAMES / max(total_elapsed, 1e-6):.2f} fps)."
        )
        compile_video()
        py5.exit_sketch()


def compile_video():
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
        "17",
        "-preset",
        "fast",
        str(VIDEO_PATH),
    ]
    subprocess.run(cmd, check=True)
    size_mb = VIDEO_PATH.stat().st_size / (1024 * 1024)
    print(f"[{WORK_NAME}] Successfully generated output.mp4 ({size_mb:.2f} MB)")
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
    print(f"[{WORK_NAME}] Complete!")


START_TIME = time.time()
if __name__ == "__main__":
    py5.run_sketch()

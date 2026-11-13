# py5 Media Art — Autonomous Animation
# Work: kinetic_muqarnas_stalactite_vault_corbeling_stereotomy_2d
# Genre: Architectural / Brutalism / Geometric (Genre 2)
# Background Polarity: Dark (#060912 Deep Alhambra & Samarkand Architectural Stereotomy Obsidian)

from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import py5

WORK_NAME = "kinetic_muqarnas_stalactite_vault_corbeling_stereotomy_2d"
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC  # 720 frames

OUT_DIR = Path(__file__).parent
FRAMES_DIR = OUT_DIR / "frames"
PREVIEW_PATH = OUT_DIR / f"{WORK_NAME}_p1.png"
VIDEO_PATH = OUT_DIR / "output.mp4"

# Palette — Deep Alhambra & Samarkand Stereotomy Obsidian (#060912)
BG_OBSIDIAN = (6, 9, 18)
CARD_BG = (11, 16, 30)
CARD_HEADER_BG = (17, 25, 45)
VAULT_BG = (8, 12, 24)
DRUM_RIM = (22, 32, 56)

# Polychrome Glazed Tile, Gold Leaf & Stucco Chromatics
NASRID_GOLD = (248, 190, 60)
GOLD_BRIGHT = (255, 228, 128)
SAMARKAND_TURQUOISE = (20, 216, 180)
LAPIS_COBALT = (34, 112, 238)
CINNABAR_RUBY = (238, 66, 92)
STUCCO_ALABASTER = (238, 232, 218)
AMETHYST_GLAZE = (158, 82, 242)

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


def draw_frame_border_and_header(phi: float, sun_az_deg: float):
    py5.no_fill()
    py5.stroke(*BORDER_SLATE, 220)
    py5.stroke_weight(2.0)
    py5.rect(42, 36, W - 84, H - 72, 8)
    py5.stroke(*NASRID_GOLD, 135)
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
        "MUQARNAS STALACTITE VAULT CORBELING & STAR-DOME STEREOTOMY // ALHAMBRA & SAMARKAND",
        114,
        72,
    )

    py5.text_font(FONT_MONO)
    py5.fill(*INK_SILVER)
    py5.text_size(16)
    py5.text(
        f"SYMMETRY: D_16 OCTAGONAL-STAR CUPOLA (7 CORBELED TIERS)   |   CELLS: 896 PRISMATIC NICHES   "
        f"|   CLERESTORY SOLAR AZIMUTH: {sun_az_deg:05.1f} deg   |   MODULE m = R_0 / 16",
        114,
        114,
    )

    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*SAMARKAND_TURQUOISE)
    py5.text_size(17)
    py5.text("AL-KASHI (MIFTAH AL-HISAB, 1427) // SALA DE LAS DOS HERMANAS (1362)", W - 114, 76)
    py5.fill(*CINNABAR_RUBY)
    py5.text_size(15)
    py5.text(
        f"TOPKAPI SCROLL (TUMAR) PROJECTION   |   DIHEDRAL ANGLES: 45, 67.5, 90, 135 deg   |   PHASE = {phi / (2.0 * np.pi) * 100.0:05.1f}%",
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
    py5.fill(*NASRID_GOLD)
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

    py5.fill(*NASRID_GOLD)
    py5.text(code2, x + 18, mid_y + 21)
    py5.fill(*INK_IVORY)
    py5.text(title2, x + 112, mid_y + 21)


def draw_central_muqarnas_cupola_medallion(phi: float):
    # Outer carved drum bezel
    py5.fill(*DRUM_RIM)
    py5.stroke(*BORDER_SLATE, 240)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    # 64 epigraphic drum piers around outer ring
    n_piers = 64
    p_ang = np.linspace(0.0, 2.0 * np.pi, n_piers, endpoint=False)
    p_segs = np.zeros((n_piers, 4), dtype=np.float32)
    p_segs[:, 0] = CX + (INNER_R + 5.0) * np.cos(p_ang)
    p_segs[:, 1] = CY + (INNER_R + 5.0) * np.sin(p_ang)
    p_segs[:, 2] = CX + (MEDALLION_R - 8.0) * np.cos(p_ang)
    p_segs[:, 3] = CY + (MEDALLION_R - 8.0) * np.sin(p_ang)
    py5.stroke(*NASRID_GOLD, 185)
    py5.stroke_weight(2.0)
    py5.lines(p_segs)

    # Recessed nocturnal cupola void
    py5.fill(*VAULT_BG)
    py5.stroke(*NASRID_GOLD, 225)
    py5.stroke_weight(2.4)
    py5.circle(CX, CY, INNER_R * 2.0)

    # Outer 8-pointed Rub el Hizb Octagonal Drum Frame (2 overlapping squares inscribed at R = 648 px)
    r_oct = 646.0
    for rot_sq in (0.0, np.pi / 4.0):
        sq_ang = rot_sq + np.array([0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi, 2.0 * np.pi], dtype=np.float32)
        sq_pts = np.column_stack((CX + r_oct * np.cos(sq_ang), CY + r_oct * np.sin(sq_ang)))
        py5.stroke(*NASRID_GOLD, 160)
        py5.stroke_weight(1.8)
        py5.lines(np.hstack((sq_pts[:-1], sq_pts[1:])))

    # Orbiting celestial light vector for 3D Lambertian + Specular facet relief shading
    lx = np.cos(phi)
    ly = np.sin(phi)

    # Render 8 Concentric Corbeled Muqarnas Stalactite Tiers (from outer Tier 0 at R=625 down to inner Tier 7 at R=68)
    # Each tier is a 32-fold star-polygon ring composed of alternating left-leaning and right-leaning 3D niche facets
    # (Lawza rhombs, Badam almond vaults, and Tasa triangular pendentives)
    n_sym = 32
    d_theta = 2.0 * np.pi / n_sym
    angles_even = np.arange(n_sym, dtype=np.float32) * d_theta
    angles_odd = angles_even + 0.5 * d_theta

    tier_radii = [626.0, 542.0, 460.0, 382.0, 308.0, 236.0, 168.0, 106.0, 54.0]
    tier_base_palettes = [
        LAPIS_COBALT,
        SAMARKAND_TURQUOISE,
        CINNABAR_RUBY,
        NASRID_GOLD,
        LAPIS_COBALT,
        SAMARKAND_TURQUOISE,
        CINNABAR_RUBY,
        STUCCO_ALABASTER,
    ]

    groin_ribs_gold = []
    groin_ribs_ivory = []

    for t_idx in range(len(tier_radii) - 1):
        r_out_base = tier_radii[t_idx]
        r_in_base = tier_radii[t_idx + 1]
        r_mid_base = 0.52 * r_out_base + 0.48 * r_in_base

        # Subtle harmonic corbel breathing per tier
        breath = 1.0 + 0.018 * np.sin(2.0 * phi - t_idx * 0.65)
        r_out = r_out_base * breath
        r_in = r_in_base * breath
        # Star-indentation modulation: alternate tiers shift by half-step (0.5 * d_theta) for authentic interlocking corbels!
        phase_shift = 0.0 if (t_idx % 2 == 0) else 0.5 * d_theta

        a_0 = angles_even + phase_shift
        a_half = angles_odd + phase_shift
        a_1 = np.roll(a_0, -1)

        # Star-tipped outer, middle (Muqarnas niche ridge), and inner vertices
        r_ridge = r_mid_base * breath * (1.06 if (t_idx % 2 == 0) else 0.94)

        p_out_x = CX + r_out * np.cos(a_0)
        p_out_y = CY + r_out * np.sin(a_0)
        p_ridge_x = CX + r_ridge * np.cos(a_half)
        p_ridge_y = CY + r_ridge * np.sin(a_half)
        p_in_x = CX + r_in * np.cos(a_0)
        p_in_y = CY + r_in * np.sin(a_0)
        p_in_next_x = np.roll(p_in_x, -1)
        p_in_next_y = np.roll(p_in_y, -1)
        p_out_next_x = np.roll(p_out_x, -1)
        p_out_next_y = np.roll(p_out_y, -1)

        base_rgb = np.array(tier_base_palettes[t_idx], dtype=np.float32)
        stucco_rgb = np.array(STUCCO_ALABASTER, dtype=np.float32)
        gold_rgb = np.array(NASRID_GOLD, dtype=np.float32)

        # Group the 32 * 2 = 64 left/right Muqarnas vault facets + 32 outer spandrel triangles into 8 luminance bins
        n_bins = 8
        bin_quads = [[] for _ in range(n_bins)]
        bin_cols = []
        for b_k in range(n_bins):
            lit = 0.28 + 0.88 * (b_k / float(n_bins - 1))
            col_b = np.clip(base_rgb * lit + gold_rgb * (0.22 * (lit**2)), 0, 255).astype(np.int32)
            bin_cols.append(tuple(col_b))

        for k in range(n_sym):
            # Left vault facet of cell k: quad (p_out[k], p_ridge[k], p_in_next[k], p_in[k])
            # Right spandrel/rhomb facet of cell k: quad (p_out[k], p_out_next[k], p_ridge[k], p_in[k])
            ang_k = a_half[k]
            # Facet 1 normal tilted +38 deg azimuthally
            n1_x, n1_y = np.cos(ang_k - 0.55), np.sin(ang_k - 0.55)
            dot1 = 0.5 + 0.5 * (n1_x * lx + n1_y * ly)
            b_idx1 = int(np.clip(dot1 * n_bins, 0, n_bins - 1))

            q1 = [
                [p_out_x[k], p_out_y[k]],
                [p_ridge_x[k], p_ridge_y[k]],
                [p_in_next_x[k], p_in_next_y[k]],
                [p_in_x[k], p_in_y[k]],
            ]
            bin_quads[b_idx1].append(q1)

            # Facet 2 normal tilted -38 deg azimuthally
            n2_x, n2_y = np.cos(ang_k + 0.55), np.sin(ang_k + 0.55)
            dot2 = 0.5 + 0.5 * (n2_x * lx + n2_y * ly)
            b_idx2 = int(np.clip(dot2 * n_bins, 0, n_bins - 1))

            q2 = [
                [p_out_x[k], p_out_y[k]],
                [p_out_next_x[k], p_out_next_y[k]],
                [p_ridge_x[k], p_ridge_y[k]],
                [p_in_x[k], p_in_y[k]],
            ]
            bin_quads[b_idx2].append(q2)

            # Collect stereotomic groin ribs (Muqarnas facet edges)
            groin_ribs_gold.append([p_out_x[k], p_out_y[k], p_ridge_x[k], p_ridge_y[k]])
            groin_ribs_gold.append([p_out_next_x[k], p_out_next_y[k], p_ridge_x[k], p_ridge_y[k]])
            groin_ribs_ivory.append([p_in_x[k], p_in_y[k], p_ridge_x[k], p_ridge_y[k]])
            groin_ribs_ivory.append([p_in_next_x[k], p_in_next_y[k], p_ridge_x[k], p_ridge_y[k]])
            groin_ribs_gold.append([p_out_x[k], p_out_y[k], p_in_x[k], p_in_y[k]])

        py5.no_stroke()
        for b_k in range(n_bins):
            if bin_quads[b_k]:
                py5.fill(*bin_cols[b_k], 242)
                with py5.begin_shape(py5.QUADS):
                    py5.vertices(np.array(bin_quads[b_k], dtype=np.float32).reshape(-1, 2))

    # Draw all stereotomic groin ribs in two fast batched py5.lines calls
    py5.stroke(*STUCCO_ALABASTER, 195)
    py5.stroke_weight(1.4)
    py5.lines(np.array(groin_ribs_ivory, dtype=np.float32))

    py5.stroke(*GOLD_BRIGHT, 225)
    py5.stroke_weight(1.8)
    py5.lines(np.array(groin_ribs_gold, dtype=np.float32))

    # Central 16-Pointed Shamsa Zenith Star Lantern at (CX, CY, r = 0..56 px)
    py5.fill(*VAULT_BG)
    py5.stroke(*GOLD_BRIGHT, 255)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, 110.0)

    shamsa_segs = []
    n_sh = 16
    for s_i in range(n_sh):
        a1 = s_i * (2.0 * np.pi / n_sh) + 0.25 * phi
        a2 = ((s_i + 5) % n_sh) * (2.0 * np.pi / n_sh) + 0.25 * phi
        shamsa_segs.append(
            [CX + 52.0 * np.cos(a1), CY + 52.0 * np.sin(a1), CX + 52.0 * np.cos(a2), CY + 52.0 * np.sin(a2)]
        )
    py5.stroke(*GOLD_BRIGHT, 250)
    py5.stroke_weight(2.0)
    py5.lines(np.array(shamsa_segs, dtype=np.float32))
    py5.fill(*SAMARKAND_TURQUOISE)
    py5.circle(CX, CY, 22.0)

    # Bottom viewport telemetry pill inside medallion
    badge_w = 560.0
    badge_y = CY + INNER_R - 132.0
    py5.fill(*CARD_HEADER_BG, 240)
    py5.stroke(*NASRID_GOLD, 215)
    py5.stroke_weight(1.5)
    py5.rect(CX - badge_w * 0.5, badge_y, badge_w, 44.0, 6)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        "SALA DE LAS DOS HERMANAS CUPOLA  |  8 CORBELED TIERS  |  SHAMSA ZENITH",
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
        "AL-KASHI (1427) MODULAR MUQARNAS NICHE CELL & CURVED ROOF",
        "FIG. 02",
        "TOPKAPI SCROLL (TUMAR) 2D PLAN -> 3D CORBELED TIER CANTILEVER",
    )

    # --- FIG. 01: Axonometric Elevation of a Single Al-Kashi Muqarnas Niche Unit ---
    bx, by, bw, bh = x + 36.0, y + 64.0, 520.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(bx, by, bw, bh, 6)

    mcx = bx + bw * 0.5
    mcy = by + bh * 0.54

    # Left & Right Vertical Facet Walls (Saq, height = 2*m, width = m)
    py5.fill(*LAPIS_COBALT, 210)
    py5.stroke(*GOLD_BRIGHT, 235)
    py5.stroke_weight(2.2)
    with py5.begin_shape(py5.QUADS):
        py5.vertex(mcx - 130.0, mcy - 26.0)
        py5.vertex(mcx, mcy - 78.0)
        py5.vertex(mcx, mcy + 68.0)
        py5.vertex(mcx - 130.0, mcy + 104.0)

    py5.fill(*SAMARKAND_TURQUOISE, 210)
    with py5.begin_shape(py5.QUADS):
        py5.vertex(mcx, mcy - 78.0)
        py5.vertex(mcx + 130.0, mcy - 26.0)
        py5.vertex(mcx + 130.0, mcy + 104.0)
        py5.vertex(mcx, mcy + 68.0)

    # Overhanging Curved Vault Roof (Saqf / Badam Almond Hood) at top of niche
    py5.fill(*CINNABAR_RUBY, 230)
    with py5.begin_shape(py5.TRIANGLES):
        py5.vertex(mcx - 130.0, mcy - 26.0)
        py5.vertex(mcx, mcy - 78.0)
        py5.vertex(mcx, mcy - 138.0)

        py5.vertex(mcx + 130.0, mcy - 26.0)
        py5.vertex(mcx, mcy - 78.0)
        py5.vertex(mcx, mcy - 138.0)

    # Al-Kashi curved profile arc inside the roof
    u_arc = np.linspace(0.0, 1.0, 40, dtype=np.float32)
    ax_pts = mcx - 130.0 * (1.0 - u_arc)
    ay_pts = (mcy - 26.0) * (1.0 - u_arc) + (mcy - 138.0) * u_arc - 24.0 * np.sin(np.pi * u_arc)
    pts_a = np.column_stack((ax_pts, ay_pts))
    py5.stroke(*GOLD_BRIGHT, 255)
    py5.stroke_weight(3.0)
    py5.lines(np.hstack((pts_a[:-1], pts_a[1:])))

    py5.text_font(FONT_MONO)
    py5.text_size(11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text("SAQF (CURVED VAULT ROOF)", bx + 20.0, by + 18.0)
    py5.fill(*SAMARKAND_TURQUOISE)
    py5.text("SAQ (VERTICAL WALL FACETS)", bx + 20.0, by + bh - 34.0)

    # Right column specs for FIG. 01
    rx = bx + bw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(15)
    py5.text("AL-KASHI MODULE RATIOS", rx, by + 6.0)
    specs_f1 = [
        ("TREATISE", "Miftah al-Hisab (1427)"),
        ("BASE MODULE", "m = Max Facet Width"),
        ("CELL HEIGHT", "h = 2 * m (Standard Tier)"),
        ("ROOF ARC", "r_1 = (1/2) m, r_2 = m"),
        ("SURFACE AREA", "A_roof = 1.685 * m^2"),
        ("BIPED ANGLE", "beta = 45, 67.5, 90 deg"),
        ("ALMOND RATIO", "cos(45 deg) = 0.7071 * m"),
        ("COMPLEMENT", "1 - cos(45 deg) = 0.2929 m"),
        ("JOINERY", "Mortared Stucco / Brick"),
    ]
    for i, (k_s, v_s) in enumerate(specs_f1):
        yy = by + 42.0 + i * 32.0
        py5.fill(*INK_MUTED)
        py5.text_size(13)
        py5.text(k_s, rx, yy)
        py5.fill(*(SAMARKAND_TURQUOISE if i in (1, 3, 4) else INK_IVORY))
        py5.text(v_s, rx + 156.0, yy)

    # --- FIG. 02: 7-Tier Corbel Overhang Cross-Section (2D Plan -> 3D Elevation) ---
    mid_y = y + h * 0.5
    cx0, cy0, cw, ch = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(cx0, cy0, cw, ch, 6)

    # Draw symmetrical stepped corbel arch profile (left & right walls stepping inward toward central cupola)
    n_steps = 7
    step_h = 27.0
    base_y = cy0 + ch - 34.0
    mid_x = cx0 + cw * 0.5

    for s_i in range(n_steps):
        y_bot = base_y - s_i * step_h
        y_top = y_bot - step_h
        span_half = 390.0 - s_i * 52.0
        col_s = [LAPIS_COBALT, SAMARKAND_TURQUOISE, CINNABAR_RUBY, NASRID_GOLD][s_i % 4]

        # Left & right corbeled blocks
        py5.fill(*col_s, 215)
        py5.stroke(*GOLD_BRIGHT, 230)
        py5.stroke_weight(1.8)
        py5.rect(mid_x - span_half - 56.0, y_top, 56.0, step_h, 3)
        py5.rect(mid_x + span_half, y_top, 56.0, step_h, 3)

        # Vertical dashed projection lines down to 2D Tumar plan bar at bottom
        py5.stroke(*INK_MUTED, 130)
        py5.stroke_weight(1.0)
        py5.line(mid_x - span_half, y_bot, mid_x - span_half, base_y + 16.0)
        py5.line(mid_x + span_half, y_bot, mid_x + span_half, base_y + 16.0)

    # Central Shamsa cupola cap at top of corbel arch
    py5.fill(*NASRID_GOLD, 235)
    py5.stroke(*GOLD_BRIGHT, 250)
    py5.stroke_weight(2.2)
    py5.rect(mid_x - 42.0, base_y - n_steps * step_h - 24.0, 84.0, 24.0, 4)

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text("CANTILEVERED CORBEL SECTION (TABAQAT T1..T7): ZERO-CENTERING COMPRESSIVE OVERHANG", cx0 + 22.0, cy0 + 18.0)
    py5.fill(*SAMARKAND_TURQUOISE)
    py5.text("VERTICAL LINES PROJECT 3D TIER EDGES ONTO 2D TOPKAPI TUMAR SCROLL BLUEPRINT", cx0 + 22.0, cy0 + 40.0)


def draw_left_bottom_card(phi: float):
    x, y, w, h = LEFT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 03",
        "AL-KASHI'S FOUR MUQARNAS TAXONOMIC CLASSES (SAMARKAND, 1427)",
        "FIG. 04",
        "ALHAMBRA & SAMARKAND POLYCHROME STEREOTOMY PALETTE",
    )

    # --- FIG. 03: 4 Classical Muqarnas Types (Sadhaj, Mutayyan, Muqassar, Shirazi) ---
    tx, ty, tw, th = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(tx, ty, tw, th, 6)

    classes = [
        ("1. SADHAJ (SIMPLE PLAIN)", LAPIS_COBALT, "Rectilinear prisms & flat 45/90 deg roofs"),
        ("2. MUTAYYAN (CLAY-PLASTERED)", SAMARKAND_TURQUOISE, "Uniform tier height with curved Badam hoods"),
        ("3. MUQASSAR (CURVED ARCHED)", CINNABAR_RUBY, "Tiered ribs without intermediate vertical legs"),
        ("4. SHIRAZI (POLYCHROME STAR)", NASRID_GOLD, "Variable angles + suspended stalactite drops"),
    ]
    cw_box = (tw - 42.0) * 0.5
    ch_box = (th - 42.0) * 0.5
    for idx_c, (c_title, c_col, c_desc) in enumerate(classes):
        ci = idx_c % 2
        ri = idx_c // 2
        bx_c = tx + 14.0 + ci * (cw_box + 14.0)
        by_c = ty + 14.0 + ri * (ch_box + 14.0)
        py5.fill(*CARD_HEADER_BG, 185)
        py5.stroke(*c_col, 215)
        py5.stroke_weight(1.5)
        py5.rect(bx_c, by_c, cw_box, ch_box, 5)

        # Geometric star/rhomb glyph on left
        gx_c = bx_c + 60.0
        gy_c = by_c + ch_box * 0.54
        py5.fill(*c_col, 210)
        py5.stroke(*GOLD_BRIGHT)
        py5.stroke_weight(1.8)
        with py5.begin_shape(py5.QUADS):
            py5.vertex(gx_c, gy_c - 34.0)
            py5.vertex(gx_c + 34.0, gy_c)
            py5.vertex(gx_c, gy_c + 34.0)
            py5.vertex(gx_c - 34.0, gy_c)
        py5.fill(*VAULT_BG)
        py5.circle(gx_c, gy_c, 16.0)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*c_col)
        py5.text_size(13)
        py5.text(c_title, bx_c + 114.0, by_c + 24.0)
        py5.fill(*INK_IVORY)
        py5.text_size(11)
        py5.text(c_desc, bx_c + 114.0, by_c + 56.0)
        py5.fill(*GOLD_BRIGHT)
        py5.text("BOOK IV, CH. 9 (SAMARKAND CANON)", bx_c + 114.0, by_c + 88.0)

    # --- FIG. 04: 6 Chromatic Swatches ---
    mid_y = y + h * 0.5
    swatches = [
        (NASRID_GOLD, "NASRID GOLD LEAF", "#F8BE3C // SHAMSA & RIBS"),
        (SAMARKAND_TURQUOISE, "SAMARKAND TURQUOISE", "#14D8B4 // GLAZED KASHI"),
        (LAPIS_COBALT, "BADAKHSHAN LAPIS", "#2270EE // COBALT NICHE"),
        (CINNABAR_RUBY, "ALHAMBRA CINNABAR", "#EE425C // VERMILION HOOD"),
        (STUCCO_ALABASTER, "YESERIA CARVED STUCCO", "#EEE8DA // GYPSUM PRISM"),
        (AMETHYST_GLAZE, "TIMURID MANGANESE", "#9E52F2 // STAR SPANDREL"),
    ]
    sw_w = (w - 96.0) / 3.0
    sw_h = 152.0
    for i, (scol, sname, sdesc) in enumerate(swatches):
        col_i = i % 3
        row_i = i // 3
        bx_s = x + 36.0 + col_i * (sw_w + 12.0)
        by_s = mid_y + 62.0 + row_i * (sw_h + 18.0)
        py5.fill(*VAULT_BG)
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
        "CANONICAL 2D PROTOTILE SET (LAWZA, BADAM, BIPED & SHAMSA)",
        "FIG. 06",
        "MUQARNAS & STALACTITE VAULT STEREOTOMY LEDGER (1085-2004)",
    )

    # --- FIG. 05: 5 Canonical Euclidean Prototiles that Tile the Tumar Plan ---
    px, py, pw, ph = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(px, py, pw, ph, 6)

    tiles = [
        ("LAWZA (45 deg)", "Rhomb", LAPIS_COBALT),
        ("BADAM (67.5 deg)", "Almond", SAMARKAND_TURQUOISE),
        ("MURABBA (90 deg)", "Square", NASRID_GOLD),
        ("TASA (45-90-45)", "Triangle", CINNABAR_RUBY),
        ("SHAMSA (D_8)", "Star", AMETHYST_GLAZE),
    ]
    tw_cell = (pw - 40.0) / 5.0
    for idx_t, (t_name, t_sub, t_col) in enumerate(tiles):
        cx_t = px + 20.0 + (idx_t + 0.5) * tw_cell
        cy_t = py + 155.0

        py5.fill(*t_col, 210)
        py5.stroke(*GOLD_BRIGHT, 240)
        py5.stroke_weight(2.2)
        if idx_t == 0:
            # 45-deg Rhomb
            with py5.begin_shape(py5.QUADS):
                py5.vertex(cx_t, cy_t - 62.0)
                py5.vertex(cx_t + 32.0, cy_t)
                py5.vertex(cx_t, cy_t + 62.0)
                py5.vertex(cx_t - 32.0, cy_t)
        elif idx_t == 1:
            # 67.5-deg Almond deltoid
            with py5.begin_shape(py5.QUADS):
                py5.vertex(cx_t, cy_t - 64.0)
                py5.vertex(cx_t + 44.0, cy_t + 8.0)
                py5.vertex(cx_t, cy_t + 54.0)
                py5.vertex(cx_t - 44.0, cy_t + 8.0)
        elif idx_t == 2:
            py5.rect(cx_t - 44.0, cy_t - 44.0, 88.0, 88.0, 4)
        elif idx_t == 3:
            with py5.begin_shape(py5.TRIANGLES):
                py5.vertex(cx_t, cy_t - 54.0)
                py5.vertex(cx_t + 54.0, cy_t + 46.0)
                py5.vertex(cx_t - 54.0, cy_t + 46.0)
        else:
            py5.circle(cx_t, cy_t, 92.0)
            py5.fill(*VAULT_BG)
            py5.circle(cx_t, cy_t, 42.0)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.fill(*GOLD_BRIGHT)
        py5.text_size(12)
        py5.text(t_name, cx_t, py + 248.0)
        py5.fill(*INK_SILVER)
        py5.text_size(11)
        py5.text(t_sub, cx_t, py + 272.0)

    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*INK_IVORY)
    py5.text_size(12)
    py5.text("MODULAR EUCLIDEAN PROTOTILES (SIDE LENGTH = m OR m / sqrt(2))", px + 24.0, py + 20.0)

    # --- FIG. 06: Historical Muqarnas Stereotomy Ledger ---
    mid_y = y + h * 0.5
    lx, ly, lw, lh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(lx, ly, lw, lh, 6)

    headers = ["YEAR", "MONUMENT / AUTHOR", "SYMMETRY & TIERS", "ARCHITECTURAL INNOVATION"]
    col_xs = [lx + 20, lx + 96, lx + 410, lx + 675]
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(lx + 2, ly + 2, lw - 4, 38, 4)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(13)
    for cx_h, h_str in zip(col_xs, headers):
        py5.text(h_str, cx_h, ly + 21)

    rows = [
        ("1085", "Imam Dur Mausoleum (Samarra)", "Octagonal 5-Tier Brick Dome", "Earliest Surviving Muqarnas Cupola"),
        ("1274", "Natanz Shrine (Ilkhanid Iran)", "12-Pointed Star Shell Vault", "Glazed Turquoise & Lapis Ribs"),
        ("1362", "Sala de las Dos Hermanas", "Octagonal 5,000-Prism Vault", "7 Nasrid Stucco Modular Prisms"),
        ("1427", "Al-Kashi (Miftah al-Hisab)", "4 Taxonomic Classes (m)", "Exact Curved Roof Surface Integrals"),
        ("1500", "Topkapi Scroll (Timurid Iran)", "114 Radial Plan Drawings", "2D Tumar Blueprint Projection"),
        ("1992", "Y. Dold-Samplonius (Heidelberg)", "Algorithmic CAD Reconstruction", "Parametric Al-Kashi Roof Solver"),
    ]
    for r_i, r_vals in enumerate(rows):
        ry_row = ly + 52.0 + r_i * 47.0
        if r_i % 2 == 1:
            py5.fill(*CARD_HEADER_BG, 110)
            py5.no_stroke()
            py5.rect(lx + 8, ry_row - 8, lw - 16, 40, 3)
        for c_i, (cx_c, val_str) in enumerate(zip(col_xs, r_vals)):
            py5.fill(*(NASRID_GOLD if c_i == 0 else (SAMARKAND_TURQUOISE if r_i in (2, 3) else INK_IVORY)))
            py5.text_size(12)
            py5.text(val_str, cx_c, ry_row + 12)


def draw_right_bottom_card(phi: float):
    x, y, w, h = RIGHT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 07",
        "SQUINCH TRANSITION: SQUARE (D_4) -> OCTAGON (D_8) -> CUPOLA (D_16)",
        "FIG. 08",
        "8-TIER LAMBERTIAN ILLUMINATION & FACET SHADOW OSCILLOGRAM",
    )

    # --- FIG. 07: Concentric Symmetry Doubling Diagram (D4 -> D8 -> D16 -> S1) ---
    sx, sy, sw, sh = x + 36.0, y + 64.0, 480.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(sx, sy, sw, sh, 6)

    scx, scy = sx + sw * 0.5, sy + sh * 0.5
    # 1) Outer Square Base (D_4, side = 260)
    py5.no_fill()
    py5.stroke(*CINNABAR_RUBY, 235)
    py5.stroke_weight(2.6)
    py5.rect(scx - 130.0, scy - 130.0, 260.0, 260.0)

    # 2) Octagonal Squinch Drum (D_8, R = 130)
    a8 = np.linspace(0.0, 2.0 * np.pi, 9, dtype=np.float32) + np.pi / 8.0
    pts8 = np.column_stack((scx + 130.0 * np.cos(a8), scy + 130.0 * np.sin(a8)))
    py5.stroke(*SAMARKAND_TURQUOISE, 240)
    py5.stroke_weight(2.6)
    py5.lines(np.hstack((pts8[:-1], pts8[1:])))

    # 3) 16-Pointed Star Ring (D_16, R = 92)
    a16 = np.linspace(0.0, 2.0 * np.pi, 33, dtype=np.float32)
    r16 = np.where(np.arange(33) % 2 == 0, 96.0, 72.0)
    pts16 = np.column_stack((scx + r16 * np.cos(a16), scy + r16 * np.sin(a16)))
    py5.stroke(*NASRID_GOLD, 250)
    py5.stroke_weight(2.2)
    py5.lines(np.hstack((pts16[:-1], pts16[1:])))

    # 4) Inner Cupola Circle (S^1, R = 42)
    py5.stroke(*GOLD_BRIGHT, 255)
    py5.circle(scx, scy, 84.0)

    # Right side explanatory column for FIG. 07
    rx7 = sx + sw + 26.0
    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(15)
    py5.text("DIHEDRAL SYMMETRY CASCADE", rx7, sy + 8.0)
    steps_s = [
        (CINNABAR_RUBY, "TIER 0: SQUARE HALL (D_4)", "4 Corner Trompe Squinches"),
        (SAMARKAND_TURQUOISE, "TIER 1-2: OCTAGON DRUM (D_8)", "16 Clerestory Windows"),
        (NASRID_GOLD, "TIER 3-6: STAR VAULT (D_16)", "512 Corbeled Lawza/Badam"),
        (GOLD_BRIGHT, "TIER 7: SHAMSA DOME (D_32)", "Spherical Zenith Cupola"),
    ]
    for i, (scol, stitle, sdesc) in enumerate(steps_s):
        yy = sy + 48.0 + i * 74.0
        py5.fill(*scol)
        py5.no_stroke()
        py5.rect(rx7, yy + 3.0, 16.0, 16.0, 3)
        py5.fill(*INK_IVORY)
        py5.text_size(13)
        py5.text(stitle, rx7 + 26.0, yy)
        py5.fill(*INK_SILVER)
        py5.text_size(12)
        py5.text(sdesc, rx7 + 26.0, yy + 22.0)

    # --- FIG. 08: 8-Tier Luminance Matrix + Clerestory Light Oscillogram ---
    mid_y = y + h * 0.5
    ox, oy, ow, oh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*VAULT_BG)
    py5.stroke(*BORDER_SLATE, 195)
    py5.stroke_weight(1.4)
    py5.rect(ox, oy, ow, oh, 6)

    cell_w = (ow - 48.0) / 8.0
    t_cols = [
        LAPIS_COBALT,
        SAMARKAND_TURQUOISE,
        CINNABAR_RUBY,
        NASRID_GOLD,
        LAPIS_COBALT,
        SAMARKAND_TURQUOISE,
        CINNABAR_RUBY,
        STUCCO_ALABASTER,
    ]
    for t_i in range(8):
        bx_i = ox + 24.0 + t_i * cell_w
        by_i = oy + 18.0
        lum_val = 0.55 + 0.45 * np.cos(phi - t_i * 0.45)
        py5.fill(*t_cols[t_i], int(130 + 115 * lum_val))
        py5.stroke(*GOLD_BRIGHT)
        py5.stroke_weight(1.4)
        py5.rect(bx_i + 4.0, by_i, cell_w - 8.0, 52.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*BG_OBSIDIAN if t_i in (1, 3, 5, 7) else INK_IVORY)
        py5.text_size(14)
        py5.text(f"TIER {t_i + 1}", bx_i + cell_w * 0.5, by_i + 18.0)
        py5.text_size(11)
        py5.text(f"L={int(lum_val * 100):02d}%", bx_i + cell_w * 0.5, by_i + 38.0)

    # Lower half: 3-trace Dihedral Facet Reflectance Oscillogram
    osc_cy = oy + 204.0
    py5.stroke(*GRID_LINE, 180)
    py5.stroke_weight(1.0)
    py5.line(ox + 24.0, osc_cy, ox + ow - 24.0, osc_cy)

    u_o = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_o = ox + 24.0 + u_o * (ow - 48.0)
    w1 = 68.0 * np.sin(8.0 * np.pi * u_o - 2.0 * phi) * np.cos(2.0 * np.pi * u_o + phi)
    w2 = 54.0 * np.cos(12.0 * np.pi * u_o - 3.0 * phi)
    w3 = 42.0 * np.sin(16.0 * np.pi * u_o + 4.0 * phi)

    for w_arr, w_col in ((w1, NASRID_GOLD), (w2, SAMARKAND_TURQUOISE), (w3, CINNABAR_RUBY)):
        pts_o = np.column_stack((x_o, osc_cy - w_arr))
        py5.stroke(*w_col, 235)
        py5.stroke_weight(2.2)
        py5.lines(np.hstack((pts_o[:-1], pts_o[1:])))

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        "CLERESTORY SOLAR ORBIT: N_facet . L(phi) LAMBERTIAN RELIEF ACROSS 896 CORBELED PRISMS",
        ox + 26.0,
        oy + oh - 12.0,
    )


def draw():
    frame_idx = py5.frame_count - 1
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phi = 2.0 * np.pi * t_norm + (SEED_OFFSET % 100) * 0.01

    py5.background(*BG_OBSIDIAN)

    sun_az_deg = (t_norm * 360.0) % 360.0

    draw_frame_border_and_header(phi, sun_az_deg)
    draw_central_muqarnas_cupola_medallion(phi)
    draw_left_top_card(phi)
    draw_left_bottom_card(phi)
    draw_right_top_card(phi)
    draw_right_bottom_card(phi)

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

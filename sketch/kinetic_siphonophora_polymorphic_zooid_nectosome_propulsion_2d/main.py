# py5 Media Art — Autonomous Animation
# Work: kinetic_siphonophora_polymorphic_zooid_nectosome_propulsion_2d
# Genre: Organic / Morphogenesis (Genre 1)
# Background Polarity: Light (#f6f2e8 Warm H.M.S. Challenger & Naples Zoological Vellum)

from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import py5

WORK_NAME = "kinetic_siphonophora_polymorphic_zooid_nectosome_propulsion_2d"
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC  # 720 frames

OUT_DIR = Path(__file__).parent
FRAMES_DIR = OUT_DIR / "frames"
PREVIEW_PATH = OUT_DIR / f"{WORK_NAME}_p1.png"
VIDEO_PATH = OUT_DIR / "output.mp4"

# Palette — Warm H.M.S. Challenger & Naples Zoological Vellum (#f6f2e8)
BG_VELLUM = (246, 242, 232)
CARD_BG = (252, 249, 242)
CARD_HEADER_BG = (236, 229, 214)
ABYSS_BG = (10, 18, 34)
PANEL_MIST = (240, 234, 220)

# Ink & Framing
INK_CHARCOAL = (24, 30, 44)
INK_SLATE = (72, 84, 106)
INK_MUTED = (118, 128, 148)
BORDER_BRONZE = (158, 136, 98)
BRASS_GOLD = (196, 142, 38)
BRASS_BRIGHT = (246, 198, 78)

# Siphonophore Polymorphic Zooid Chromatics
PNEUMA_CRIMSON = (234, 48, 104)
NECTO_CERULEAN = (38, 182, 248)
NECTO_ICE = (156, 228, 255)
COENOSARC_GOLD = (252, 194, 58)
GASTRO_CORAL = (248, 106, 62)
CNIDO_AMETHYST = (168, 78, 244)
JET_VIRIDIAN = (24, 218, 158)

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


def draw_frame_border_and_header(phi: float, thrust_mn: float):
    py5.no_fill()
    py5.stroke(*BORDER_BRONZE, 235)
    py5.stroke_weight(2.2)
    py5.rect(42, 36, W - 84, H - 72, 8)
    py5.stroke(*INK_CHARCOAL, 150)
    py5.stroke_weight(1.0)
    py5.rect(50, 44, W - 100, H - 88, 6)

    py5.fill(*CARD_HEADER_BG, 245)
    py5.stroke(*BORDER_BRONZE, 220)
    py5.stroke_weight(1.6)
    py5.rect(84, 58, W - 168, 94, 6)

    py5.text_font(FONT_SANS)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(27)
    py5.text(
        "SIPHONOPHORA POLYMORPHIC ZOOID MORPHOGENESIS & MULTI-JET NECTOSOME PROPULSION",
        114,
        72,
    )

    py5.text_font(FONT_MONO)
    py5.fill(*INK_SLATE)
    py5.text_size(16)
    py5.text(
        f"TAXON: PHYSONECTAE (NANOMIA / PHYSOPHORA)   |   NECTOSOME: 10 BISERIAL SWIMMING BELLS   "
        f"|   SIPHOSOME: 8 CORMIDIA REPEATS   |   NET THRUST F_z = {thrust_mn:05.2f} mN",
        114,
        114,
    )

    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*PNEUMA_CRIMSON)
    py5.text_size(17)
    py5.text("E. HAECKEL (CHALLENGER EXPEDITION, 1888) // DUNN (2005) // COSTELLO (2015)", W - 114, 76)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(15)
    py5.text(
        f"METACHRONAL JET WAVE kappa = 0.65 rad/bell   |   REYNOLDS Re = 420   |   PHASE = {phi / (2.0 * np.pi) * 100.0:05.1f}%",
        W - 114,
        114,
    )


def draw_flank_card(x: float, y: float, w: float, h: float, code1: str, title1: str, code2: str, title2: str):
    py5.fill(*CARD_BG, 248)
    py5.stroke(*BORDER_BRONZE, 225)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, y + 2, w - 4, 42, 6)
    py5.stroke(*BORDER_BRONZE, 190)
    py5.stroke_weight(1.2)
    py5.line(x, y + 44, x + w, y + 44)

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*PNEUMA_CRIMSON)
    py5.text_size(16)
    py5.text(code1, x + 18, y + 23)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(16)
    py5.text(title1, x + 112, y + 23)

    mid_y = y + h * 0.5
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, mid_y, w - 4, 42)
    py5.stroke(*BORDER_BRONZE, 190)
    py5.stroke_weight(1.2)
    py5.line(x, mid_y, x + w, mid_y)
    py5.line(x, mid_y + 42, x + w, mid_y + 42)

    py5.fill(*PNEUMA_CRIMSON)
    py5.text(code2, x + 18, mid_y + 21)
    py5.fill(*INK_CHARCOAL)
    py5.text(title2, x + 112, mid_y + 21)


def draw_central_siphonophore_medallion(phi: float):
    # Outer brass Challenger bathythermograph bezel
    py5.fill(*CARD_HEADER_BG)
    py5.stroke(*INK_CHARCOAL, 230)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    n_ticks = 72
    t_ang = np.linspace(0.0, 2.0 * np.pi, n_ticks, endpoint=False)
    r_t1 = INNER_R + 5.0
    r_t2 = MEDALLION_R - 10.0
    t_segs = np.zeros((n_ticks, 4), dtype=np.float32)
    t_segs[:, 0] = CX + r_t1 * np.cos(t_ang)
    t_segs[:, 1] = CY + r_t1 * np.sin(t_ang)
    t_segs[:, 2] = CX + r_t2 * np.cos(t_ang)
    t_segs[:, 3] = CY + r_t2 * np.sin(t_ang)
    py5.stroke(*INK_CHARCOAL, 165)
    py5.stroke_weight(1.8)
    py5.lines(t_segs)

    # Recessed abyssal bathypelagic basin
    py5.fill(*ABYSS_BG)
    py5.stroke(*BRASS_GOLD, 215)
    py5.stroke_weight(2.2)
    py5.circle(CX, CY, INNER_R * 2.0)

    # Bathymetric depth rings & meridian crosshairs
    py5.no_fill()
    py5.stroke(24, 42, 74, 155)
    py5.stroke_weight(1.0)
    for r_g in (180.0, 360.0, 540.0):
        py5.circle(CX, CY, r_g * 2.0)
    py5.line(CX - INNER_R + 16, CY, CX + INNER_R - 16, CY)

    # 1. Compute Sinuous Central Coenosarc Stem Spine from Apex (CY - 540) to Base (CY + 410)
    n_spine = 120
    u_sp = np.linspace(0.0, 1.0, n_spine, dtype=np.float32)
    y_sp = (CY - 535.0) + u_sp * 920.0
    # Undulation increases from apical float down into the flexible siphosome
    x_sp = CX + (12.0 + 36.0 * u_sp) * np.sin(2.5 * np.pi * u_sp - phi)

    # 2. Render 10 Biserial Nectophores (Swimming Bells) along upper Nectosome (u in [0.07..0.48])
    n_bells = 10
    bell_quads_outer = []
    bell_quads_sub = []
    canal_segs = []
    jet_segs = []

    for b_k in range(n_bells):
        u_b = 0.08 + (b_k / float(n_bells - 1)) * 0.39
        idx_sp = int(u_b * (n_spine - 1))
        sx, sy = x_sp[idx_sp], y_sp[idx_sp]
        side = -1.0 if (b_k % 2 == 0) else 1.0

        # Bell size grows from apical youngest buds (b_k=0) to mature basal bells (b_k=9)
        size_scale = 0.68 + 0.48 * (b_k / float(n_bells - 1))
        # Metachronal contraction phase
        psi_k = 2.0 * phi - b_k * 0.68
        contract = 0.5 + 0.5 * np.sin(psi_k)  # 1 = peak systole jet, 0 = diastole refill

        bell_len = 136.0 * size_scale * (1.0 + 0.12 * contract)
        bell_rad = 62.0 * size_scale * (1.0 - 0.22 * contract)

        # Bell axis points outward and slightly downward (+24 deg from horizontal)
        ang_bell = (np.pi - 0.38) if side < 0 else 0.38
        ca, sa = np.cos(ang_bell), np.sin(ang_bell)
        nx, ny = -sa, ca

        # Construct 14-slice bilobed medusoid bell profile from pedicular attachment (sx, sy) to velar ostium
        n_sl = 14
        v_sl = np.linspace(0.0, 1.0, n_sl, dtype=np.float32)
        # Outer exumbrella width envelope and inner subumbrella cavity envelope
        w_out = bell_rad * np.sin(np.pi * (v_sl**0.72) * 0.86)
        w_sub = 0.68 * w_out * (1.0 - 0.18 * contract)

        for m in range(n_sl - 1):
            d0, d1 = v_sl[m] * bell_len, v_sl[m + 1] * bell_len
            wo0, wo1 = w_out[m], w_out[m + 1]
            ws0, ws1 = w_sub[m], w_sub[m + 1]

            p0x, p0y = sx + d0 * ca, sy + d0 * sa
            p1x, p1y = sx + d1 * ca, sy + d1 * sa

            bell_quads_outer.append(
                [
                    [p0x - wo0 * nx, p0y - wo0 * ny],
                    [p1x - wo1 * nx, p1y - wo1 * ny],
                    [p1x + wo1 * nx, p1y + wo1 * ny],
                    [p0x + wo0 * nx, p0y + wo0 * ny],
                ]
            )
            if m >= 2:
                bell_quads_sub.append(
                    [
                        [p0x - ws0 * nx, p0y - ws0 * ny],
                        [p1x - ws1 * nx, p1y - ws1 * ny],
                        [p1x + ws1 * nx, p1y + ws1 * ny],
                        [p0x + ws0 * nx, p0y + ws0 * ny],
                    ]
                )

            # Looped radial gastrovascular canals along the nectophore mantle
            canal_segs.append(
                [p0x - ws0 * 0.85 * nx, p0y - ws0 * 0.85 * ny, p1x - ws1 * 0.85 * nx, p1y - ws1 * 0.85 * ny]
            )
            canal_segs.append(
                [p0x + ws0 * 0.85 * nx, p0y + ws0 * 0.85 * ny, p1x + ws1 * 0.85 * nx, p1y + ws1 * 0.85 * ny]
            )
            canal_segs.append([p0x, p0y, p1x, p1y])

        # Ejected Multi-Ring Vortex Wake Plume from the Velar Aperture at tip of bell
        ost_x = sx + bell_len * ca
        ost_y = sy + bell_len * sa
        jet_len = (165.0 + 95.0 * contract) * size_scale
        jx = ost_x + jet_len * ca
        jy = ost_y + jet_len * sa
        jet_segs.append([ost_x, ost_y, jx, jy])
        # 4 propagating vortex-ring cross-bars along the wake axis
        for vr_idx in range(4):
            vr_frac = ((vr_idx * 0.25 + (phi / (2.0 * np.pi))) % 1.0)
            vx_c = ost_x + vr_frac * jet_len * ca
            vy_c = ost_y + vr_frac * jet_len * sa
            vr_w = (16.0 + 34.0 * vr_frac) * size_scale
            jet_segs.append([vx_c - vr_w * nx, vy_c - vr_w * ny, vx_c + vr_w * nx, vy_c + vr_w * ny])
            jet_segs.append(
                [
                    vx_c - vr_w * nx - 10.0 * ca,
                    vy_c - vr_w * ny - 10.0 * sa,
                    vx_c - vr_w * nx + 10.0 * ca,
                    vy_c - vr_w * ny + 10.0 * sa,
                ]
            )
            jet_segs.append(
                [
                    vx_c + vr_w * nx - 10.0 * ca,
                    vy_c + vr_w * ny - 10.0 * sa,
                    vx_c + vr_w * nx + 10.0 * ca,
                    vy_c + vr_w * ny + 10.0 * sa,
                ]
            )

    py5.no_stroke()
    py5.fill(*NECTO_CERULEAN, 150)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(bell_quads_outer, dtype=np.float32).reshape(-1, 2))

    py5.fill(*NECTO_ICE, 185)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(bell_quads_sub, dtype=np.float32).reshape(-1, 2))

    py5.stroke(*COENOSARC_GOLD, 215)
    py5.stroke_weight(1.6)
    py5.lines(np.array(canal_segs, dtype=np.float32))

    py5.stroke(*JET_VIRIDIAN, 235)
    py5.stroke_weight(2.4)
    py5.lines(np.array(jet_segs, dtype=np.float32))

    # 3. Render Lower Siphosome Cormidia (Phyllozooid Bracts + Coral Gastrozooids + Coiled Cnidoband Tentilla)
    n_cormidia = 9
    bract_quads = []
    gastro_quads = []
    tentilla_segs = []
    cnido_nodes = []

    for c_k in range(n_cormidia):
        u_c = 0.52 + (c_k / float(n_cormidia - 1)) * 0.44
        idx_c = int(u_c * (n_spine - 1))
        cx_c, cy_c = x_sp[idx_c], y_sp[idx_c]
        side = -1.0 if (c_k % 2 == 0) else 1.0

        # 1) Hyaline Leaf-like Protective Bract (Phyllozooid)
        ang_br = (np.pi - 0.48) if side < 0 else 0.48
        ang_br += 0.12 * np.sin(phi + c_k)
        ca, sa = np.cos(ang_br), np.sin(ang_br)
        nx, ny = -sa, ca
        b_len = 138.0
        for m in range(8):
            f0, f1 = m / 8.0, (m + 1) / 8.0
            w0 = 32.0 * np.sin(np.pi * f0)
            w1 = 32.0 * np.sin(np.pi * f1)
            p0x, p0y = cx_c + f0 * b_len * ca, cy_c + f0 * b_len * sa
            p1x, p1y = cx_c + f1 * b_len * ca, cy_c + f1 * b_len * sa
            bract_quads.append(
                [
                    [p0x - w0 * nx, p0y - w0 * ny],
                    [p1x - w1 * nx, p1y - w1 * ny],
                    [p1x + w1 * nx, p1y + w1 * ny],
                    [p0x + w0 * nx, p0y + w0 * ny],
                ]
            )

        # 2) Muscular Coral-Vermilion Gastrozooid Polyp (with basigaster & trumpet mouth)
        ang_g = ang_br + side * 0.34
        cg, sg = np.cos(ang_g), np.sin(ang_g)
        ng_x, ng_y = -sg, cg
        g_len = 108.0 + 14.0 * np.cos(phi * 2.0 + c_k)
        for m in range(8):
            f0, f1 = m / 8.0, (m + 1) / 8.0
            w0 = 20.0 * np.sin(np.pi * (f0**0.8)) + 5.0 * (f0**2)
            w1 = 20.0 * np.sin(np.pi * (f1**0.8)) + 5.0 * (f1**2)
            p0x, p0y = cx_c + f0 * g_len * cg, cy_c + f0 * g_len * sg
            p1x, p1y = cx_c + f1 * g_len * cg, cy_c + f1 * g_len * sg
            gastro_quads.append(
                [
                    [p0x - w0 * ng_x, p0y - w0 * ng_y],
                    [p1x - w1 * ng_x, p1y - w1 * ng_y],
                    [p1x + w1 * ng_x, p1y + w1 * ng_y],
                    [p0x + w0 * ng_x, p0y + w0 * ng_y],
                ]
            )

        # 3) Sweeping Pelagic Fishing Tentacle Curtain & Hanging Cnidoband Tentilla Sub-Filaments
        u_t = np.linspace(0.0, 1.0, 40, dtype=np.float32)
        tx_pts = cx_c + side * (75.0 * u_t + 365.0 * (u_t**1.15)) + 24.0 * np.sin(4.0 * np.pi * u_t - phi + c_k)
        ty_pts = cy_c + 155.0 * (u_t**1.25) + 18.0 * np.cos(3.0 * np.pi * u_t - phi)

        # Clamp strictly inside INNER_R - 28 px
        r_t = np.hypot(tx_pts - CX, ty_pts - CY)
        sc_t = np.minimum(1.0, (INNER_R - 28.0) / np.maximum(r_t, 1.0))
        tx_pts = CX + (tx_pts - CX) * sc_t
        ty_pts = CY + (ty_pts - CY) * sc_t

        t_arr = np.column_stack((tx_pts, ty_pts))
        tentilla_segs.append(np.hstack((t_arr[:-1], t_arr[1:])))

        # Hanging vertical tentilla sub-branches with coiled cnidoband beads
        for k_br in range(5, 39, 5):
            bx0, by0 = tx_pts[k_br], ty_pts[k_br]
            drop_x = bx0 + 8.0 * np.sin(phi * 2.0 + k_br)
            drop_y = min(by0 + 38.0, CY + np.sqrt(max(0.0, (INNER_R - 32.0) ** 2 - (drop_x - CX) ** 2)))
            tentilla_segs.append(np.array([[bx0, by0, drop_x, drop_y]], dtype=np.float32))
            cnido_nodes.append((drop_x, drop_y, k_br % 2 == 0))

    py5.no_stroke()
    py5.fill(*NECTO_CERULEAN, 110)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(bract_quads, dtype=np.float32).reshape(-1, 2))

    py5.fill(*GASTRO_CORAL, 235)
    with py5.begin_shape(py5.QUADS):
        py5.vertices(np.array(gastro_quads, dtype=np.float32).reshape(-1, 2))

    py5.stroke(*CNIDO_AMETHYST, 215)
    py5.stroke_weight(1.8)
    py5.lines(np.vstack(tentilla_segs))

    for nx_c, ny_c, is_red in cnido_nodes:
        py5.fill(*(PNEUMA_CRIMSON if is_red else CNIDO_AMETHYST))
        py5.stroke(*BRASS_BRIGHT, 190)
        py5.stroke_weight(1.0)
        py5.circle(nx_c, ny_c, 8.5)

    # 4. Draw Central Golden Coenosarc Muscular Stem & Apical CO-Filled Pneumatophore Float
    sp_pts = np.column_stack((x_sp, y_sp))
    sp_segs = np.hstack((sp_pts[:-1], sp_pts[1:]))
    py5.stroke(*COENOSARC_GOLD, 250)
    py5.stroke_weight(6.2)
    py5.lines(sp_segs)
    py5.stroke(*PNEUMA_CRIMSON, 220)
    py5.stroke_weight(2.0)
    py5.lines(sp_segs)

    # Apical Pneumatophore Float at (x_sp[0], y_sp[0])
    px0, py0 = x_sp[0], y_sp[0]
    py5.fill(*COENOSARC_GOLD)
    py5.stroke(*BRASS_BRIGHT, 245)
    py5.stroke_weight(2.4)
    py5.ellipse(px0, py0 - 16.0, 38.0, 62.0)
    # Crimson apical gas-pore cap
    py5.fill(*PNEUMA_CRIMSON)
    py5.ellipse(px0, py0 - 34.0, 24.0, 22.0)

    # Anatomical region callout badges inside the medallion
    py5.text_font(FONT_MONO)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(11)
    callouts = [
        (CX, CY - 602.0, 340.0, "APICAL PNEUMATOPHORE (CO GAS FLOAT)", BRASS_BRIGHT),
        (CX - 345.0, CY - 340.0, 265.0, "NECTOSOME (10 JET BELLS)", NECTO_ICE),
        (CX + 345.0, CY - 140.0, 265.0, "VELAR VORTEX RINGS (Re=420)", JET_VIRIDIAN),
        (CX - 365.0, CY + 65.0, 275.0, "SIPHOSOME CORMIDIA REPEATS", GASTRO_CORAL),
        (CX + 355.0, CY + 290.0, 265.0, "CNIDOBAND TENTILLA BATTERIES", CNIDO_AMETHYST),
    ]
    for lx_c, ly_c, lw_c, l_str, l_col in callouts:
        py5.fill(*ABYSS_BG, 220)
        py5.stroke(*BORDER_BRONZE, 180)
        py5.stroke_weight(1.2)
        py5.rect(lx_c - lw_c * 0.5, ly_c - 12.0, lw_c, 24.0, 4)
        py5.fill(*l_col)
        py5.text(l_str, lx_c, ly_c)

    # Bottom viewport telemetry pill inside medallion
    badge_w = 540.0
    badge_y = CY + INNER_R - 138.0
    py5.fill(*ABYSS_BG, 238)
    py5.stroke(*BRASS_BRIGHT, 210)
    py5.stroke_weight(1.5)
    py5.rect(CX - badge_w * 0.5, badge_y, badge_w, 44.0, 6)
    py5.fill(*BRASS_BRIGHT)
    py5.text_size(12)
    py5.text(
        "SUPERORGANISM COLONY  |  2 BUDDING ZONES  |  10 NECTOPHORES + 9 CORMIDIA",
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
        "SINGLE NECTOPHORE SUBUMBRELLAR CAVITY & VELAR JET VORTEX",
        "FIG. 02",
        "BIPOLAR BLASTEMA BUDDING ZONES (NECTOSOME VS. SIPHOSOME)",
    )

    # --- FIG. 01: Anatomical Cross-Section of a Single Contracting Nectophore ---
    bx, by, bw, bh = x + 36.0, y + 64.0, 520.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(bx, by, bw, bh, 6)

    ncx = bx + 205.0
    ncy = by + bh * 0.5
    contract = 0.5 + 0.5 * np.sin(phi * 2.0)

    # Outer hyaline exumbrella dome
    py5.fill(*NECTO_CERULEAN, 95)
    py5.stroke(*NECTO_CERULEAN, 240)
    py5.stroke_weight(2.6)
    py5.ellipse(ncx, ncy, 250.0, 210.0 * (1.0 - 0.14 * contract))

    # Inner muscular subumbrella cavity + looped radial mantle canals
    py5.fill(*ABYSS_BG)
    py5.stroke(*COENOSARC_GOLD, 240)
    py5.stroke_weight(2.4)
    sub_h = 136.0 * (1.0 - 0.25 * contract)
    py5.ellipse(ncx + 18.0, ncy, 178.0, sub_h)

    # Velar nozzle aperture at right edge of bell (ncx + 108)
    vel_x = ncx + 108.0
    vel_gap = 28.0 * (1.0 - 0.35 * contract)
    py5.stroke(*PNEUMA_CRIMSON, 250)
    py5.stroke_weight(4.0)
    py5.line(vel_x, ncy - 68.0, vel_x, ncy - vel_gap)
    py5.line(vel_x, ncy + vel_gap, vel_x, ncy + 68.0)

    # Shed counter-rotating Vortex Ring pair translating rightward in wake!
    vr_x = vel_x + 36.0 + ((phi / (2.0 * np.pi)) * 125.0) % 125.0
    py5.no_fill()
    py5.stroke(*JET_VIRIDIAN, 240)
    py5.stroke_weight(2.6)
    py5.circle(vr_x, ncy - 26.0, 34.0)
    py5.circle(vr_x, ncy + 26.0, 34.0)
    py5.line(vel_x + 8.0, ncy, vr_x + 22.0, ncy)

    py5.text_font(FONT_MONO)
    py5.text_size(11)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*NECTO_ICE)
    py5.text("EXUMBRELLA MESOGLEA", bx + 20.0, by + 18.0)
    py5.fill(*COENOSARC_GOLD)
    py5.text("4 RADIAL + RING CANALS", bx + 20.0, by + bh - 34.0)
    py5.fill(*JET_VIRIDIAN)
    py5.text("VORTEX RING", vr_x - 36.0, ncy + 52.0)

    # Right telemetry specs for FIG. 01
    rx = bx + bw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(15)
    py5.text("NECTOPHORE JET KINEMATICS", rx, by + 6.0)
    specs_f1 = [
        ("BELL VOLUME", "V_0 = 42.5 mm^3"),
        ("EJECTION FRAC", "Delta_V / V_0 = 0.64"),
        ("VELAR NOZZLE", "d_v = 1.85 mm (Variable)"),
        ("FORMATION NUM", "L / D = 3.8 (Optimal Vortex)"),
        ("JET VELOCITY", f"u_jet = {18.5 + 9.2 * contract:04.1f} cm/s"),
        ("CANAL TOPOLOGY", "4 Radial + 1 Ostial Ring"),
        ("MUSCLE FIBER", "Striated Subumbrellar Sheet"),
        ("NERVE RING", "Duplex Inner/Outer Margin"),
        ("THRUST PULSE", f"F_bell = {0.42 + 0.35 * contract:04.2f} mN"),
    ]
    for i, (k_s, v_s) in enumerate(specs_f1):
        yy = by + 42.0 + i * 32.0
        py5.fill(*INK_MUTED)
        py5.text_size(13)
        py5.text(k_s, rx, yy)
        py5.fill(*(PNEUMA_CRIMSON if i in (3, 4, 8) else INK_CHARCOAL))
        py5.text(v_s, rx + 158.0, yy)

    # --- FIG. 02: Bipolar Budding Zones (Proliferation Zone Z_N vs. Z_S) ---
    mid_y = y + h * 0.5
    zx, zy, zw, zh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(zx, zy, zw, zh, 6)

    # Horizontal developmental schematic of the Coenosarc growth zones
    cy_z = zy + zh * 0.52
    py5.stroke(*COENOSARC_GOLD, 245)
    py5.stroke_weight(6.0)
    py5.line(zx + 90.0, cy_z, zx + zw - 60.0, cy_z)

    # Left: Pneumatophore Float at zx + 90
    py5.fill(*PNEUMA_CRIMSON)
    py5.stroke(*BRASS_BRIGHT)
    py5.stroke_weight(2.0)
    py5.ellipse(zx + 90.0, cy_z, 68.0, 44.0)

    # Budding Zone 1 (Nectosomal Horn at zx + 210) -> buds nectophores to the right (zx+250..460)
    py5.fill(*JET_VIRIDIAN)
    py5.circle(zx + 195.0, cy_z - 22.0, 22.0)
    for b_i in range(4):
        bx_n = zx + 255.0 + b_i * 58.0
        rad_n = 16.0 + b_i * 6.5
        py5.fill(*NECTO_CERULEAN, 190)
        py5.stroke(*NECTO_ICE)
        py5.stroke_weight(1.6)
        py5.ellipse(bx_n, cy_z - 36.0 if b_i % 2 == 0 else cy_z + 36.0, rad_n * 1.6, rad_n * 1.2)

    # Budding Zone 2 (Siphosomal Horn at zx + 530) -> buds reiterative cormidia (zx+580..860)
    py5.fill(*PNEUMA_CRIMSON)
    py5.stroke(*BRASS_BRIGHT)
    py5.circle(zx + 530.0, cy_z + 22.0, 22.0)
    for c_i in range(4):
        cx_s = zx + 595.0 + c_i * 74.0
        py5.fill(*GASTRO_CORAL, 220)
        py5.stroke(*COENOSARC_GOLD)
        py5.rect(cx_s - 18.0, cy_z + 14.0, 36.0, 48.0, 6)
        py5.fill(*CNIDO_AMETHYST)
        py5.circle(cx_s, cy_z + 78.0, 14.0)

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*BRASS_BRIGHT)
    py5.text("DUNN & WAGNER (2006) BIPOLAR GROWTH ARCHITECTURE: TWO OPPOSING STEM-CELL BLASTEMAS", zx + 24.0, zy + 18.0)
    py5.fill(*JET_VIRIDIAN)
    py5.text("ZONE I: NECTOSOMAL HORN (BUDS SWIMMING BELLS)", zx + 165.0, zy + 52.0)
    py5.fill(*GASTRO_CORAL)
    py5.text("ZONE II: SIPHOSOMAL HORN (PRODUCES CORMIDIA)", zx + 515.0, zy + zh - 36.0)


def draw_left_bottom_card(phi: float):
    x, y, w, h = LEFT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 03",
        "COSTELLO MULTI-JET TORQUE LEVER ARMS (APICAL STEER VS. BASAL THRUST)",
        "FIG. 04",
        "H.M.S. CHALLENGER SIPHONOPHORAE ARCHIVAL PALETTE",
    )

    # --- FIG. 03: Costello et al. (PNAS 2015) Torque vs. Axial Thrust Bar & Vector Plot ---
    tx, ty, tw, th = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(tx, ty, tw, th, 6)

    left_p = tx + 68.0
    base_p = ty + th - 52.0
    plot_w = tw - 104.0

    # 10 Nectophores from N01 (Apical: high torque lever arm, low thrust) to N10 (Basal: high axial thrust)
    bar_w = plot_w / 10.0
    for k in range(10):
        frac = k / 9.0
        bx_k = left_p + k * bar_w
        pulse = 0.75 + 0.25 * np.sin(2.0 * phi - k * 0.68)
        # Apical torque bar (Cerulean) vs. Basal axial thrust bar (Coral-Gold)
        torque_h = (1.0 - frac * 0.72) * 205.0 * pulse
        thrust_h = (0.18 + 0.82 * (frac**1.3)) * 220.0 * pulse

        py5.fill(*NECTO_CERULEAN, 215)
        py5.no_stroke()
        py5.rect(bx_k + 8.0, base_p - torque_h, bar_w * 0.38, torque_h, 3)

        py5.fill(*GASTRO_CORAL, 230)
        py5.rect(bx_k + 8.0 + bar_w * 0.42, base_p - thrust_h, bar_w * 0.38, thrust_h, 3)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.fill(*NECTO_ICE)
        py5.text_size(11)
        py5.text(f"N{k + 1:02d}", bx_k + bar_w * 0.48, base_p + 14.0)

    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(12)
    py5.fill(*NECTO_CERULEAN)
    py5.text("CERULEAN: STEERING TORQUE M_z = r_k x F_jet (PEAKS AT APICAL NECTOPHORES N01-N03)", left_p + 12.0, ty + 20.0)
    py5.fill(*GASTRO_CORAL)
    py5.text("CORAL: FORWARD AXIAL THRUST F_z = F_jet * cos(theta_k) (PEAKS AT BASAL BELLS N08-N10)", left_p + 12.0, ty + 42.0)

    # --- FIG. 04: 6 Chromatic Swatches ---
    mid_y = y + h * 0.5
    swatches = [
        (PNEUMA_CRIMSON, "PNEUMATOPHORE CRIMSON", "#EA3068 // CO FLOAT APEX"),
        (NECTO_CERULEAN, "HYALINE NECTOPHORE", "#26B6F8 // SWIMMING BELL"),
        (COENOSARC_GOLD, "COENOSARC STEM GOLD", "#FCC23A // AXIAL CANAL"),
        (GASTRO_CORAL, "GASTROZOOID CORAL", "#F86A3E // FEEDING POLYP"),
        (CNIDO_AMETHYST, "CNIDOBAND AMETHYST", "#A84EF4 // NEMATOCYST COIL"),
        (JET_VIRIDIAN, "VELAR VORTEX VIRIDIAN", "#18DA9E // WAKE RING JET"),
    ]
    sw_w = (w - 96.0) / 3.0
    sw_h = 152.0
    for i, (scol, sname, sdesc) in enumerate(swatches):
        col_i = i % 3
        row_i = i // 3
        bx_s = x + 36.0 + col_i * (sw_w + 12.0)
        by_s = mid_y + 62.0 + row_i * (sw_h + 18.0)
        py5.fill(*PANEL_MIST)
        py5.stroke(*BORDER_BRONZE, 200)
        py5.stroke_weight(1.4)
        py5.rect(bx_s, by_s, sw_w, sw_h, 6)

        py5.fill(*scol)
        py5.stroke(*INK_CHARCOAL, 120)
        py5.stroke_weight(1.0)
        py5.rect(bx_s + 14.0, by_s + 14.0, sw_w - 28.0, 66.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*INK_CHARCOAL)
        py5.text_size(13)
        py5.text(sname, bx_s + 14.0, by_s + 92.0)
        py5.fill(*INK_SLATE)
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
        "SIPHOSOMAL CORMIDIUM METAMERIC MODULE (DIVISION OF LABOR)",
        "FIG. 06",
        "SIPHONOPHORA POLYMORPHISM & PROPULSION LEDGER (1853-2015)",
    )

    # --- FIG. 05: 4 Polymorphic Zooid Types inside a Single Cormidium Repeat ---
    cx0, cy0, cw, ch = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(cx0, cy0, cw, ch, 6)

    zooids = [
        ("1. PHYLLOZOOID (BRACT)", NECTO_CERULEAN, "Buoyant mesoglea shield & armor"),
        ("2. GASTROZOOID (SIPHON)", GASTRO_CORAL, "Digestive polyp + single tentacle"),
        ("3. DACTYLOZOOID (PALPON)", JET_VIRIDIAN, "Tactile/excretory taster zooid"),
        ("4. GONOPHORE (GONODENDRON)", CNIDO_AMETHYST, "Dioecious medusoid gamete cluster"),
    ]
    zw_box = (cw - 42.0) * 0.5
    zh_box = (ch - 42.0) * 0.5
    for idx_z, (z_title, z_col, z_desc) in enumerate(zooids):
        ci = idx_z % 2
        ri = idx_z // 2
        bx_z = cx0 + 14.0 + ci * (zw_box + 14.0)
        by_z = cy0 + 14.0 + ri * (zh_box + 14.0)
        py5.fill(16, 26, 48, 220)
        py5.stroke(*z_col, 210)
        py5.stroke_weight(1.5)
        py5.rect(bx_z, by_z, zw_box, zh_box, 5)

        # Mini zooid morphological glyph on left of cell
        gx_z = bx_z + 62.0
        gy_z = by_z + zh_box * 0.54
        py5.fill(*z_col, 185)
        py5.stroke(*BRASS_BRIGHT)
        py5.stroke_weight(1.8)
        py5.ellipse(gx_z, gy_z, 68.0, 38.0 + 6.0 * np.sin(phi + idx_z))
        py5.fill(*COENOSARC_GOLD)
        py5.circle(gx_z - 26.0, gy_z, 10.0)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*z_col)
        py5.text_size(13)
        py5.text(z_title, bx_z + 116.0, by_z + 24.0)
        py5.fill(*NECTO_ICE)
        py5.text_size(11)
        py5.text(z_desc, bx_z + 116.0, by_z + 56.0)
        py5.fill(*COENOSARC_GOLD)
        py5.text("HOMOLOGOUS POLYP / MEDUSA BUD", bx_z + 116.0, by_z + 88.0)

    # --- FIG. 06: Historical Siphonophore Ledger ---
    mid_y = y + h * 0.5
    tx, ty, tw, th = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PANEL_MIST)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(tx, ty, tw, th, 6)

    headers = ["YEAR", "INVESTIGATOR / EXPEDITION", "SPECIES / GROUP", "KEY DISCOVERY"]
    col_xs = [tx + 20, tx + 96, tx + 410, tx + 675]
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(tx + 2, ty + 2, tw - 4, 38, 4)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(13)
    for cx_h, h_str in zip(col_xs, headers):
        py5.text(h_str, cx_h, ty + 21)

    rows = [
        ("1853", "A. Kölliker (Messina Strait)", "Physophora hydrostatica", "Colonial Coenosarc Continuity"),
        ("1854", "R. Leuckart (Giessen)", "Calycophorae / Physonectae", "Division-of-Labor Polymorphism"),
        ("1888", "E. Haeckel (H.M.S. Challenger)", "142 Pelagic Siphonophores", "Siphonanthae vs. Disconanthae"),
        ("1965", "A. K. Totton (British Museum)", "World Siphonophora Synopsis", "Nectophore Canal Homologies"),
        ("2005", "C. W. Dunn (Yale / MBARI)", "Marrus orthocanna / Nanomia", "Bipolar Proliferation Blastemas"),
        ("2015", "S. P. Colin & J. H. Costello", "Nanomia bijuga Multi-Jet", "Apical Torque vs. Basal Thrust"),
    ]
    for r_i, r_vals in enumerate(rows):
        ry_row = ty + 52.0 + r_i * 47.0
        if r_i % 2 == 1:
            py5.fill(*CARD_HEADER_BG, 145)
            py5.no_stroke()
            py5.rect(tx + 8, ry_row - 8, tw - 16, 40, 3)
        for c_i, (cx_c, val_str) in enumerate(zip(col_xs, r_vals)):
            py5.fill(*(PNEUMA_CRIMSON if c_i == 0 else (INK_CHARCOAL if c_i == 1 else INK_SLATE)))
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
        "COILED TENTILLUM CNIDOBAND & NEMATOCYST BALLISTIC DISCHARGE",
        "FIG. 08",
        "10-NECTOPHORE METACHRONAL JET MATRIX & SURGE OSCILLOGRAM",
    )

    # --- FIG. 07: Coiled Cnidoband Spiral + Terminal Elastic Filament ---
    px, py, pw, ph = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(px, py, pw, ph, 6)

    # Draw helical coiled Cnidoband battery across left/center of FIG. 07
    u_sp = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_coil = px + 85.0 + u_sp * 560.0
    amp_coil = 72.0 * np.sin(np.pi * u_sp)
    y_coil = py + ph * 0.48 + amp_coil * np.sin(14.0 * np.pi * u_sp - 2.0 * phi)
    pts_coil = np.column_stack((x_coil, y_coil))

    # Translucent involucrum sheath
    py5.no_fill()
    py5.stroke(*NECTO_CERULEAN, 130)
    py5.stroke_weight(2.0)
    py5.ellipse(px + 365.0, py + ph * 0.48, 590.0, 185.0)

    # Coiled Cnidoband armed with heteroneme & haploneme nematocysts
    py5.stroke(*PNEUMA_CRIMSON, 250)
    py5.stroke_weight(4.2)
    py5.lines(np.hstack((pts_coil[:-1], pts_coil[1:])))

    # Terminal filament extending to the right (px+645..px+pw-36)
    u_tf = np.linspace(0.0, 1.0, 80, dtype=np.float32)
    x_tf = px + 645.0 + u_tf * (pw - 685.0)
    y_tf = py + ph * 0.48 + 38.0 * np.sin(6.0 * np.pi * u_tf - 3.0 * phi)
    pts_tf = np.column_stack((x_tf, y_tf))
    py5.stroke(*COENOSARC_GOLD, 240)
    py5.stroke_weight(2.4)
    py5.lines(np.hstack((pts_tf[:-1], pts_tf[1:])))

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*PNEUMA_CRIMSON)
    py5.text("HELICAL CNIDOBAND (2,400 HETERONEME + HAPLONEME NEMATOCYSTS // 150 ATM OSMOTIC PRESSURE)", px + 24.0, py + 18.0)
    py5.fill(*COENOSARC_GOLD)
    py5.text("TERMINAL FILAMENT (DESMONEMES)", px + 635.0, py + ph - 36.0)

    # --- FIG. 08: 10-Nectophore Metachronal Contraction Matrix + Surge Velocity Oscillogram ---
    mid_y = y + h * 0.5
    ox, oy, ow, oh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*ABYSS_BG)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(ox, oy, ow, oh, 6)

    # Top row: 10 Nectophore Jet State Cells (N01..N10)
    cell_w = (ow - 48.0) / 10.0
    for k_b in range(10):
        bx_i = ox + 24.0 + k_b * cell_w
        by_i = oy + 18.0
        c_val = 0.5 + 0.5 * np.sin(2.0 * phi - k_b * 0.68)
        is_jetting = c_val > 0.68
        py5.fill(*(JET_VIRIDIAN if is_jetting else NECTO_CERULEAN), int(120 + 125 * c_val))
        py5.stroke(*(BRASS_BRIGHT if is_jetting else BORDER_BRONZE))
        py5.stroke_weight(1.8 if is_jetting else 1.2)
        py5.rect(bx_i + 3.0, by_i, cell_w - 6.0, 52.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*INK_CHARCOAL if is_jetting else NECTO_ICE)
        py5.text_size(14)
        py5.text(f"N{k_b + 1:02d}", bx_i + cell_w * 0.5, by_i + 18.0)
        py5.text_size(11)
        py5.text(f"{int(c_val * 100):02d}%", bx_i + cell_w * 0.5, by_i + 38.0)

    # Lower half: 3-trace Multi-Jet Thrust, Torque & Colony Surge Velocity Oscillogram
    osc_cy = oy + 204.0
    py5.stroke(36, 52, 82, 190)
    py5.stroke_weight(1.0)
    py5.line(ox + 24.0, osc_cy, ox + ow - 24.0, osc_cy)

    u_o = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_o = ox + 24.0 + u_o * (ow - 48.0)
    w_thrust = 68.0 * np.sin(6.0 * np.pi * u_o - 2.0 * phi) * np.cos(2.0 * np.pi * u_o + phi)
    w_torque = 54.0 * np.cos(10.0 * np.pi * u_o - 3.0 * phi)
    w_surge = 42.0 * np.sin(4.0 * np.pi * u_o - 2.0 * phi + 0.6)

    for w_arr, w_col in ((w_thrust, JET_VIRIDIAN), (w_torque, NECTO_CERULEAN), (w_surge, COENOSARC_GOLD)):
        pts_o = np.column_stack((x_o, osc_cy - w_arr))
        py5.stroke(*w_col, 235)
        py5.stroke_weight(2.4)
        py5.lines(np.hstack((pts_o[:-1], pts_o[1:])))

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*BRASS_BRIGHT)
    py5.text_size(12)
    py5.text(
        "ASYNCHRONOUS METACHRONAL WAVE: QUASI-STEADY SURGE VELOCITY U_col = 14.8 cm/s (COSTELLO ET AL., 2015)",
        ox + 26.0,
        oy + oh - 12.0,
    )


def draw():
    frame_idx = py5.frame_count - 1
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phi = 2.0 * np.pi * t_norm + (SEED_OFFSET % 100) * 0.01

    py5.background(*BG_VELLUM)

    thrust_mn = 4.85 + 0.92 * np.sin(2.0 * phi)

    draw_frame_border_and_header(phi, thrust_mn)
    draw_central_siphonophore_medallion(phi)
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

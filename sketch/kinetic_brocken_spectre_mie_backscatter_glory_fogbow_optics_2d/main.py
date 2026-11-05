# py5 Media Art — Autonomous Animation
# Work: kinetic_brocken_spectre_mie_backscatter_glory_fogbow_optics_2d
# Genre: Atmospheric / Painterly / Color Field (Genre 4)
# Background Polarity: Light (#f6f2e8 Warm Brocken & Ben Nevis Meteorological Vellum)

from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import py5

WORK_NAME = "kinetic_brocken_spectre_mie_backscatter_glory_fogbow_optics_2d"
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC  # 720 frames

OUT_DIR = Path(__file__).parent
FRAMES_DIR = OUT_DIR / "frames"
PREVIEW_PATH = OUT_DIR / f"{WORK_NAME}_p1.png"
VIDEO_PATH = OUT_DIR / "output.mp4"

# Palette — Warm Brocken & Ben Nevis Meteorological Vellum (#f6f2e8)
BG_VELLUM = (246, 242, 232)
CARD_BG = (252, 249, 242)
CARD_HEADER_BG = (236, 229, 214)
PANEL_DARK = (14, 22, 38)
PANEL_MIST = (240, 234, 220)

# Ink & Framing
INK_CHARCOAL = (24, 30, 44)
INK_SLATE = (72, 84, 106)
INK_MUTED = (118, 128, 148)
BORDER_BRONZE = (158, 136, 98)
BRASS_GOLD = (196, 142, 38)
BRASS_BRIGHT = (244, 196, 78)

# Glory & Nebelbogen Spectral Chromatics
AUREOLE_GOLD = (255, 236, 156)
GLORY_CRIMSON = (228, 52, 108)
GLORY_CORAL = (248, 134, 62)
GLORY_EMERALD = (22, 198, 148)
GLORY_CERULEAN = (38, 168, 246)
GLORY_VIOLET = (142, 78, 238)
FOGBOW_PEARL = (242, 246, 255)
STRATUS_INDIGO = (22, 38, 68)
STRATUS_SLATE = (44, 72, 114)
SPECTRE_SHADOW = (9, 14, 26)

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

# Precomputed azimuth table for circular color-field glory & fogbow rings
N_AZIM = 96
THETA_AZ = np.linspace(0.0, 2.0 * np.pi, N_AZIM + 1, dtype=np.float32)
COS_AZ = np.cos(THETA_AZ)
SIN_AZ = np.sin(THETA_AZ)


def eval_glory_spectrum(r_norm: float, droplet_scale: float) -> tuple[int, int, int]:
    """
    Evaluate analytical Airy-Debye-Mie backscatter glory + Nebelbogen fogbow color field
    for normalized radius r_norm in [0, 1] from the Antisolar Point.
    """
    # Scale radial diffraction coordinate by live droplet radius modulation
    u = r_norm / droplet_scale

    # Base cloud-sea Prussian indigo-cerulean background inside medallion
    bg_r = 20.0 + 28.0 * (1.0 - r_norm)
    bg_g = 36.0 + 48.0 * (1.0 - r_norm)
    bg_b = 68.0 + 74.0 * (1.0 - r_norm)

    # Multi-wavelength Bessel-like backscatter interference for Red (650nm), Green (540nm), Blue (450nm)
    # In a glory, Red has the largest angular radius in each ring order, Blue the smallest!
    if u < 0.56:
        # Glory regime (0th-order central aureole + 1st, 2nd, 3rd diffraction rings)
        x_r = u * 18.2
        x_g = u * 21.6
        x_b = u * 25.4

        env = np.exp(-3.4 * u)
        # Central solar-gold aureole peak + multi-order oscillatory glory rings
        aureole = np.exp(-((u / 0.085) ** 2))
        ring_r = (0.5 + 0.5 * np.cos(x_r - 0.8)) * np.exp(-2.2 * u) * (1.0 - 0.5 * aureole)
        ring_g = (0.5 + 0.5 * np.cos(x_g - 0.8)) * np.exp(-2.3 * u) * (1.0 - 0.5 * aureole)
        ring_b = (0.5 + 0.5 * np.cos(x_b - 0.8)) * np.exp(-2.4 * u) * (1.0 - 0.5 * aureole)

        r_val = bg_r + 235.0 * aureole + 215.0 * ring_r * (1.0 + 0.35 * env)
        g_val = bg_g + 205.0 * aureole + 185.0 * ring_g * (1.0 + 0.25 * env)
        b_val = bg_b + 125.0 * aureole + 225.0 * ring_b * (1.0 + 0.30 * env)
    else:
        # Outer Nebelbogen (White Fogbow at r_norm ~ 0.78..0.88) + supernumerary inner ripples
        fog_main = np.exp(-(((u - 0.82) / 0.068) ** 2))
        fog_warm_outer = np.exp(-(((u - 0.865) / 0.038) ** 2))
        fog_cool_inner = np.exp(-(((u - 0.775) / 0.038) ** 2))
        supernum = 0.22 * np.exp(-(((u - 0.70) / 0.065) ** 2)) * (0.5 + 0.5 * np.cos((u - 0.65) * 95.0))

        r_val = bg_r + 188.0 * fog_main + 54.0 * fog_warm_outer + 32.0 * supernum
        g_val = bg_g + 194.0 * fog_main + 24.0 * fog_warm_outer + 28.0 * fog_cool_inner + 58.0 * supernum
        b_val = bg_b + 206.0 * fog_main + 64.0 * fog_cool_inner + 74.0 * supernum

    return (
        int(np.clip(r_val, 0, 255)),
        int(np.clip(g_val, 0, 255)),
        int(np.clip(b_val, 0, 255)),
    )


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


def draw_frame_border_and_header(phi: float, r_eff: float, sun_elev: float):
    # Outer archival vellum double-rule border
    py5.no_fill()
    py5.stroke(*BORDER_BRONZE, 235)
    py5.stroke_weight(2.2)
    py5.rect(42, 36, W - 84, H - 72, 8)
    py5.stroke(*INK_CHARCOAL, 150)
    py5.stroke_weight(1.0)
    py5.rect(50, 44, W - 100, H - 88, 6)

    # Top title banner
    py5.fill(*CARD_HEADER_BG, 245)
    py5.stroke(*BORDER_BRONZE, 220)
    py5.stroke_weight(1.6)
    py5.rect(84, 58, W - 168, 94, 6)

    py5.text_font(FONT_SANS)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(27)
    py5.text(
        "BROCKEN SPECTRE, MIE BACKSCATTER GLORY & NEBELBOGEN FOGBOW // ANTISOLAR CLOUD OPTICS",
        114,
        72,
    )

    py5.text_font(FONT_MONO)
    py5.fill(*INK_SLATE)
    py5.text_size(16)
    x_param = 2.0 * np.pi * r_eff / 0.550
    py5.text(
        f"STATION: BROCKEN / BEN NEVIS SUMMIT (1,141 m)   |   DROPLET r_eff = {r_eff:04.2f} um (x = {x_param:05.1f})   "
        f"|   SOLAR ELEVATION alpha = +{sun_elev:04.2f} deg   |   SURFACE WAVE: REGGE-DEBYE p=2",
        114,
        114,
    )

    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*GLORY_CRIMSON)
    py5.text_size(17)
    py5.text("SILBERSCHLAG (1780) // C. T. R. WILSON (1895) // VAN DE HULST (1947)", W - 114, 76)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(15)
    py5.text(
        f"ANTISOLAR RETRO-ANGLE theta = 172.0..180.0 deg   |   FOGBOW = 141.2 deg   |   PHASE = {phi / (2.0 * np.pi) * 100.0:05.1f}%",
        W - 114,
        114,
    )


def draw_flank_card(x: float, y: float, w: float, h: float, code1: str, title1: str, code2: str, title2: str):
    py5.fill(*CARD_BG, 248)
    py5.stroke(*BORDER_BRONZE, 225)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    # Top header bar
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, y + 2, w - 4, 42, 6)
    py5.stroke(*BORDER_BRONZE, 190)
    py5.stroke_weight(1.2)
    py5.line(x, y + 44, x + w, y + 44)

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*GLORY_CRIMSON)
    py5.text_size(16)
    py5.text(code1, x + 18, y + 23)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(16)
    py5.text(title1, x + 112, y + 23)

    # Mid divider + second header bar
    mid_y = y + h * 0.5
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, mid_y, w - 4, 42)
    py5.stroke(*BORDER_BRONZE, 190)
    py5.stroke_weight(1.2)
    py5.line(x, mid_y, x + w, mid_y)
    py5.line(x, mid_y + 42, x + w, mid_y + 42)

    py5.fill(*GLORY_CRIMSON)
    py5.text(code2, x + 18, mid_y + 21)
    py5.fill(*INK_CHARCOAL)
    py5.text(title2, x + 112, mid_y + 21)


def draw_central_glory_and_spectre_medallion(phi: float, r_eff: float, sun_az_shift: float):
    # Outer brass meteorological goniometer ring
    py5.fill(*CARD_HEADER_BG)
    py5.stroke(*INK_CHARCOAL, 230)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    # 72 azimuth degree ticks around the brass bezel
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

    # Antisolar center shifts slightly with grazing sun oscillation
    anti_x = CX + sun_az_shift
    anti_y = CY - 26.0
    droplet_scale = r_eff / 12.4

    # 1. Render 56 Concentric Painterly Color-Field Glory & Nebelbogen Fogbow Rings via py5.QUADS
    # Each ring is clipped naturally to the INNER_R circle by clamping outer radii
    n_rings = 56
    r_edges = np.linspace(0.0, INNER_R, n_rings + 1, dtype=np.float32)
    cos0, sin0 = COS_AZ[:-1], SIN_AZ[:-1]
    cos1, sin1 = COS_AZ[1:], SIN_AZ[1:]

    py5.no_stroke()
    for k in range(n_rings - 1, -1, -1):
        r0 = r_edges[k]
        r1 = r_edges[k + 1]
        r_mid_norm = 0.5 * (r0 + r1) / INNER_R
        col_rgb = eval_glory_spectrum(r_mid_norm, droplet_scale)

        # Gentle breathing wave perturbation on inner glory rings
        wobble0 = 1.0 + 0.012 * np.sin(4.0 * THETA_AZ[:-1] + phi) * (1.0 - r_mid_norm)
        wobble1 = 1.0 + 0.012 * np.sin(4.0 * THETA_AZ[1:] + phi) * (1.0 - r_mid_norm)

        # Center shift tapers to 0 at k == n_rings - 1 so outer edge is a perfect circle at (CX, CY)
        blend0 = 1.0 - (r0 / INNER_R) ** 2
        blend1 = 1.0 - (r1 / INNER_R) ** 2
        cx0 = CX + sun_az_shift * blend0
        cy0 = CY - 26.0 * blend0
        cx1 = CX + sun_az_shift * blend1
        cy1 = CY - 26.0 * blend1

        q_verts = np.zeros((N_AZIM * 4, 2), dtype=np.float32)
        q_verts[0::4, 0] = cx0 + r0 * wobble0 * cos0
        q_verts[0::4, 1] = cy0 + r0 * wobble0 * sin0
        q_verts[1::4, 0] = cx1 + r1 * wobble0 * cos0
        q_verts[1::4, 1] = cy1 + r1 * wobble0 * sin0
        q_verts[2::4, 0] = cx1 + r1 * wobble1 * cos1
        q_verts[2::4, 1] = cy1 + r1 * wobble1 * sin1
        q_verts[3::4, 0] = cx0 + r0 * wobble1 * cos1
        q_verts[3::4, 1] = cy0 + r0 * wobble1 * sin1

        py5.fill(*col_rgb, 255)
        with py5.begin_shape(py5.QUADS):
            py5.vertices(q_verts)

    # 2. Draw Billowing Stratus Nebulosus Cloud-Sea Wave Decks (Bokashi layered color field in lower hemisphere)
    n_decks = 9
    u_cloud = np.linspace(-0.96, 0.96, 120, dtype=np.float32)
    for d_i in range(n_decks):
        frac_d = d_i / float(n_decks - 1)
        y_base = CY + 85.0 + frac_d * 485.0
        # Chord half-width inside circle of radius INNER_R
        dy_c = y_base - CY
        if abs(dy_c) >= INNER_R - 20.0:
            continue
        max_dx = np.sqrt(max(0.0, (INNER_R - 6.0) ** 2 - dy_c**2))
        x_pts = CX + u_cloud * max_dx
        wave_y = (
            y_base
            + 18.0 * np.sin(3.5 * np.pi * u_cloud + phi * (1.0 if d_i % 2 == 0 else -1.0) + d_i * 0.9)
            + 9.0 * np.cos(7.0 * np.pi * u_cloud - 2.0 * phi + d_i)
        )
        # Clamp inside circle
        r_pts = np.hypot(x_pts - CX, wave_y - CY)
        clamp_scale = np.minimum(1.0, (INNER_R - 4.0) / np.maximum(r_pts, 1.0))
        x_clamped = CX + (x_pts - CX) * clamp_scale
        y_clamped = CY + (wave_y - CY) * clamp_scale

        # Draw sunlit golden-pearl cloud crest line
        crest_pts = np.column_stack((x_clamped, y_clamped))
        py5.stroke(*(AUREOLE_GOLD if d_i < 4 else FOGBOW_PEARL), int(155 - d_i * 11))
        py5.stroke_weight(2.4 - d_i * 0.14)
        py5.lines(np.hstack((crest_pts[:-1], crest_pts[1:])))

    # 3. Draw Antisolar Crepuscular Shadow Rays & Triangular Brocken Spectre Shadow Cone
    n_rays = 24
    ray_angles = np.linspace(0.0, 2.0 * np.pi, n_rays, endpoint=False) + 0.08 * np.sin(phi)
    ray_segs = np.zeros((n_rays, 4), dtype=np.float32)
    ray_segs[:, 0] = anti_x + 28.0 * np.cos(ray_angles)
    ray_segs[:, 1] = anti_y + 28.0 * np.sin(ray_angles)
    ray_segs[:, 2] = CX + (INNER_R - 12.0) * np.cos(ray_angles)
    ray_segs[:, 3] = CY + (INNER_R - 12.0) * np.sin(ray_angles)
    py5.stroke(*AUREOLE_GOLD, 72)
    py5.stroke_weight(1.4)
    py5.lines(ray_segs)

    # Elongated perspective shadow cone of the summit observer & meteorological cairn
    # Radiates from the Antisolar Point (anti_x, anti_y) down to the foreground ridge at bottom of medallion
    py5.no_stroke()
    # Outer penumbra shadow cone
    py5.fill(*SPECTRE_SHADOW, 125)
    with py5.begin_shape(py5.TRIANGLES):
        py5.vertex(anti_x - 14.0, anti_y - 12.0)
        py5.vertex(CX - 255.0 - sun_az_shift * 1.4, CY + INNER_R - 28.0)
        py5.vertex(CX + 255.0 - sun_az_shift * 1.4, CY + INNER_R - 28.0)

    # Inner umbra shadow of the Brocken Spectre figure + meteorological mast
    py5.fill(*SPECTRE_SHADOW, 210)
    with py5.begin_shape(py5.TRIANGLES):
        py5.vertex(anti_x, anti_y - 18.0)
        py5.vertex(CX - 118.0 - sun_az_shift * 1.1, CY + INNER_R - 14.0)
        py5.vertex(CX + 118.0 - sun_az_shift * 1.1, CY + INNER_R - 14.0)

    # Brocken Spectre head & shoulders silhouette right at the Antisolar Point center!
    py5.fill(*SPECTRE_SHADOW, 240)
    py5.stroke(*AUREOLE_GOLD, 220)
    py5.stroke_weight(1.8)
    # Shoulders trapezoid
    with py5.begin_shape(py5.QUADS):
        py5.vertex(anti_x - 22.0, anti_y + 12.0)
        py5.vertex(anti_x + 22.0, anti_y + 12.0)
        py5.vertex(anti_x + 36.0, anti_y + 58.0)
        py5.vertex(anti_x - 36.0, anti_y + 58.0)
    # Head silhouette at the exact center of the 0th-order diffraction aureole
    py5.circle(anti_x, anti_y - 4.0, 26.0)

    # Antisolar crosshair reticle
    py5.stroke(*GLORY_CRIMSON, 215)
    py5.stroke_weight(1.5)
    py5.line(anti_x - 42.0, anti_y - 4.0, anti_x - 16.0, anti_y - 4.0)
    py5.line(anti_x + 16.0, anti_y - 4.0, anti_x + 42.0, anti_y - 4.0)
    py5.line(anti_x, anti_y - 46.0, anti_x, anti_y - 20.0)

    # Optical ring callout labels inside the medallion with high-contrast dark pill backdrops
    py5.text_font(FONT_MONO)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text_size(11)
    callouts = [
        (anti_x, anti_y - 60.0, 260.0, "ANTISOLAR POINT (180.0 deg)", AUREOLE_GOLD),
        (anti_x, anti_y - 128.0, 236.0, "1ST-ORDER GLORY (177.2 deg)", FOGBOW_PEARL),
        (anti_x, anti_y - 220.0, 236.0, "2ND-ORDER GLORY (174.6 deg)", FOGBOW_PEARL),
        (anti_x, anti_y - 312.0, 236.0, "3RD-ORDER GLORY (171.8 deg)", FOGBOW_PEARL),
        (CX, CY - 552.0, 440.0, "PRIMARY NEBELBOGEN FOGBOW (141.2 deg // AIRY CAUSTIC)", AUREOLE_GOLD),
    ]
    for lx_c, ly_c, lw_c, l_str, l_col in callouts:
        py5.fill(*PANEL_DARK, 205)
        py5.stroke(*BORDER_BRONZE, 160)
        py5.stroke_weight(1.0)
        py5.rect(lx_c - lw_c * 0.5, ly_c - 11.0, lw_c, 22.0, 4)
        py5.fill(*l_col)
        py5.text(l_str, lx_c, ly_c)

    # Outer bezel ring stroke
    py5.no_fill()
    py5.stroke(*INK_CHARCOAL, 235)
    py5.stroke_weight(2.4)
    py5.circle(CX, CY, INNER_R * 2.0)

    # Bottom telemetry badge inside medallion (positioned well inside circle chord with generous padding)
    badge_w = 540.0
    badge_y = CY + INNER_R - 142.0
    py5.fill(*PANEL_DARK, 235)
    py5.stroke(*BRASS_BRIGHT, 210)
    py5.stroke_weight(1.5)
    py5.rect(CX - badge_w * 0.5, badge_y, badge_w, 44.0, 6)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.fill(*AUREOLE_GOLD)
    py5.text_size(12)
    py5.text(
        f"BROCKENGESPENST CONE  |  GLORY m=1..3  |  r_eff = {r_eff:04.2f} um  |  n = 1.333",
        CX,
        badge_y + 22.0,
    )


def draw_left_top_card(phi: float, r_eff: float):
    x, y, w, h = LEFT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 01",
        "VAN DE HULST & NUSSENZVEIG SURFACE-WAVE DROPLET RAY (p=2)",
        "FIG. 02",
        "MIE BACKSCATTER PHASE FUNCTION P11(theta) (170..180 DEG)",
    )

    # --- FIG. 01: Spherical Cloud Droplet Grazing Ray + 14.4 deg Surface Wave Retroreflection ---
    dx, dy, dw, dh = x + 36.0, y + 64.0, 520.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(dx, dy, dw, dh, 6)

    dcx = dx + dw * 0.52
    dcy = dy + dh * 0.50
    drop_r = 122.0

    # Water droplet sphere with subtle cerulean rim
    py5.fill(20, 48, 86, 220)
    py5.stroke(*GLORY_CERULEAN, 240)
    py5.stroke_weight(2.6)
    py5.circle(dcx, dcy, drop_r * 2.0)

    # Incident grazing solar ray at top of droplet (impact parameter b -> R_drop)
    in_y = dcy - drop_r
    py5.stroke(*BRASS_BRIGHT, 255)
    py5.stroke_weight(3.2)
    py5.line(dx + 24.0, in_y, dcx, in_y)

    # Critical refraction chord inside water sphere (2 * theta_c = 97.2 deg -> angle from top = 97.2 deg)
    # In screen coords: top is -pi/2; internal reflection point B is at -pi/2 + 1.696 rad (~ +7.2 deg below right equator)
    ang_top = -0.5 * np.pi
    ang_b = ang_top + np.deg2rad(97.2)
    bx_pt = dcx + drop_r * np.cos(ang_b)
    by_pt = dcy + drop_r * np.sin(ang_b)
    py5.stroke(*GLORY_EMERALD, 245)
    py5.stroke_weight(2.8)
    py5.line(dcx, in_y, bx_pt, by_pt)

    # Second internal chord from B across to C near bottom-left, plus 14.4 deg Regge-Debye surface-wave creep!
    ang_c = ang_b + np.deg2rad(97.2)
    cx_pt = dcx + drop_r * np.cos(ang_c)
    cy_pt = dcy + drop_r * np.sin(ang_c)
    py5.line(bx_pt, by_pt, cx_pt, cy_pt)

    # Surface wave creep arc from C (ang_c) to bottom exit point (+pi/2)
    creep_angs = np.linspace(ang_c, 0.5 * np.pi, 24, dtype=np.float32)
    creep_pts = np.column_stack((dcx + (drop_r + 4.0) * np.cos(creep_angs), dcy + (drop_r + 4.0) * np.sin(creep_angs)))
    py5.stroke(*GLORY_CRIMSON, 255)
    py5.stroke_weight(4.0)
    py5.lines(np.hstack((creep_pts[:-1], creep_pts[1:])))

    # Exiting retroreflected ray at bottom (theta_s = 180.0 deg back toward sun/observer!)
    out_y = dcy + drop_r
    py5.stroke(*GLORY_CRIMSON, 255)
    py5.stroke_weight(3.2)
    py5.line(dcx, out_y, dx + 24.0, out_y)

    # Animated wavefront bead traveling along the optical path
    py5.fill(*AUREOLE_GOLD)
    py5.no_stroke()
    py5.circle(bx_pt, by_pt, 10.0)
    py5.circle(cx_pt, cy_pt, 10.0)

    py5.text_font(FONT_MONO)
    py5.text_size(11)
    py5.fill(*BRASS_BRIGHT)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text("INCIDENT GRAZING RAY (b = R)", dx + 28.0, in_y - 6.0)
    py5.fill(*GLORY_CRIMSON)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("RETRO-RAY (theta = 180 deg)", dx + 28.0, out_y + 8.0)

    # Right explanatory column for FIG. 01
    rx = dx + dw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*INK_CHARCOAL)
    py5.text_size(15)
    py5.text("REGGE-DEBYE SURFACE WAVE", rx, dy + 6.0)
    specs_f1 = [
        ("REFRACTIVE IDX", "n = 1.333 (H2O)"),
        ("CRITICAL ANGLE", "theta_c = 48.6 deg"),
        ("CHORD DEFLECT", "2 * 48.6 = 97.2 deg"),
        ("AXIAL DEFICIT", "180 - 165.6 = 14.4 deg"),
        ("SURFACE CREEP", "Delta_theta = 14.4 deg"),
        ("TUNNELING MODE", "Debye p=2 Regge Pole"),
        ("INTERFERENCE", "Axial Focus Toroidal"),
        ("POLARIZATION", "Tangential vs Radial"),
        ("DROPLET DIAM", f"2*r = {2.0 * r_eff:04.1f} um"),
    ]
    for i, (k_s, v_s) in enumerate(specs_f1):
        yy = dy + 42.0 + i * 32.0
        py5.fill(*INK_MUTED)
        py5.text_size(13)
        py5.text(k_s, rx, yy)
        py5.fill(*(GLORY_CRIMSON if i in (4, 8) else INK_CHARCOAL))
        py5.text(v_s, rx + 166.0, yy)

    # --- FIG. 02: Multi-Wavelength Backscatter Phase Function P11(theta) ---
    mid_y = y + h * 0.5
    px, py, pw, ph = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(px, py, pw, ph, 6)

    left_p = px + 68.0
    base_p = py + ph - 52.0
    plot_w = pw - 96.0

    # Grid lines
    py5.stroke(36, 52, 82, 190)
    py5.stroke_weight(1.0)
    for frac in (0.2, 0.4, 0.6, 0.8):
        py5.line(left_p + plot_w * frac, py + 20.0, left_p + plot_w * frac, base_p)
    for dy_g in (60.0, 120.0, 180.0, 240.0):
        py5.line(left_p, base_p - dy_g, left_p + plot_w, base_p - dy_g)

    # Plot P11(theta) for Blue (450nm), Green (540nm), Red (650nm) across gamma = 180 - theta in [0..10 deg]
    u_ang = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_plot = left_p + u_ang * plot_w
    scale_d = r_eff / 12.4

    for w_scale, w_col in (
        (24.0 * scale_d, GLORY_CERULEAN),
        (20.2 * scale_d, GLORY_EMERALD),
        (16.8 * scale_d, GLORY_CRIMSON),
    ):
        arg = u_ang * w_scale
        # J0^2 + J2^2 Van de Hulst glory Bessel envelope approximation
        p11 = (np.cos(arg - 0.65) ** 2) * np.exp(-2.1 * u_ang) * 215.0 + 35.0 * np.exp(-16.0 * (u_ang**2))
        pts_p = np.column_stack((x_plot, base_p - p11))
        py5.stroke(*w_col, 240)
        py5.stroke_weight(2.6)
        py5.lines(np.hstack((pts_p[:-1], pts_p[1:])))

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*GLORY_CRIMSON)
    py5.text("LAMBDA = 650 nm (RED: OUTER RING MAXIMA)", left_p + plot_w - 14.0, py + 24.0)
    py5.fill(*GLORY_EMERALD)
    py5.text("LAMBDA = 540 nm (GREEN: MID RING MAXIMA)", left_p + plot_w - 14.0, py + 46.0)
    py5.fill(*GLORY_CERULEAN)
    py5.text("LAMBDA = 450 nm (BLUE: INNER RING MAXIMA)", left_p + plot_w - 14.0, py + 68.0)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(*AUREOLE_GOLD)
    for deg_i, deg_val in enumerate((180, 178, 176, 174, 172, 170)):
        xx = left_p + (deg_i / 5.0) * plot_w
        py5.text(f"{deg_val} deg", xx, base_p + 14.0)


def draw_left_bottom_card(phi: float, r_eff: float):
    x, y, w, h = LEFT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 03",
        "MONODISPERSE STRATUS DROPLET GAMMA DISTRIBUTION n(r)",
        "FIG. 04",
        "BROCKEN SPECTRE & NEBELBOGEN ARCHIVAL PALETTE",
    )

    # --- FIG. 03: Cloud Droplet Size Histogram n(r) ---
    hx, hy, hw, hh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(hx, hy, hw, hh, 6)

    left_h = hx + 68.0
    base_h = hy + hh - 52.0
    plot_w = hw - 104.0

    # Histogram bars for r in [4..24 um]
    n_bars = 20
    r_bins = np.linspace(4.0, 24.0, n_bars, dtype=np.float32)
    bar_w = plot_w / n_bars
    for b_i, r_b in enumerate(r_bins):
        # Narrow gamma distribution centered at live r_eff (effective variance v_eff = 0.04)
        prob = np.exp(-(((r_b - r_eff) / 2.35) ** 2))
        bh_px = prob * 232.0
        bx_i = left_h + b_i * bar_w
        is_peak = abs(r_b - r_eff) < 1.2
        py5.fill(*(GLORY_CRIMSON if is_peak else GLORY_CERULEAN), 195)
        py5.stroke(*(AUREOLE_GOLD if is_peak else GLORY_CERULEAN), 235)
        py5.stroke_weight(1.4)
        py5.rect(bx_i + 4.0, base_h - bh_px, bar_w - 8.0, bh_px, 3)

    # Smooth analytical Gamma envelope curve over the bars
    r_cont = np.linspace(4.0, 24.0, 180, dtype=np.float32)
    x_cont = left_h + ((r_cont - 4.0) / 20.0) * plot_w
    y_cont = base_h - 238.0 * np.exp(-(((r_cont - r_eff) / 2.35) ** 2))
    pts_g = np.column_stack((x_cont, y_cont))
    py5.stroke(*AUREOLE_GOLD, 250)
    py5.stroke_weight(2.8)
    py5.lines(np.hstack((pts_g[:-1], pts_g[1:])))

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*AUREOLE_GOLD)
    py5.text(f"MODIFIED GAMMA DROPLET SPECTRUM: r_eff = {r_eff:04.2f} um  |  v_eff = 0.042 (MONODISPERSE STRATUS)", left_h + 12.0, hy + 22.0)
    py5.fill(*GLORY_EMERALD)
    py5.text("C. T. R. WILSON CONDITION: v_eff < 0.08 REQUIRED FOR > 3 DISTINCT GLORY RINGS", left_h + 12.0, hy + 44.0)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(*FOGBOW_PEARL)
    for r_lbl in (4, 8, 12, 16, 20, 24):
        xx = left_h + ((r_lbl - 4.0) / 20.0) * plot_w
        py5.text(f"r={r_lbl}um", xx, base_h + 14.0)

    # --- FIG. 04: 6 Chromatic Swatches ---
    mid_y = y + h * 0.5
    swatches = [
        (AUREOLE_GOLD, "0TH-ORDER AUREOLE GOLD", "#FFEC9C // ANTISOLAR CORE"),
        (GLORY_CRIMSON, "1ST-ORDER GLORY CRIMSON", "#E4346C // OUTER DIFFRACTION"),
        (GLORY_EMERALD, "2ND-ORDER GLORY EMERALD", "#16C694 // 540 nm MAXIMA"),
        (GLORY_CERULEAN, "SURFACE-WAVE CERULEAN", "#26A8F6 // DEBYE p=2 CREEP"),
        (GLORY_VIOLET, "INNER RING HELIOTROPE", "#8E4EEE // 430 nm VIOLET"),
        (STRATUS_INDIGO, "STRATUS NEBULOSUS SEA", "#162644 // CLOUD ABYSS"),
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


def draw_right_top_card(phi: float, r_eff: float):
    x, y, w, h = RIGHT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 05",
        "DESCARTES RAINBOW (500 um) VS. AIRY NEBELBOGEN FOGBOW (12 um)",
        "FIG. 06",
        "HISTORICAL GLORY, FOGBOW & CLOUD CHAMBER LEDGER (1735-1969)",
    )

    # --- FIG. 05: Rainbow vs. White Fogbow Airy Caustic Overlap ---
    fx, fy, fw, fh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(fx, fy, fw, fh, 6)

    left_f = fx + 68.0
    base_f = fy + fh - 52.0
    plot_w = fw - 104.0

    u_f = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_f = left_f + u_f * plot_w

    # Narrow Descartes raindrop caustic peaks (R, G, B well-separated at 42.3, 41.4, 40.6 deg)
    rain_r = 210.0 * np.exp(-(((u_f - 0.30) / 0.025) ** 2))
    rain_g = 210.0 * np.exp(-(((u_f - 0.37) / 0.025) ** 2))
    rain_b = 210.0 * np.exp(-(((u_f - 0.44) / 0.025) ** 2))

    # Broad Airy fogbow caustic for 12 um droplets (R, G, B overlap into white alabaster dome + supernumeraries!)
    fog_env = (
        185.0 * np.exp(-(((u_f - 0.52) / 0.14) ** 2))
        + 48.0 * np.exp(-(((u_f - 0.76) / 0.09) ** 2)) * (0.5 + 0.5 * np.cos((u_f - 0.65) * 58.0 - phi))
    )

    for r_curve, r_col in ((rain_r, GLORY_CRIMSON), (rain_g, GLORY_EMERALD), (rain_b, GLORY_CERULEAN)):
        pts_r = np.column_stack((x_f, base_f - r_curve))
        py5.stroke(*r_col, 175)
        py5.stroke_weight(2.0)
        py5.lines(np.hstack((pts_r[:-1], pts_r[1:])))

    pts_fog = np.column_stack((x_f, base_f - fog_env))
    py5.stroke(*FOGBOW_PEARL, 255)
    py5.stroke_weight(3.4)
    py5.lines(np.hstack((pts_fog[:-1], pts_fog[1:])))

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*FOGBOW_PEARL)
    py5.text("WHITE NEBELBOGEN FOGBOW (r = 12.4 um): AIRY DIFFRACTION OVERLAPS RGB CAUSTICS", left_f + 16.0, fy + 24.0)
    py5.fill(*GLORY_CORAL)
    py5.text("DESCARTES RAINBOW (r = 500 um): SEPARATED RGB PEAKS AT 40.6..42.3 DEG", left_f + 16.0, fy + 46.0)

    py5.text_align(py5.CENTER, py5.TOP)
    py5.fill(*AUREOLE_GOLD)
    for idx_a, ang_lbl in enumerate(("135 deg", "138 deg", "141 deg (FOGBOW)", "144 deg (SUPERNUM.)", "147 deg")):
        xx = left_f + (idx_a / 4.0) * plot_w
        py5.text(ang_lbl, xx, base_f + 14.0)

    # --- FIG. 06: Historical Archival Ledger ---
    mid_y = y + h * 0.5
    tx, ty, tw, th = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PANEL_MIST)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(tx, ty, tw, th, 6)

    headers = ["YEAR", "INVESTIGATOR / SITE", "PHENOMENON & INSTRUMENT", "THEORETICAL MODEL"]
    col_xs = [tx + 20, tx + 96, tx + 395, tx + 695]
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
        ("1735", "Bouguer & Ulloa (Pambamarca)", "Andean Antisolar Glory Rings", "First Scientific Record"),
        ("1780", "J. Silberschlag (Harz Brocken)", "Brockengespenst & Nebelbogen", "Perspective Shadow Cone"),
        ("1838", "G. B. Airy (Cambridge)", "Rainbow Supernumerary Caustic", "Airy Integral Ai(-z)"),
        ("1895", "C. T. R. Wilson (Ben Nevis)", "Summit Glory -> Cloud Chamber", "Adiabatic Nucleation"),
        ("1947", "H. C. van de Hulst (Utrecht)", "Grazing 14.4 deg Surface Wave", "Toroidal Wavefront Focus"),
        ("1969", "H. M. Nussenzveig (Rochester)", "Complex Angular Momentum", "Debye / Regge Pole Sum"),
    ]
    for r_i, r_vals in enumerate(rows):
        ry_row = ty + 52.0 + r_i * 47.0
        if r_i % 2 == 1:
            py5.fill(*CARD_HEADER_BG, 145)
            py5.no_stroke()
            py5.rect(tx + 8, ry_row - 8, tw - 16, 40, 3)
        for c_i, (cx_c, val_str) in enumerate(zip(col_xs, r_vals)):
            py5.fill(*(GLORY_CRIMSON if c_i == 0 else (INK_CHARCOAL if c_i == 1 else INK_SLATE)))
            py5.text_size(12)
            py5.text(val_str, cx_c, ry_row + 12)


def draw_right_bottom_card(phi: float, r_eff: float, sun_elev: float):
    x, y, w, h = RIGHT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 07",
        "SUMMIT ANTISOLAR ELEVATION & INVERSION CLOUD DECK GEOMETRY",
        "FIG. 08",
        "MULTI-WAVELENGTH REGGE-POLE INTERFERENCE OSCILLOGRAM",
    )

    # --- FIG. 07: Summit Crag Elevation Cross-Section & Antisolar Sightline ---
    gx, gy, gw, gh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(gx, gy, gw, gh, 6)

    # Stratus inversion cloud sea in right half of cross-section
    cloud_y = gy + 178.0
    py5.fill(32, 54, 92, 185)
    py5.no_stroke()
    py5.rect(gx + 260.0, cloud_y, gw - 276.0, gh - 194.0, 4)
    py5.stroke(*FOGBOW_PEARL, 210)
    py5.stroke_weight(2.2)
    py5.line(gx + 260.0, cloud_y, gx + gw - 16.0, cloud_y)

    # Basalt summit crag on left (Brocken peak, z = 1141 m)
    py5.fill(46, 52, 68)
    py5.stroke(*BRASS_GOLD, 200)
    py5.stroke_weight(2.0)
    with py5.begin_shape(py5.POLYGON):
        py5.vertex(gx + 16.0, gy + gh - 16.0)
        py5.vertex(gx + 16.0, gy + 148.0)
        py5.vertex(gx + 195.0, gy + 118.0)
        py5.vertex(gx + 265.0, gy + 188.0)
        py5.vertex(gx + 340.0, gy + gh - 16.0)

    # Observer figure standing on summit crag at (gx + 205, gy + 92..118)
    obs_x, obs_y = gx + 205.0, gy + 88.0
    py5.fill(*AUREOLE_GOLD)
    py5.no_stroke()
    py5.circle(obs_x, obs_y, 12.0)
    py5.stroke(*AUREOLE_GOLD)
    py5.stroke_weight(3.0)
    py5.line(obs_x, obs_y + 6.0, obs_x, obs_y + 30.0)

    # Incident grazing solar rays from upper left through observer into the stratus deck
    anti_target_x = gx + 665.0
    anti_target_y = cloud_y + 42.0
    py5.stroke(*BRASS_BRIGHT, 235)
    py5.stroke_weight(2.4)
    py5.line(gx + 28.0, gy + 44.0, anti_target_x, anti_target_y)

    # Glory backscatter cone returning from (anti_target_x, anti_target_y) to observer's eye!
    py5.stroke(*GLORY_CRIMSON, 225)
    py5.stroke_weight(1.8)
    py5.line(anti_target_x, anti_target_y, obs_x, obs_y - 16.0)
    py5.stroke(*GLORY_EMERALD, 225)
    py5.line(anti_target_x, anti_target_y, obs_x, obs_y + 18.0)

    # Glowing glory node inside cloud layer
    py5.fill(*GLORY_CRIMSON)
    py5.stroke(*AUREOLE_GOLD)
    py5.stroke_weight(2.0)
    py5.circle(anti_target_x, anti_target_y, 24.0)

    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*AUREOLE_GOLD)
    py5.text(f"LOW GRAZING SUN (alpha = +{sun_elev:04.2f} deg)", gx + 36.0, gy + 18.0)
    py5.fill(*FOGBOW_PEARL)
    py5.text("STRATUS INVERSION TOP (z_inv = 980 m // T = +2.4 C, RH = 100%)", gx + 345.0, cloud_y - 24.0)
    py5.fill(*GLORY_CRIMSON)
    py5.text("ANTISOLAR GLORY LOCUS (180 deg RETRO-CONE)", gx + 515.0, anti_target_y + 22.0)

    # --- FIG. 08: Multi-Order Glory Interference Oscillogram ---
    mid_y = y + h * 0.5
    ox, oy, ow, oh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*PANEL_DARK)
    py5.stroke(*BORDER_BRONZE, 210)
    py5.stroke_weight(1.5)
    py5.rect(ox, oy, ow, oh, 6)

    osc_cy = oy + oh * 0.48
    py5.stroke(36, 52, 82, 190)
    py5.stroke_weight(1.0)
    py5.line(ox + 24.0, osc_cy, ox + ow - 24.0, osc_cy)

    u_o = np.linspace(0.0, 1.0, 240, dtype=np.float32)
    x_o = ox + 24.0 + u_o * (ow - 48.0)
    env_o = np.exp(-1.8 * ((u_o - 0.5) ** 2))

    w_red = 92.0 * env_o * np.cos(10.0 * np.pi * (u_o - 0.5) - phi)
    w_grn = 84.0 * env_o * np.cos(12.2 * np.pi * (u_o - 0.5) - phi)
    w_blu = 76.0 * env_o * np.cos(14.6 * np.pi * (u_o - 0.5) - phi)

    for w_arr, w_col in ((w_red, GLORY_CRIMSON), (w_grn, GLORY_EMERALD), (w_blu, GLORY_CERULEAN)):
        pts_o = np.column_stack((x_o, osc_cy - w_arr))
        py5.stroke(*w_col, 235)
        py5.stroke_weight(2.4)
        py5.lines(np.hstack((pts_o[:-1], pts_o[1:])))

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*AUREOLE_GOLD)
    py5.text_size(12)
    py5.text(
        f"REGGE-POLE AMPLITUDE S_l(x)  |  x_650 = {2*np.pi*r_eff/0.650:05.1f}  |  "
        f"x_540 = {2*np.pi*r_eff/0.540:05.1f}  |  x_450 = {2*np.pi*r_eff/0.450:05.1f}",
        ox + 26.0,
        oy + oh - 14.0,
    )


def draw():
    frame_idx = py5.frame_count - 1
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phi = 2.0 * np.pi * t_norm + (SEED_OFFSET % 100) * 0.01

    py5.background(*BG_VELLUM)

    # Harmonic modulation of stratus cloud droplet radius r_eff(t) and solar azimuth
    r_eff = 12.4 + 1.35 * np.sin(2.0 * np.pi * t_norm)
    sun_elev = 6.4 + 0.85 * np.cos(2.0 * np.pi * t_norm)
    sun_az_shift = 22.0 * np.sin(2.0 * np.pi * t_norm)

    draw_frame_border_and_header(phi, r_eff, sun_elev)
    draw_central_glory_and_spectre_medallion(phi, r_eff, sun_az_shift)
    draw_left_top_card(phi, r_eff)
    draw_left_bottom_card(phi, r_eff)
    draw_right_top_card(phi, r_eff)
    draw_right_bottom_card(phi, r_eff, sun_elev)

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

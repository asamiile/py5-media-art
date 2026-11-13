"""
kinetic_vauban_bastioned_trace_italienne_polygonal_citadel_2d

Sebastien Le Prestre de Vauban's Troisieme Systeme (Neuf-Brisach Octagonal Star
Citadel, 1698-1706), Menno van Coehoorn's Dutch Water-Defense Geometry (1685),
and Renaissance Trace Italienne Defilade & Crossfire Ballistic Stereotomy,
inspired by Allain Manesson Mallet's Les Travaux de Mars (1671), Simon Stevin's
Sterctenbouwing (1594), and the 1:600 scale Plans-Reliefs collection.
"""

from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
import py5

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------
WORK_NAME = "kinetic_vauban_bastioned_trace_italienne_polygonal_citadel_2d"
SIZE = (3840, 2160)
WIDTH, HEIGHT = SIZE
TOTAL_FRAMES = 720
FPS = 60

SKETCH_DIR = Path(__file__).resolve().parent
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_PATH = SKETCH_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_MP4 = SKETCH_DIR / "output.mp4"

# Layout Geometry (4K 3840x2160)
CX, CY = 1920.0, 1110.0
R_MEDALLION = 805.0
R_RING_OUTER = 842.0

LEFT_X, CARD_W = 104.0, 860.0
RIGHT_X = 3840.0 - 104.0 - 860.0
CARD_Y_TOP = 180.0
CARD_H_TOP = 885.0
CARD_Y_BOT = 1105.0
CARD_H_BOT = 885.0

# ---------------------------------------------------------------------------
# Color Palette — Royal Corps of Engineers Vellum (Light BG) & Vauban Citadel
# ---------------------------------------------------------------------------
BG_VELLUM = (245, 241, 230)       # #f5f1e6 Warm Genie Militaire Cartographic Vellum
CARD_BG = (252, 249, 241, 238)    # Translucent Treatise Plate Paper
CARD_BORDER = (184, 166, 136)     # Sepia & Brass Caliper Rule
TEXT_PRIMARY = (24, 30, 44)       # Deep Iron-Gall Drafting Ink
TEXT_SECONDARY = (92, 84, 72)     # Muted Sepia Specification Ink
TEXT_ACCENT = (182, 54, 36)       # Vauban Vosges Sandstone Vermilion

MOAT_DEEP = (13, 27, 46)          # #0d1b2e Flooded Grand Fosse & Counterscarp Basin
MOAT_CERULEAN = (28, 72, 122)     # Flooded Ditch Water Channel
GLACIS_TURF_DARK = (24, 108, 82)  # Outer Glacis Earthwork Slope Base
GLACIS_TURF_LIGHT = (56, 164, 124)# Crown of Covered Way (Chemin Couvert) Turf
VOSGES_SANDSTONE = (206, 82, 56)  # Alsace Pink-Terracotta Brick & Sandstone Scarp
VOSGES_HIGH = (238, 128, 94)      # Sunlit Rampart Parapet Crest
ASHLAR_LIMESTONE = (232, 206, 152)# Dressed Limestone Cordon & Casemate Vault
ASHLAR_SHADOW = (176, 146, 96)    # Terre-Plein & Talus Slope
BALLISTIC_GOLD = (248, 198, 68)   # Enfilading Crossfire Line of Defense

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

N_SIDES = 8  # Octagonal Neuf-Brisach Star Citadel
GRID_LINES = None
TOWN_BLOCKS = None


def polar_pt(r, theta):
    return np.array([CX + r * np.cos(theta), CY + r * np.sin(theta)], dtype=np.float32)


def make_beveled_star_layer(r_nodes_angles, r_scale_in, col_slope, col_crest):
    """
    Given a closed polygon ring of (r, theta) vertices around the 8-fold star,
    generate outer-to-inner beveled embankment quads and top crest polygon quads.
    """
    n_v = len(r_nodes_angles)
    pts_out = np.array([polar_pt(r, th) for r, th in r_nodes_angles], dtype=np.float32)
    pts_in = np.array([polar_pt(r * r_scale_in, th) for r, th in r_nodes_angles], dtype=np.float32)

    slope_quads = []
    for i in range(n_v):
        j = (i + 1) % n_v
        slope_quads.append([pts_out[i], pts_out[j], pts_in[j], pts_in[i]])
    return np.array(slope_quads, dtype=np.float32), pts_out, pts_in


def init_citadel_geometry():
    """Precompute background drafting grid and Neuf-Brisach orthogonal town blocks."""
    global GRID_LINES, TOWN_BLOCKS

    g_segs = []
    for x in range(80, WIDTH - 80, 60):
        g_segs.append([float(x), 55.0, float(x), float(HEIGHT - 55)])
    for y in range(60, HEIGHT - 60, 60):
        g_segs.append([80.0, float(y), float(WIDTH - 80), float(y)])
    GRID_LINES = np.array(g_segs, dtype=np.float32)

    # Precompute 8x8 Orthogonal Castrametation Town Grid inside R_town = 235 px
    # Leaving the central 2x2 blocks open as the monumental Place d'Armes!
    blocks = []
    grid_span = 215.0
    step = (grid_span * 2.0) / 8.0
    pad = 5.5
    r_max_town = 222.0

    for gx in range(8):
        for gy in range(8):
            # Central 2x2 is the grand Place d'Armes
            if gx in (3, 4) and gy in (3, 4):
                continue
            bx0 = CX - grid_span + gx * step + pad
            bx1 = CX - grid_span + (gx + 1) * step - pad
            by0 = CY - grid_span + gy * step + pad
            by1 = CY - grid_span + (gy + 1) * step - pad

            # Check all 4 corners lie inside octagonal town enceinte (r < r_max_town)
            corners = np.array([[bx0, by0], [bx1, by0], [bx1, by1], [bx0, by1]], dtype=np.float32)
            dists = np.hypot(corners[:, 0] - CX, corners[:, 1] - CY)
            if np.all(dists < r_max_town):
                is_command = (gx in (2, 5) and gy in (3, 4)) or (gy in (2, 5) and gx in (3, 4))
                blocks.append({
                    "corners": corners,
                    "cx": 0.5 * (bx0 + bx1),
                    "cy": 0.5 * (by0 + by1),
                    "w": bx1 - bx0,
                    "h": by1 - by0,
                    "is_command": is_command,
                })
    TOWN_BLOCKS = blocks


def settings():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.pixel_density(1)
    py5.smooth(4)


def setup():
    global FONT_MAIN, START_TIME, PHASE_OFFSET
    START_TIME = time.time()
    seed_val = int(START_TIME * 1000) % 100000
    np.random.seed(seed_val)
    PHASE_OFFSET = (seed_val % 1000) / 1000.0 * 2.0 * np.pi

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    FONT_MAIN = py5.create_font("Helvetica", 16)
    py5.text_font(FONT_MAIN)

    init_citadel_geometry()
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


# ---------------------------------------------------------------------------
# Main Medallion: Vauban Octagonal Star Citadel (Neuf-Brisach Master Plan)
# ---------------------------------------------------------------------------
def draw_vauban_citadel_medallion(tau):
    r_inner = R_MEDALLION - 14.0
    d_theta = (2.0 * np.pi) / N_SIDES  # 45 deg per octagonal sector

    # Slow harmonic rotation of ballistic illumination & water ripples (citadel stays aligned to cardinal gates)
    sun_angle = tau + PHASE_OFFSET
    sx_dir, sy_dir = np.cos(sun_angle), np.sin(sun_angle)

    # 1. Outer Brass Goniometer Ring & Flooded Moat Basin
    py5.no_stroke()
    py5.fill(198, 152, 64)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    py5.fill(*MOAT_DEEP)
    py5.circle(CX, CY, R_MEDALLION * 2.0)

    # Concentric ballistic range rings in the flooded basin (100, 150, 200, 250, 300 Toises)
    py5.no_fill()
    py5.stroke(28, 64, 112, 130)
    py5.stroke_weight(1.2)
    for r_rng in [320.0, 440.0, 560.0, 675.0, 765.0]:
        py5.circle(CX, CY, r_rng * 2.0)

    # -----------------------------------------------------------------------
    # LAYER 1: Outer Sloping Turf Glacis & Covered Way (Chemin Couvert, R = 520..760 px)
    # 16-pointed star alternating between Bastion Salients (k*45 deg) and Ravelin Salients ((k+0.5)*45 deg)
    # -----------------------------------------------------------------------
    glacis_outer_nodes = []
    glacis_inner_nodes = []
    for k in range(N_SIDES):
        th_b = k * d_theta
        th_r = (k + 0.5) * d_theta
        th_re1 = (k + 0.23) * d_theta
        th_re2 = (k + 0.77) * d_theta

        # Outer foot of Glacis (Crête Militaire -> Queue du Glacis)
        glacis_outer_nodes.extend([
            (728.0, th_b),
            (618.0, th_re1),
            (758.0, th_r),
            (618.0, th_re2),
        ])
        # Inner Crest of Glacis / Counterscarp wall of Moat
        glacis_inner_nodes.extend([
            (598.0, th_b),
            (492.0, th_re1),
            (628.0, th_r),
            (492.0, th_re2),
        ])

    n_gl = len(glacis_outer_nodes)
    pts_gl_out = np.array([polar_pt(r, th) for r, th in glacis_outer_nodes], dtype=np.float32)
    pts_gl_in = np.array([polar_pt(r, th) for r, th in glacis_inner_nodes], dtype=np.float32)

    # Render beveled Glacis turf facets with directional solar shading + hachure slope lines
    hachure_segs = []
    py5.no_stroke()
    for i in range(n_gl):
        j = (i + 1) % n_gl
        p0, p1 = pts_gl_out[i], pts_gl_out[j]
        p2, p3 = pts_gl_in[j], pts_gl_in[i]

        # Outward facet normal for Lambertian relief shading
        dx_f = p1[0] - p0[0]
        dy_f = p1[1] - p0[1]
        fn_len = max(np.hypot(dx_f, dy_f), 1e-4)
        nx, ny = dy_f / fn_len, -dx_f / fn_len
        dot_sun = 0.5 + 0.5 * (nx * sx_dir + ny * sy_dir)

        rc = int(GLACIS_TURF_DARK[0] * (1.0 - dot_sun) + GLACIS_TURF_LIGHT[0] * dot_sun)
        gc = int(GLACIS_TURF_DARK[1] * (1.0 - dot_sun) + GLACIS_TURF_LIGHT[1] * dot_sun)
        bc = int(GLACIS_TURF_DARK[2] * (1.0 - dot_sun) + GLACIS_TURF_LIGHT[2] * dot_sun)
        py5.fill(rc, gc, bc)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array([p0, p1, p2, p3], dtype=np.float32))
        py5.end_shape()

        # Topographical hachure lines perpendicular to slope
        for h_k in range(1, 7):
            u = h_k / 7.0
            ha = (1.0 - u) * p3 + u * p2
            hb = (1.0 - u) * p0 + u * p1
            hachure_segs.append([ha[0], ha[1], hb[0], hb[1]])

    if hachure_segs:
        py5.stroke(14, 58, 46, 145)
        py5.stroke_weight(1.1)
        py5.lines(np.array(hachure_segs, dtype=np.float32))

    # Covered Way (Chemin Couvert) limestone banquette rim at pts_gl_in
    banquette_segs = []
    for i in range(n_gl):
        j = (i + 1) % n_gl
        banquette_segs.append([pts_gl_in[i, 0], pts_gl_in[i, 1], pts_gl_in[j, 0], pts_gl_in[j, 1]])
    py5.stroke(*ASHLAR_LIMESTONE)
    py5.stroke_weight(2.4)
    py5.lines(np.array(banquette_segs, dtype=np.float32))

    # 8 Re-entrant Places of Arms (Places d'Armes Rentrantes) diamond redoubts
    reentrant_quads_wall = []
    reentrant_quads_roof = []
    for k in range(N_SIDES):
        for offset in [0.23, 0.77]:
            th_re = (k + offset) * d_theta
            c_re = polar_pt(528.0, th_re)
            u_rad = np.array([np.cos(th_re), np.sin(th_re)], dtype=np.float32)
            u_tan = np.array([-np.sin(th_re), np.cos(th_re)], dtype=np.float32)
            d1 = c_re + u_rad * 32.0
            d2 = c_re + u_tan * 22.0
            d3 = c_re - u_rad * 22.0
            d4 = c_re - u_tan * 22.0
            reentrant_quads_wall.append([d1, d2, d3, d4])
            reentrant_quads_roof.append([
                c_re + u_rad * 18.0, c_re + u_tan * 12.0,
                c_re - u_rad * 12.0, c_re - u_tan * 12.0,
            ])

    py5.no_stroke()
    py5.fill(*ASHLAR_LIMESTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(reentrant_quads_wall, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()
    py5.fill(*VOSGES_SANDSTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(reentrant_quads_roof, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    # -----------------------------------------------------------------------
    # LAYER 2: Flooded Grand Moat (Grand Fosse) & 8 Demi-Lunes / Ravelins + Redoubts
    # -----------------------------------------------------------------------
    # Carve the flooded moat polygon inside pts_gl_in
    py5.fill(*MOAT_CERULEAN)
    py5.begin_shape()
    for pt in pts_gl_in:
        py5.vertex(pt[0], pt[1])
    py5.end_shape(py5.CLOSE)

    # Animated water contour ripples inside the moat
    moat_ripple_segs = []
    center_xy = np.array([CX, CY], dtype=np.float32)
    for r_scale in [0.96, 0.92]:
        rip_scale = r_scale + 0.008 * np.sin(tau * 2.0 + r_scale * 20.0)
        pts_rip = center_xy + (pts_gl_in - center_xy) * rip_scale
        for i in range(n_gl):
            j = (i + 1) % n_gl
            moat_ripple_segs.append([pts_rip[i, 0], pts_rip[i, 1], pts_rip[j, 0], pts_rip[j, 1]])
    py5.stroke(86, 168, 234, 95)
    py5.stroke_weight(1.2)
    py5.lines(np.array(moat_ripple_segs, dtype=np.float32))

    # 8 Triangular Demi-Lunes (Ravelins) with Nested Inner Redoubts (Reduits de Demi-Lune)
    ravelin_scarp_quads = []
    ravelin_turf_quads = []
    ravelin_redoubt_quads = []
    tenaille_quads = []

    for k in range(N_SIDES):
        th_r = (k + 0.5) * d_theta
        th_L = th_r - 0.145 * d_theta
        th_R = th_r + 0.145 * d_theta

        # Outer Ravelin masonry scarp vertices (Salient point, Left shoulder, Gorge center, Right shoulder)
        v_sal = polar_pt(576.0, th_r)
        v_shL = polar_pt(418.0, th_L)
        v_gor = polar_pt(442.0, th_r)
        v_shR = polar_pt(418.0, th_R)
        ravelin_scarp_quads.append([v_sal, v_shR, v_gor, v_shL])

        # Inner Ravelin turf parapet
        t_sal = polar_pt(542.0, th_r)
        t_shL = polar_pt(428.0, th_r - 0.115 * d_theta)
        t_gor = polar_pt(456.0, th_r)
        t_shR = polar_pt(428.0, th_r + 0.115 * d_theta)
        ravelin_turf_quads.append([t_sal, t_shR, t_gor, t_shL])

        # Nested Reduit de Demi-Lune (Inner stone redoubt)
        rd_sal = polar_pt(495.0, th_r)
        rd_shL = polar_pt(422.0, th_r - 0.068 * d_theta)
        rd_gor = polar_pt(434.0, th_r)
        rd_shR = polar_pt(422.0, th_r + 0.068 * d_theta)
        ravelin_redoubt_quads.append([rd_sal, rd_shR, rd_gor, rd_shL])

        # Curtain Tenaille (V-shaped low shield wall in the moat behind the ravelin)
        tn_L = polar_pt(374.0, th_r - 0.155 * d_theta)
        tn_C = polar_pt(352.0, th_r)
        tn_R = polar_pt(374.0, th_r + 0.155 * d_theta)
        tn_inL = polar_pt(354.0, th_r - 0.150 * d_theta)
        tn_inC = polar_pt(334.0, th_r)
        tn_inR = polar_pt(354.0, th_r + 0.150 * d_theta)
        tenaille_quads.append([tn_L, tn_C, tn_inC, tn_inL])
        tenaille_quads.append([tn_C, tn_R, tn_inR, tn_inC])

    py5.no_stroke()
    py5.fill(*VOSGES_SANDSTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(ravelin_scarp_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.fill(*GLACIS_TURF_LIGHT)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(ravelin_turf_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.fill(*ASHLAR_LIMESTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(ravelin_redoubt_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.fill(*VOSGES_HIGH)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(tenaille_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    # -----------------------------------------------------------------------
    # LAYER 3: 8 Detached Bastion Counterguards (Contre-Gardes) & Enceinte Ramparts
    # -----------------------------------------------------------------------
    # Build the 8-pointed Bastioned Enceinte Star Polygon:
    # Each sector k has:
    # - Salient Point of Bastion (k * d_theta, R = 528 px)
    # - Right Shoulder of Bastion ((k + 0.13) * d_theta, R = 415 px)
    # - Right Curtain-Flank Junction ((k + 0.17) * d_theta, R = 328 px)
    # - Mid-Curtain Gate ((k + 0.50) * d_theta, R = 318 px)
    # - Next Left Curtain-Flank Junction ((k + 0.83) * d_theta, R = 328 px)
    # - Next Left Shoulder of Bastion ((k + 0.87) * d_theta, R = 415 px)
    enceinte_nodes = []
    for k in range(N_SIDES):
        enceinte_nodes.extend([
            (526.0, (k + 0.00) * d_theta),   # Bastion Salient Apex
            (416.0, (k + 0.135) * d_theta),  # Bastion Right Shoulder (Epaule)
            (326.0, (k + 0.175) * d_theta),  # Curtain-Flank Angle (Angle de Flanc)
            (316.0, (k + 0.500) * d_theta),  # Curtain Center (Courtine)
            (326.0, (k + 0.825) * d_theta),  # Next Curtain-Flank Angle
            (416.0, (k + 0.865) * d_theta),  # Next Bastion Left Shoulder
        ])

    slope_scarp, pts_scarp_out, pts_scarp_in = make_beveled_star_layer(
        enceinte_nodes, 0.90, VOSGES_SANDSTONE, VOSGES_HIGH
    )
    slope_parapet, _, pts_parapet_in = make_beveled_star_layer(
        [(r * 0.90, th) for r, th in enceinte_nodes], 0.89, GLACIS_TURF_LIGHT, ASHLAR_LIMESTONE
    )
    slope_terreplein, _, pts_town_wall = make_beveled_star_layer(
        [(r * 0.80, th) for r, th in enceinte_nodes], 0.86, ASHLAR_LIMESTONE, ASHLAR_SHADOW
    )

    # Render Outer Masonry Scarp & Counterguard Band (Vosges Pink-Terracotta Sandstone)
    py5.fill(*VOSGES_SANDSTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(slope_scarp.reshape(-1, 2))
    py5.end_shape()

    # Render Turf Parapet Band
    py5.fill(*GLACIS_TURF_LIGHT)
    py5.begin_shape(py5.QUADS)
    py5.vertices(slope_parapet.reshape(-1, 2))
    py5.end_shape()

    # Render Ashlar Limestone Terre-Plein & Casemate Band
    py5.fill(*ASHLAR_LIMESTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(slope_terreplein.reshape(-1, 2))
    py5.end_shape()

    # Crisp masonry cordon outlines around the star layers
    cordon_segs = []
    for ring_pts in [pts_scarp_out, pts_scarp_in, pts_parapet_in, pts_town_wall]:
        n_p = len(ring_pts)
        for i in range(n_p):
            j = (i + 1) % n_p
            cordon_segs.append([ring_pts[i, 0], ring_pts[i, 1], ring_pts[j, 0], ring_pts[j, 1]])
    py5.stroke(34, 24, 22, 185)
    py5.stroke_weight(1.4)
    py5.lines(np.array(cordon_segs, dtype=np.float32))

    # 8 Vauban Bastioned Towers (Tours Bastionnees) at the inner gorges of the 8 bastions (R = 292 px)
    py5.stroke(42, 28, 22)
    py5.stroke_weight(1.8)
    for k in range(N_SIDES):
        th_b = k * d_theta
        pt_t = polar_pt(296.0, th_b)
        py5.fill(*VOSGES_HIGH)
        py5.circle(pt_t[0], pt_t[1], 32.0)
        py5.fill(*ASHLAR_LIMESTONE)
        py5.circle(pt_t[0], pt_t[1], 16.0)

    # -----------------------------------------------------------------------
    # LAYER 4: Inner Fortified Town of Neuf-Brisach, Castrametation Grid & Place d'Armes
    # -----------------------------------------------------------------------
    py5.no_stroke()
    py5.fill(18, 28, 46)
    py5.begin_shape()
    for pt in pts_town_wall:
        py5.vertex(pt[0], pt[1])
    py5.end_shape(py5.CLOSE)

    # Orthogonal Street Grid & Cross-Axial Royal Boulevards to the 4 Gates
    street_segs = []
    grid_span = 215.0
    step = (grid_span * 2.0) / 8.0
    for idx in range(9):
        off = -grid_span + idx * step
        max_ext = np.sqrt(max(0.0, 232.0 ** 2 - off ** 2))
        street_segs.append([CX + off, CY - max_ext, CX + off, CY + max_ext])
        street_segs.append([CX - max_ext, CY + off, CX + max_ext, CY + off])
    py5.stroke(78, 96, 128, 130)
    py5.stroke_weight(1.2)
    py5.lines(np.array(street_segs, dtype=np.float32))

    # Central Monumental Place d'Armes (2x2 Block Square) with Geometric Parterre & Wellhead
    pa_w = step * 2.0 - 8.0
    py5.stroke(*FIL_DOR_COLOR if False else (238, 194, 96))
    py5.stroke_weight(2.0)
    py5.fill(32, 48, 76)
    py5.rect(CX - pa_w * 0.5, CY - pa_w * 0.5, pa_w, pa_w, 3)
    py5.line(CX - pa_w * 0.5, CY - pa_w * 0.5, CX + pa_w * 0.5, CY + pa_w * 0.5)
    py5.line(CX - pa_w * 0.5, CY + pa_w * 0.5, CX + pa_w * 0.5, CY - pa_w * 0.5)
    py5.fill(*VOSGES_HIGH)
    py5.circle(CX, CY, 24.0)
    py5.fill(*ASHLAR_LIMESTONE)
    py5.circle(CX, CY, 10.0)

    # Render all 44 Hip-Roofed Garrison, Arsenal, Church & Command Blocks (Plans-Reliefs style!)
    roof_outer_quads = []
    roof_courtyard_quads = []
    command_quads = []

    for blk in TOWN_BLOCKS:
        c_out = blk["corners"]
        cx_b, cy_b = blk["cx"], blk["cy"]
        # Inner courtyard inset
        c_in = np.array([
            [cx_b + (pt[0] - cx_b) * 0.48, cy_b + (pt[1] - cy_b) * 0.48]
            for pt in c_out
        ], dtype=np.float32)
        if blk["is_command"]:
            command_quads.append(c_out)
        else:
            roof_outer_quads.append(c_out)
        roof_courtyard_quads.append(c_in)

    py5.no_stroke()
    py5.fill(*VOSGES_SANDSTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(roof_outer_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.fill(*ASHLAR_LIMESTONE)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(command_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.fill(18, 28, 46)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(roof_courtyard_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    # -----------------------------------------------------------------------
    # LAYER 5: Animated Enfilading Crossfire Ballistic Lines of Defense (Lignes de Defense)
    # -----------------------------------------------------------------------
    # From each Bastion Flank (Angle de Flanc, R = 326 px), enfilading fire sweeps along the face
    # of the adjacent Bastion AND across the face of the adjacent Ravelin!
    ballistic_segs_gold = []
    ballistic_segs_red = []

    sweep_u = 0.5 + 0.5 * np.sin(tau * 2.0)
    for k in range(N_SIDES):
        # Right flank of Bastion k fires across Curtain k to Left Apex of Bastion k+1
        p_flank_R = polar_pt(345.0, (k + 0.16) * d_theta)
        p_apex_next = polar_pt(526.0 + 185.0 * sweep_u, (k + 1.0) * d_theta)
        ballistic_segs_gold.append([p_flank_R[0], p_flank_R[1], p_apex_next[0], p_apex_next[1]])

        # Left flank of Bastion k+1 fires across Curtain k to Right Apex of Bastion k
        p_flank_L = polar_pt(345.0, (k + 0.84) * d_theta)
        p_apex_cur = polar_pt(526.0 + 185.0 * (1.0 - sweep_u), (k + 0.0) * d_theta)
        ballistic_segs_gold.append([p_flank_L[0], p_flank_L[1], p_apex_cur[0], p_apex_cur[1]])

        # Ravelin crossfire rays covering the glacis approaches
        p_rav = polar_pt(565.0, (k + 0.5) * d_theta)
        p_glL = polar_pt(735.0, (k + 0.12 * sweep_u) * d_theta)
        p_glR = polar_pt(735.0, (k + 1.0 - 0.12 * sweep_u) * d_theta)
        ballistic_segs_red.append([p_rav[0], p_rav[1], p_glL[0], p_glL[1]])
        ballistic_segs_red.append([p_rav[0], p_rav[1], p_glR[0], p_glR[1]])

    py5.stroke(248, 198, 68, 165)
    py5.stroke_weight(1.5)
    py5.lines(np.array(ballistic_segs_gold, dtype=np.float32))

    py5.stroke(244, 96, 68, 155)
    py5.stroke_weight(1.3)
    py5.lines(np.array(ballistic_segs_red, dtype=np.float32))

    # 6. Outer Graduated Brass Artillery Goniometer Bezel Ring
    py5.no_fill()
    py5.stroke(94, 72, 38)
    py5.stroke_weight(3.2)
    py5.circle(CX, CY, R_MEDALLION * 2.0)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    tick_segs = []
    for deg in range(0, 360, 2):
        rad = np.deg2rad(deg)
        r0 = R_MEDALLION + 3.0
        r1 = R_RING_OUTER - 3.0 if deg % 10 == 0 else (R_MEDALLION + 18.0 if deg % 5 == 0 else R_MEDALLION + 10.0)
        tick_segs.append([
            CX + r0 * np.cos(rad), CY + r0 * np.sin(rad),
            CX + r1 * np.cos(rad), CY + r1 * np.sin(rad),
        ])
    py5.stroke(82, 62, 32, 195)
    py5.stroke_weight(1.4)
    py5.lines(np.array(tick_segs, dtype=np.float32))


# ---------------------------------------------------------------------------
# Side Panels & 8 Fortification Stereotomy / Ballistic Apparatuses
# ---------------------------------------------------------------------------
def draw_card_shell(x, y, w, h, fig_top, title_top, sub_top, fig_bot, title_bot, sub_bot):
    py5.fill(*CARD_BG)
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    mid_y = y + h * 0.49
    py5.stroke(184, 166, 136, 175)
    py5.stroke_weight(1.2)
    py5.line(x + 24, mid_y, x + w - 24, mid_y)

    py5.fill(*TEXT_ACCENT)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(14)
    py5.text(f"{fig_top} // {title_top}", x + 28, y + 22)
    py5.fill(*TEXT_SECONDARY)
    py5.text_size(12)
    py5.text(sub_top, x + 28, y + 44)

    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(f"{fig_bot} // {title_bot}", x + 28, mid_y + 20)
    py5.fill(*TEXT_SECONDARY)
    py5.text_size(12)
    py5.text(sub_bot, x + 28, mid_y + 42)


def draw_kv_rows(x, y_start, rows, row_h=33.0):
    for i, (k, v) in enumerate(rows):
        yy = y_start + i * row_h
        py5.fill(*TEXT_SECONDARY)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.text_size(12)
        py5.text(k, x, yy)
        py5.fill(*TEXT_PRIMARY)
        py5.text(f": {v}", x + 195, yy)


def draw_left_cards(tau):
    # --- TOP-LEFT CARD: FIG. 01 & FIG. 02 ---
    draw_card_shell(
        LEFT_X, CARD_Y_TOP, CARD_W, CARD_H_TOP,
        "FIG. 01", "TRACE ITALIENNE ZERO-DEAD-GROUND CROSSFIRE GEOMETRY",
        "LIGNE DE DEFENSE FICHANTE & RASANTE: RECIPROCAL BASTION FLANK ENFILADE (L <= 180 TOISES)",
        "FIG. 02", "DEFILADE CROSS-SECTION: RAMPART, FOSSE, DEMI-LUNE & GLACIS",
        "GRAZING ARTILLERY TRAJECTORY SHIELDING THE MASONRY SCARP BELOW THE GLACIS CREST",
    )

    # FIG. 01 Diagram: Single Bastioned Front (2 Half-Bastions + Curtain + Ravelin + Crossfire Lines)
    bx, by, bw, bh = LEFT_X + 28, CARD_Y_TOP + 86, 235.0, 245.0
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.rect(bx, by, bw, bh, 4)

    # Bastioned front trace inside box
    pts_bf = np.array([
        [bx + 22, by + 68],     # Left Bastion Apex
        [bx + 68, by + 112],    # Left Shoulder
        [bx + 58, by + 178],    # Left Curtain-Flank
        [bx + bw - 58, by + 178], # Right Curtain-Flank
        [bx + bw - 68, by + 112], # Right Shoulder
        [bx + bw - 22, by + 68],  # Right Bastion Apex
    ], dtype=np.float32)
    py5.stroke(*VOSGES_HIGH)
    py5.stroke_weight(2.8)
    for j in range(len(pts_bf) - 1):
        py5.line(pts_bf[j, 0], pts_bf[j, 1], pts_bf[j + 1, 0], pts_bf[j + 1, 1])

    # Crossfire lines of defense (Lignes de Defense)
    py5.stroke(*BALLISTIC_GOLD)
    py5.stroke_weight(1.6)
    py5.line(bx + 58, by + 178, bx + bw - 22, by + 68)
    py5.line(bx + bw - 58, by + 178, bx + 22, by + 68)

    # Triangular Ravelin in front of curtain
    py5.fill(*GLACIS_TURF_LIGHT)
    py5.stroke(*ASHLAR_LIMESTONE)
    py5.triangle(bx + bw * 0.5, by + 52, bx + bw * 0.34, by + 132, bx + bw * 0.66, by + 132)

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("EXTERIOR SIDE (C)", "180 Toises (~350.8 m Octagon Edge)"),
        ("PERPENDICULAR (P)", "P = C / 6 = 30 Toises Setback"),
        ("BASTION FACE (F)", "F = 2/7 * C = 51.4 Toises Masonry"),
        ("LINE OF DEFENSE", "L_def = 132 Toises (< Musket Range)"),
        ("FLANKING ANGLE", "Angle Diminue = 18.43 DEG Enfilade"),
        ("DEAD GROUND AREA", "Zero (100% Reciprocal Flank Cover)"),
        ("SYSTEM CLASS", "Vauban 3rd System (Neuf-Brisach)"),
    ])

    # FIG. 02 Diagram: Horizontal Defilade Profile (Rampart -> Ditch -> Covered Way -> Glacis)
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    px, py, pw, ph = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.rect(px, py, pw, ph, 4)

    # Profile polygon: Rampart at left -> Deep Ditch in middle -> Glacis slope at right
    y_water = py + 175.0
    py5.no_stroke()
    py5.fill(*MOAT_CERULEAN)
    py5.rect(px + 68, y_water, 78, 38)

    py5.stroke(*ASHLAR_LIMESTONE)
    py5.stroke_weight(2.2)
    prof_pts = [
        [px + 14, py + 145], [px + 32, py + 145], [px + 38, py + 108],
        [px + 58, py + 108], [px + 68, py + 212], [px + 146, py + 212],
        [px + 152, py + 138], [px + 172, py + 138], [px + 176, py + 122],
        [px + pw - 12, py + 168],
    ]
    for j in range(len(prof_pts) - 1):
        py5.line(prof_pts[j][0], prof_pts[j][1], prof_pts[j + 1][0], prof_pts[j + 1][1])

    # Grazing artillery defilade ray skimming Rampart Crest and Glacis Crest
    py5.stroke(*BALLISTIC_GOLD)
    py5.stroke_weight(1.8)
    py5.line(px + 58, py + 108, px + pw - 12, py + 146)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("SCARP PROTECTION", "Masonry Scarp Hidden Below Glacis"),
        ("RAMPART COMMAND", "+22 Pieds (+7.15 m) Above Campaign"),
        ("GLACIS CREST", "+8 Pieds (+2.60 m) Covering Wall"),
        ("MOAT DEPTH", "-18 Pieds (-5.85 m) Flooded Basin"),
        ("TALUS BATTER", "1:5 Masonry Slope Resists Cannon"),
        ("CORDON STONE", "Dressed Limestone Projecting Mould"),
        ("COVERED WAY", "Palisaded Infantry Musketry Shelf"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "VAUBAN SIEGE PARALLELS & SAPPER ZIGZAG APPROACHES",
        "THREE CONCENTRIC TRENCH PARALLELS & RICOCHET BATTERY GEOMETRY (TRAITE DE L'ATTAQUE, 1704)",
        "FIG. 04", "ALSACE VOSGES SANDSTONE, ASHLAR & TURF PALETTE",
        "PLANS-RELIEFS (1:600) POLYCHROME STEREOTOMY: TERRACOTTA BRICK, LIMESTONE & CANAL SLATE",
    )

    sx, sy, sw, sh = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.rect(sx, sy, sw, sh, 4)

    # 3 Concentric Siege Trench Parallels + Zigzag Saps (Boyaux de Communication)
    bx_s, by_s = sx + sw * 0.5, sy + 42.0
    py5.no_fill()
    py5.stroke(*ASHLAR_LIMESTONE)
    py5.stroke_weight(1.8)
    for r_par in [75.0, 128.0, 182.0]:
        py5.arc(bx_s, by_s, r_par * 2.0, r_par * 1.6, 0.22 * np.pi, 0.78 * np.pi)

    # Zigzag sapper trench approaching bastion apex at (bx_s, by_s + 22)
    py5.stroke(*BALLISTIC_GOLD)
    py5.stroke_weight(2.2)
    sap_pts = [
        [bx_s - 45, sy + 215], [bx_s + 38, sy + 182], [bx_s - 32, sy + 150],
        [bx_s + 26, sy + 118], [bx_s - 18, sy + 88], [bx_s, sy + 64],
    ]
    for j in range(len(sap_pts) - 1):
        py5.line(sap_pts[j][0], sap_pts[j][1], sap_pts[j + 1][0], sap_pts[j + 1][1])

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("1ST PARALLEL", "300 Toises (~585 m) Out of Grape"),
        ("2ND PARALLEL", "150 Toises (~292 m) Ricochet Fire"),
        ("3RD PARALLEL", "30 Toises (~58 m) Foot of Glacis"),
        ("ZIGZAG SAP ANGLE", "Defiladed Outside Bastion Ray Cone"),
        ("RICOCHET BATTERY", "Low-Charge Grazing Enfilade Shot"),
        ("SIEGE TIMETABLE", "Vauban 48-Day Mathematical Schedule"),
        ("COUNTER-MINE", "Subterranean Listening Galleries"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (VOSGES_SANDSTONE, "GRES DES VOSGES // ALSACE PINK-TERRACOTTA SANDSTONE SCARP (#CE5238)"),
        (ASHLAR_LIMESTONE, "PIERRE DE TAILLE // DRESSED JURASSIC LIMESTONE CORDON & CASEMATE (#E8CE98)"),
        (GLACIS_TURF_LIGHT, "GAZON DE REMBLAI // COMPACTED EARTHWORK GLACIS & PARAPET TURF (#38A47C)"),
        (MOAT_CERULEAN, "GRAND FOSSE INONDE // RHINE CANAL FLOODED DITCH BASIN (#1C487A)"),
        (BALLISTIC_GOLD, "LIGNE DE FEU // ENFILADING ARTILLERY & MUSKETRY CROSSFIRE (#F8C644)"),
        (MOAT_DEEP, "CONTRE-ESCARPE // RECESSED SHADOW & PLANS-RELIEFS TABLE SLATE (#0D1B2E)"),
    ]
    for i, (col, label) in enumerate(swatches):
        sy_s = mid_y_bot + 78 + i * 54
        py5.stroke(92, 84, 72, 150)
        py5.stroke_weight(1.2)
        py5.fill(int(col[0]), int(col[1]), int(col[2]))
        py5.rect(LEFT_X + 28, sy_s, 48, 34, 4)
        py5.fill(*TEXT_PRIMARY)
        py5.no_stroke()
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(label, LEFT_X + 94, sy_s + 17)


def draw_right_cards(tau):
    # --- TOP-RIGHT CARD: FIG. 05 & FIG. 06 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_TOP, CARD_W, CARD_H_TOP,
        "FIG. 05", "FORTIFIED POLYGONAL TAXONOMY (N = 4 TO N = 12 SIDES)",
        "INTERIOR POLYGON ANGLE ALPHA_N = (1 - 2/N)*180 DEG & BASTION SALIENT ACUTENESS RULE",
        "FIG. 06", "HISTORICAL TRACE ITALIENNE & MILITARY STEREOTOMY LEDGER",
        "FROM DURER (1527) & SANGALLO (1534) TO STEVIN (1594), COEHOORN (1685) & VAUBAN (1698)",
    )

    dx, dy = RIGHT_X + 145, CARD_Y_TOP + 215
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.rect(RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0, 4)

    # Nested Fortified Polygons: Pentagon (N=5), Hexagon (N=6), Octagon (N=8)
    for n_poly, r_p, col_p in [
        (8, 88.0, BALLISTIC_GOLD),
        (6, 62.0, GLACIS_TURF_LIGHT),
        (5, 38.0, VOSGES_HIGH),
    ]:
        py5.no_fill()
        py5.stroke(*col_p)
        py5.stroke_weight(2.2)
        py5.begin_shape()
        for k in range(n_poly * 2):
            ang = k * np.pi / n_poly + tau * 0.25
            rr = r_p if k % 2 == 0 else r_p * 0.72
            py5.vertex(dx + rr * np.cos(ang), dy + rr * np.sin(ang))
        py5.end_shape(py5.CLOSE)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("SQUARE FORT (N=4)", "Alpha = 90 DEG (Acute 60 DEG Salient)"),
        ("PENTAGON CITADEL (5)", "Alpha = 108 DEG (Turin / Antwerp)"),
        ("HEXAGON FORTRESS (6)", "Alpha = 120 DEG (Coevorden / Naarden)"),
        ("OCTAGON MASTER (8)", "Alpha = 135 DEG (Neuf-Brisach, 1698)"),
        ("DODECAGON PLACE (12)", "Alpha = 150 DEG (Flattest Curtain)"),
        ("MIN SALIENT RULE", "Angle Saillant >= 60 DEG Stone Strength"),
        ("TOWER BASTIONS", "8 Vaulted Casemate Artillery Keeps"),
    ])

    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("NUREMBERG (1527)", "Albrecht Durer", "Bastei Rondels", "First Printed Fortification Treatise"),
        ("FORTEZZA DA BASSO (1534)", "Antonio da Sangallo", "Pentagonal Star", "Angle-Bastion Trace Italienne"),
        ("STERCTENBOUWING (1594)", "Simon Stevin", "Dutch Water Moat", "Mathematical Regular Polygons"),
        ("TRAVAUX DE MARS (1671)", "Manesson Mallet", "3-Volume Atlas", "Codified European Star Geometry"),
        ("VESTINGBOUW (1685)", "Menno van Coehoorn", "Low Wet Outworks", "Bergen op Zoom Counterguards"),
        ("NEUF-BRISACH (1698)", "Sebastien de Vauban", "Octagonal 3rd Sys.", "UNESCO IDEAL FORTIFIED CITY"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(*(MOAT_DEEP if is_active else (240, 234, 220)))
        py5.stroke(*(TEXT_ACCENT if is_active else CARD_BORDER))
        py5.stroke_weight(1.6 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(BALLISTIC_GOLD if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*(ASHLAR_LIMESTONE if is_active else TEXT_SECONDARY))
        py5.text(author, RIGHT_X + 245, ry + 21)
        py5.fill(*(GLACIS_TURF_LIGHT if is_active else TEXT_ACCENT))
        py5.text(metric, RIGHT_X + 435, ry + 21)
        py5.fill(*(ASHLAR_LIMESTONE if is_active else TEXT_PRIMARY))
        py5.text(desc, RIGHT_X + 605, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "ORTHOGONAL CASTRAMETATION GRID & PLACE D'ARMES",
        "VITRUVIAN-VAUBAN 8x8 CARTESIAN URBAN GRID CLIPPED TO OCTAGONAL ENCEINTE",
        "FIG. 08", "RADIAL FORTIFICATION RELIEF & CROSSFIRE DENSITY OSCILLOGRAM",
        "ALTITUDE PROFILE Z(r) FROM PLACE D'ARMES TO GLACIS & INTERSECTING FIRE ENVELOPE",
    )

    tx, ty, tw, th = RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.rect(tx, ty, tw, th, 4)

    # Mini Castrametation 4x4 grid + Place d'Armes + 4 Cardinal Gates
    gx0, gy0 = tx + 42.0, ty + 48.0
    g_step = 38.0
    for r_g in range(4):
        for c_g in range(4):
            if r_g in (1, 2) and c_g in (1, 2):
                continue
            py5.fill(*VOSGES_SANDSTONE)
            py5.stroke(*ASHLAR_LIMESTONE)
            py5.stroke_weight(1.0)
            py5.rect(gx0 + c_g * g_step + 3, gy0 + r_g * g_step + 3, g_step - 6, g_step - 6, 2)

    py5.no_fill()
    py5.stroke(*BALLISTIC_GOLD)
    py5.stroke_weight(1.8)
    py5.rect(gx0 + g_step + 3, gy0 + g_step + 3, g_step * 2 - 6, g_step * 2 - 6, 2)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("URBAN GRID", "48 Regular Square Ilots (Blocks)"),
        ("PLACE D'ARMES", "Central 4-Block Parade & Muster Sq."),
        ("FOUR ROYAL GATES", "Colmar, Bale, Strasbourg, Belfort"),
        ("ARCHITECTS", "Vauban & Jacques Tarade (1698)"),
        ("GARRISON CAPACITY", "4,500 Troops + Bombproof Casemates"),
        ("SCALE MODEL", "1:600 Plan-Relief (Musee Invalides)"),
        ("SYMMETRY GROUP", "Dihedral D_8 Octagonal Invariance"),
    ])

    # FIG. 08 Oscillogram: Radial Altitude Profile & Ballistic Crossfire Density
    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    ox, oy, ow, oh = RIGHT_X + 28, mid_y_bot + 78, CARD_W - 56, 265.0
    py5.fill(*MOAT_DEEP)
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(1.5)
    py5.rect(ox, oy, ow, oh, 4)

    grid_segs = []
    for g in range(1, 4):
        gy = oy + g * (oh / 4.0)
        grid_segs.append([ox, gy, ox + ow, gy])
    for g in range(1, 8):
        gx = ox + g * (ow / 8.0)
        grid_segs.append([gx, oy, gx, oy + oh])
    py5.stroke(28, 48, 78)
    py5.stroke_weight(1.0)
    py5.lines(np.array(grid_segs, dtype=np.float32))

    xs_osc = np.linspace(0.0, 1.0, 160)
    x_px = ox + 16.0 + xs_osc * (ow - 32.0)

    waves = [
        (248, 198, 68, 0.0, 1.0),
        (238, 128, 94, 1.1, 0.85),
        (56, 164, 124, 2.2, 0.72),
    ]
    for rc, gc, bc, p_shift, amp_s in waves:
        y_sig = (
            0.65 * np.sin(xs_osc * 8.0 * np.pi - tau * 2.0 + p_shift)
            + 0.35 * np.cos(xs_osc * 16.0 * np.pi + tau)
        ) * (oh * 0.34 * amp_s)
        y_px = oy + oh * 0.50 - y_sig
        segs = np.empty((len(xs_osc) - 1, 4), dtype=np.float32)
        segs[:, 0], segs[:, 1] = x_px[:-1], y_px[:-1]
        segs[:, 2], segs[:, 3] = x_px[1:], y_px[1:]
        py5.stroke(rc, gc, bc, 235)
        py5.stroke_weight(2.2)
        py5.lines(segs)

    py5.no_stroke()
    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(12)
    py5.text(
        "GOLD: ENFILADING CROSSFIRE DENSITY // TERRACOTTA: BASTION DEFLECTION // EMERALD: GLACIS DEFILADE",
        ox + 4, oy + oh + 14,
    )


def draw_header_and_footer(tau):
    py5.stroke(222, 212, 192, 130)
    py5.stroke_weight(1.0)
    py5.lines(GRID_LINES)

    py5.no_fill()
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(2.2)
    py5.rect(48, 42, WIDTH - 96, HEIGHT - 84, 10)

    py5.fill(*TEXT_PRIMARY)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(26)
    py5.text(
        "VAUBAN BASTIONED TRACE ITALIENNE // NEUF-BRISACH OCTAGONAL STAR CITADEL",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "TROISIEME SYSTEME DE VAUBAN (1698), ZERO-DEAD-GROUND DEFILADE STEREOTOMY & 1:600 PLANS-RELIEFS CARTOGRAPHY",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "8 BASTIONED TOWERS & COUNTERGUARDS // 8 DEMI-LUNES & REDOUBTS // 8 TENAILLES // ORTHOGONAL PLACE D'ARMES GRID",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ARCHITECTURAL STEREOTOMY // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_VELLUM)

    draw_header_and_footer(tau)
    draw_vauban_citadel_medallion(tau)
    draw_left_cards(tau)
    draw_right_cards(tau)

    frame_path = FRAMES_DIR / f"frame_{frame_idx:04d}.png"
    py5.save_frame(str(frame_path))

    if frame_idx == 0:
        shutil.copyfile(frame_path, PREVIEW_PATH)
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_PATH}")

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
        print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES / max(total_elapsed, 1e-6):.2f} fps).")
        compile_mp4()
        py5.exit_sketch()


def compile_mp4():
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "16",
        "-preset", "fast",
        str(OUTPUT_MP4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"[{WORK_NAME}] Successfully generated output.mp4 ({size_mb:.2f} MB)")
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
    print(f"[{WORK_NAME}] Complete!")


if __name__ == "__main__":
    py5.run_sketch()

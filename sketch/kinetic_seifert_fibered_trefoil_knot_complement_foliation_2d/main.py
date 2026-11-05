"""
kinetic_seifert_fibered_trefoil_knot_complement_foliation_2d

Herbert Seifert's 1934 Bicollared Orientable Surface (Seifert Surface Sigma_K)
Spanning the (2,3) Trefoil Knot K_{2,3} in S^3, John Milnor's 1968 Open-Book
Fibration phi: S^3 \\ K_{2,3} -> S^1 of the Cusp Singularity (z_1^2 + z_2^3 = 0),
and First Homology Generators H_1(Sigma_K; Z) = Z^2, inspired by Seifert (1934),
Milnor (1968), Rolfsen's Knots and Links (1976), and Etienne Ghys & Jos Leys's
modular flow and Milnor fiber visualizations.
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
WORK_NAME = "kinetic_seifert_fibered_trefoil_knot_complement_foliation_2d"
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
R_VIEWPORT = 805.0
R_RING_OUTER = 842.0

LEFT_X, CARD_W = 104.0, 860.0
RIGHT_X = 3840.0 - 104.0 - 860.0
CARD_Y_TOP = 180.0
CARD_H_TOP = 885.0
CARD_Y_BOT = 1105.0
CARD_H_BOT = 885.0

# ---------------------------------------------------------------------------
# Color Palette — Deep Topology Obsidian & Bicollared Seifert Surface Palette
# ---------------------------------------------------------------------------
BG_OBSIDIAN = (6, 9, 18)          # #060912 Deep 3-Manifold & Chern-Simons Obsidian
CARD_BG = (11, 16, 30, 236)       # Translucent Topology Telemetry Slate
CARD_BORDER = (46, 68, 108)       # Instrument Frame Rule
TEXT_PRIMARY = (236, 242, 252)    # Crisp Alabaster White
TEXT_SECONDARY = (150, 172, 206)  # Muted Cohomology Slate
TEXT_ACCENT = (254, 206, 78)      # Trefoil Binding Gold

# Curated Bicollared Normal & Open-Book Fibration Swatches
POS_SAPPHIRE = np.array([34.0, 142.0, 254.0], dtype=np.float32)       # Page I (+N) Bicollared Sapphire-Cerulean
NEG_CRIMSON = np.array([246.0, 48.0, 128.0], dtype=np.float32)        # Page I (-N) Bicollared Rose-Crimson
PAGE2_EMERALD = np.array([20.0, 228.0, 168.0], dtype=np.float32)      # Page II (+N) Conjugate Milnor Emerald
PAGE2_VIOLET = np.array([172.0, 84.0, 252.0], dtype=np.float32)       # Page II (-N) Conjugate Heliotrope
BINDING_GOLD = np.array([252.0, 192.0, 56.0], dtype=np.float32)       # Trefoil Knot K_{2,3} Binding Gold
HOMOLOGY_CYAN = np.array([56.0, 232.0, 255.0], dtype=np.float32)      # H_1(Sigma; Z) Generator Loop Cyan

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

# Precomputed parametric grids for the Milnor/Seifert pages & Trefoil binding tube
S_GRID = None
V_GRID = None
KNOT_S = None
KNOT_PHI = None


def init_seifert_mesh():
    """Precompute parametric grids (THETA, V) for the Seifert surfaces & knot tube."""
    global S_GRID, V_GRID, KNOT_S, KNOT_PHI

    # theta in [0, 2*pi) sweeps around the 3-fold symmetry axis (n_theta = 132)
    # v in [-1, 1] spans across the Seifert band between strand 1 (s = theta/2)
    # and strand 2 (s = theta/2 + pi) of the (2,3) Trefoil Knot!
    n_theta = 132
    n_v = 20
    theta_vals = np.linspace(0.0, 2.0 * np.pi, n_theta + 1, dtype=np.float32)
    v_vals = np.linspace(-1.0, 1.0, n_v + 1, dtype=np.float32)
    S_GRID, V_GRID = np.meshgrid(theta_vals, v_vals, indexing="ij")

    # Trefoil knot tubular neighborhood grid (n_ks = 156, n_kphi = 10)
    ks = np.linspace(0.0, 2.0 * np.pi, 157, dtype=np.float32)
    kp = np.linspace(0.0, 2.0 * np.pi, 11, dtype=np.float32)
    KNOT_S, KNOT_PHI = np.meshgrid(ks, kp, indexing="ij")


def trefoil_curve_3d(s):
    """
    Canonical 3-fold symmetric (2,3) Trefoil Knot K_{2,3} in R^3:
    As s goes from 0 to 2*pi, azimuth 2*s winds twice around the origin while
    radius and z oscillate 3 times (3 outer lobes, 3 inner saddle crossings).
    """
    r_tor = 1.72 + 0.86 * np.cos(3.0 * s)
    x = r_tor * np.cos(2.0 * s)
    y = r_tor * np.sin(2.0 * s)
    z = -1.12 * np.sin(3.0 * s)
    return x, y, z


def seifert_page_surface_3d(THETA, V, page_angle):
    """
    Construct a smooth, non-self-intersecting 3D Milnor Open-Book Seifert Surface Page
    spanning between the two strands s_1 = THETA/2 and s_2 = THETA/2 + pi of the
    (2,3) Trefoil Knot K_{2,3}!
    - At V = -1: lies identically on strand 1 of K_{2,3}
    - At V = +1: lies identically on strand 2 of K_{2,3}
    - Across V in (-1, 1): arches along the Milnor open-book page angle page_angle,
      exhibiting the 3 half-twist Seifert saddle crossings where cos(1.5*THETA) = 0
      and the 3 broad Seifert lobes where |cos(1.5*THETA)| = 1!
    """
    s1 = 0.5 * THETA
    s2 = 0.5 * THETA + np.pi

    x1, y1, z1 = trefoil_curve_3d(s1)
    x2, y2, z2 = trefoil_curve_3d(s2)

    # Linear chord between the two strands at azimuth THETA
    u0 = 0.5 * (1.0 - V)
    u1 = 0.5 * (1.0 + V)
    x_lin = u0 * x1 + u1 * x2
    y_lin = u0 * y1 + u1 * y2
    z_lin = u0 * z1 + u1 * z2

    # Smooth arch envelope (1 - V^2) that vanishes identically on the Trefoil boundary V = +-1
    arch_env = 1.0 - V * V

    # Milnor open-book billowing normal displacement in radial and Z directions
    # Modulated by the 3-fold lobe factor cos(1.5 * THETA) so the two sides (+N and -N)
    # alternate across the 3 half-twisted saddle bands!
    lobe_mod = np.cos(1.5 * THETA)
    cross_mod = np.sin(1.5 * THETA)

    r_arch = 0.52 * arch_env * (np.cos(page_angle) + 0.45 * V * cross_mod)
    z_arch = 1.05 * arch_env * (np.sin(page_angle) * lobe_mod + 0.38 * np.cos(page_angle) * V)

    X = x_lin + r_arch * np.cos(THETA)
    Y = y_lin + r_arch * np.sin(THETA)
    Z = z_lin + z_arch
    return X, Y, Z


def rotate_3d(X, Y, Z, pitch, yaw, roll):
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    cr, sr = np.cos(roll), np.sin(roll)

    # Yaw around Y
    x1 = X * cy + Z * sy
    y1 = Y
    z1 = -X * sy + Z * cy

    # Pitch around X
    x2 = x1
    y2 = y1 * cp - z1 * sp
    z2 = y1 * sp + z1 * cp

    # Roll around Z
    x3 = x2 * cr - y2 * sr
    y3 = x2 * sr + y2 * cr
    z3 = z2
    return x3, y3, z3


def project_to_viewport(X, Y, Z, scale_px=238.0):
    persp = 9.2 / np.maximum(9.2 - Z, 3.5)
    sx = CX + X * scale_px * persp
    sy = CY + Y * scale_px * persp
    return sx, sy, Z


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

    init_seifert_mesh()
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


# ---------------------------------------------------------------------------
# Main Viewport: Open-Book Seifert Surface Foliation & Trefoil Knot K_{2,3}
# ---------------------------------------------------------------------------
def draw_seifert_fibration_viewport(tau):
    r_inner = R_VIEWPORT - 12.0

    # 1. Outer Bezel & Recessed 3-Sphere Projection Dome
    py5.no_stroke()
    py5.fill(14, 22, 42)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    py5.fill(5, 8, 18)
    py5.circle(CX, CY, R_VIEWPORT * 2.0)

    for k in range(8, 0, -1):
        frac = k / 8.0
        py5.fill(14, 28, 62, int(20 * (1.0 - frac * 0.7)))
        py5.circle(CX, CY, R_VIEWPORT * 1.85 * frac)

    # Stereographic S^3 coordinate circles & Clifford torus projection rings
    py5.no_fill()
    py5.stroke(28, 52, 96, 105)
    py5.stroke_weight(1.1)
    for r_c in [210.0, 380.0, 540.0, 680.0, 765.0]:
        py5.circle(CX, CY, r_c * 2.0)

    # 3D Camera Orientation: Gentle nutation + 1-turn azimuthal rotation over 720 frames
    pitch = 0.42 + 0.16 * np.sin(tau + PHASE_OFFSET)
    yaw = 0.28 * np.cos(tau + PHASE_OFFSET)
    roll = tau + PHASE_OFFSET * 0.5

    # Light direction in camera space
    lx, ly, lz = 0.42, -0.56, 0.71

    # 2. Collect 3D Quads across 2 Conjugate Open-Book Seifert Pages + Trefoil Knot Tube
    # Depth-sort across 16 Z-slabs so over/under crossings of the Trefoil and Seifert bands are 100% exact!
    n_z_slabs = 16
    z_min, z_max = -2.4, 2.4
    # Bucket key: (slab_idx, color_r, color_g, color_b, alpha) -> list of 4x2 quad vertices
    slab_buckets = [{} for _ in range(n_z_slabs)]
    homology_lines_3d = []

    pages_config = [
        # Page I: Primary Sovereign Seifert Surface (Sapphire +N / Crimson -N)
        {"angle": tau, "pos_rgb": POS_SAPPHIRE, "neg_rgb": NEG_CRIMSON, "alpha": 218, "draw_homology": True},
        # Page II: Dual Conjugate Milnor Fiber Page pi radians apart (Emerald +N / Violet -N)
        {"angle": tau + np.pi, "pos_rgb": PAGE2_EMERALD, "neg_rgb": PAGE2_VIOLET, "alpha": 168, "draw_homology": False},
    ]

    for p_cfg in pages_config:
        X, Y, Z = seifert_page_surface_3d(S_GRID, V_GRID, p_cfg["angle"])
        Xr, Yr, Zr = rotate_3d(X, Y, Z, pitch, yaw, roll)
        SX, SY, _ = project_to_viewport(Xr, Yr, Zr)

        # Compute quad vertices and 3D surface normals for bicollared (+N / -N) shading
        p00 = np.stack([Xr[:-1, :-1], Yr[:-1, :-1], Zr[:-1, :-1]], axis=-1)
        p10 = np.stack([Xr[1:, :-1], Yr[1:, :-1], Zr[1:, :-1]], axis=-1)
        p11 = np.stack([Xr[1:, 1:], Yr[1:, 1:], Zr[1:, 1:]], axis=-1)
        p01 = np.stack([Xr[:-1, 1:], Yr[:-1, 1:], Zr[:-1, 1:]], axis=-1)

        u_vec = p10 - p00
        v_vec = p01 - p00
        n_vec = np.cross(u_vec, v_vec)
        n_norm = np.maximum(np.linalg.norm(n_vec, axis=-1, keepdims=True), 1e-5)
        n_unit = n_vec / n_norm

        # Two-sided orientation sign (nz >= 0 is +N side, nz < 0 is -N side)
        nz = n_unit[..., 2]
        dot_l = np.abs(n_unit[..., 0] * lx + n_unit[..., 1] * ly + n_unit[..., 2] * lz)
        # Quantize lighting into 6 shade levels for fast batched rendering
        shade_idx = np.clip((dot_l * 5.99).astype(np.int32), 0, 5)

        z_mid = 0.25 * (Zr[:-1, :-1] + Zr[1:, :-1] + Zr[1:, 1:] + Zr[:-1, 1:])
        slab_idx = np.clip(((z_mid - z_min) / (z_max - z_min) * n_z_slabs).astype(np.int32), 0, n_z_slabs - 1)

        sx00, sy00 = SX[:-1, :-1], SY[:-1, :-1]
        sx10, sy10 = SX[1:, :-1], SY[1:, :-1]
        sx11, sy11 = SX[1:, 1:], SY[1:, 1:]
        sx01, sy01 = SX[:-1, 1:], SY[:-1, 1:]

        # Checkerboard/band modulation along S to highlight the 3 twisted Seifert bands
        S_mid = 0.5 * (S_GRID[:-1, :-1] + S_GRID[1:, :-1])
        V_mid = 0.5 * (V_GRID[:-1, :-1] + V_GRID[:-1, 1:])
        band_boost = 1.0 + 0.14 * np.cos(6.0 * S_mid) * np.sin(V_mid * np.pi)

        for sl in range(n_z_slabs):
            sl_mask = slab_idx == sl
            if not np.any(sl_mask):
                continue
            for side_sign, base_rgb in [(True, p_cfg["pos_rgb"]), (False, p_cfg["neg_rgb"])]:
                orient_mask = sl_mask & ((nz >= 0.0) if side_sign else (nz < 0.0))
                if not np.any(orient_mask):
                    continue
                for sh in range(6):
                    m = orient_mask & (shade_idx == sh)
                    if not np.any(m):
                        continue
                    sh_f = (0.46 + 0.11 * sh) * float(np.mean(band_boost[m]))
                    rc = int(np.clip(base_rgb[0] * sh_f, 0, 255))
                    gc = int(np.clip(base_rgb[1] * sh_f, 0, 255))
                    bc = int(np.clip(base_rgb[2] * sh_f, 0, 255))
                    key = (rc, gc, bc, p_cfg["alpha"])

                    n_q = int(np.sum(m))
                    qv = np.empty((n_q * 4, 2), dtype=np.float32)
                    qv[0::4, 0], qv[0::4, 1] = sx00[m], sy00[m]
                    qv[1::4, 0], qv[1::4, 1] = sx10[m], sy10[m]
                    qv[2::4, 0], qv[2::4, 1] = sx11[m], sy11[m]
                    qv[3::4, 0], qv[3::4, 1] = sx01[m], sy01[m]
                    if key in slab_buckets[sl]:
                        slab_buckets[sl][key].append(qv)
                    else:
                        slab_buckets[sl][key] = [qv]

        # Extract First Homology Generator Loops H_1(Sigma; Z) & Seifert Iso-V Ribs on Primary Page
        if p_cfg["draw_homology"]:
            for v_idx in [0, 5, 10, 14]:
                for s_i in range(SX.shape[0] - 1):
                    homology_lines_3d.append([
                        SX[s_i, v_idx], SY[s_i, v_idx],
                        SX[s_i + 1, v_idx], SY[s_i + 1, v_idx],
                        1 if v_idx in (5, 10) else 0,
                    ])
            for s_i in range(0, SX.shape[0] - 1, 3):
                for v_i in range(SX.shape[1] - 1):
                    homology_lines_3d.append([
                        SX[s_i, v_i], SY[s_i, v_i],
                        SX[s_i, v_i + 1], SY[s_i, v_i + 1],
                        0,
                    ])

    # 3. Construct the 3D Braided Golden Tube for the Binding Trefoil Knot K_{2,3}
    ks_1d = KNOT_S[:, 0]
    kx, ky, kz = trefoil_curve_3d(ks_1d)
    # Frenet-like normal/binormal frame along the trefoil curve
    tx = np.gradient(kx)
    ty = np.gradient(ky)
    tz = np.gradient(kz)
    t_len = np.maximum(np.sqrt(tx * tx + ty * ty + tz * tz), 1e-5)
    tx, ty, tz = tx / t_len, ty / t_len, tz / t_len

    # Radial outward vector as reference normal
    r_len = np.maximum(np.sqrt(kx * kx + ky * ky + kz * kz), 1e-5)
    rx, ry, rz = kx / r_len, ky / r_len, kz / r_len
    # Binormal B = T x R
    bx = ty * rz - tz * ry
    by = tz * rx - tx * rz
    bz = tx * ry - ty * rx
    b_len = np.maximum(np.sqrt(bx * bx + by * by + bz * bz), 1e-5)
    bx, by, bz = bx / b_len, by / b_len, bz / b_len
    # Principal normal N = B x T
    nx = by * tz - bz * ty
    ny = bz * tx - bx * tz
    nz_k = bx * ty - by * tx

    r_tube = 0.115
    cos_p = np.cos(KNOT_PHI)
    sin_p = np.sin(KNOT_PHI)
    TX = kx[:, None] + r_tube * (nx[:, None] * cos_p + bx[:, None] * sin_p)
    TY = ky[:, None] + r_tube * (ny[:, None] * cos_p + by[:, None] * sin_p)
    TZ = kz[:, None] + r_tube * (nz_k[:, None] * cos_p + bz[:, None] * sin_p)

    TXr, TYr, TZr = rotate_3d(TX, TY, TZ, pitch, yaw, roll)
    TSX, TSY, _ = project_to_viewport(TXr, TYr, TZr)

    tz_mid = 0.25 * (TZr[:-1, :-1] + TZr[1:, :-1] + TZr[1:, 1:] + TZr[:-1, 1:])
    t_slab = np.clip(((tz_mid - z_min) / (z_max - z_min) * n_z_slabs).astype(np.int32), 0, n_z_slabs - 1)

    # Shade tube facets with specular gold-bronze highlights
    phi_mid = 0.5 * (KNOT_PHI[:-1, :-1] + KNOT_PHI[:-1, 1:])
    s_knot_mid = 0.5 * (KNOT_S[:-1, :-1] + KNOT_S[1:, :-1])
    # Helical (2,3) framing stripe along the knot tube
    stripe = np.cos(3.0 * s_knot_mid + 2.0 * phi_mid - tau * 2.0)

    tsx00, tsy00 = TSX[:-1, :-1], TSY[:-1, :-1]
    tsx10, tsy10 = TSX[1:, :-1], TSY[1:, :-1]
    tsx11, tsy11 = TSX[1:, 1:], TSY[1:, 1:]
    tsx01, tsy01 = TSX[:-1, 1:], TSY[:-1, 1:]

    for sl in range(n_z_slabs):
        m_gold = (t_slab == sl) & (stripe >= -0.15)
        m_amber = (t_slab == sl) & (stripe < -0.15)
        for m, col_k in [
            (m_gold, (255, 224, 108, 255)),
            (m_amber, (214, 128, 36, 255)),
        ]:
            if not np.any(m):
                continue
            n_q = int(np.sum(m))
            qv = np.empty((n_q * 4, 2), dtype=np.float32)
            qv[0::4, 0], qv[0::4, 1] = tsx00[m], tsy00[m]
            qv[1::4, 0], qv[1::4, 1] = tsx10[m], tsy10[m]
            qv[2::4, 0], qv[2::4, 1] = tsx11[m], tsy11[m]
            qv[3::4, 0], qv[3::4, 1] = tsx01[m], tsy01[m]
            if col_k in slab_buckets[sl]:
                slab_buckets[sl][col_k].append(qv)
            else:
                slab_buckets[sl][col_k] = [qv]

    # 4. Flush all 16 Depth-Sorted Z-Slabs back-to-front!
    py5.no_stroke()
    for sl in range(n_z_slabs):
        for (rc, gc, bc, ac), q_list in slab_buckets[sl].items():
            py5.fill(rc, gc, bc, ac)
            py5.begin_shape(py5.QUADS)
            py5.vertices(np.vstack(q_list))
            py5.end_shape()

    # Overlay crisp Homology Generator Loops & Seifert Mesh Ribs
    if homology_lines_3d:
        h_arr = np.array(homology_lines_3d, dtype=np.float32)
        m_rib = h_arr[:, 4] == 0
        m_gen = h_arr[:, 4] == 1
        if np.any(m_rib):
            py5.stroke(226, 240, 255, 78)
            py5.stroke_weight(1.05)
            py5.lines(h_arr[m_rib, :4])
        if np.any(m_gen):
            py5.stroke(255, 244, 156, 210)
            py5.stroke_weight(2.2)
            py5.lines(h_arr[m_gen, :4])

    # 5. Precision Brass & Cohomology Goniometer Bezel Ring
    py5.no_fill()
    py5.stroke(46, 68, 108)
    py5.stroke_weight(3.0)
    py5.circle(CX, CY, R_VIEWPORT * 2.0)

    py5.stroke(254, 206, 78, 195)
    py5.stroke_weight(2.2)
    py5.circle(CX, CY, (R_VIEWPORT - 10.0) * 2.0)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    tick_segs = []
    for deg in range(0, 360, 2):
        rad = np.deg2rad(deg)
        r0 = R_VIEWPORT + 2.0
        r1 = R_RING_OUTER - 3.0 if deg % 10 == 0 else (R_VIEWPORT + 18.0 if deg % 5 == 0 else R_VIEWPORT + 10.0)
        tick_segs.append([
            CX + r0 * np.cos(rad), CY + r0 * np.sin(rad),
            CX + r1 * np.cos(rad), CY + r1 * np.sin(rad),
        ])
    py5.stroke(214, 182, 102, 165)
    py5.stroke_weight(1.3)
    py5.lines(np.array(tick_segs, dtype=np.float32))


# ---------------------------------------------------------------------------
# Side Panels & 8 Low-Dimensional Topology / Knot Invariant Apparatuses
# ---------------------------------------------------------------------------
def draw_card_shell(x, y, w, h, fig_top, title_top, sub_top, fig_bot, title_bot, sub_bot):
    py5.fill(*CARD_BG)
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    mid_y = y + h * 0.49
    py5.stroke(46, 68, 108, 160)
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
        "FIG. 01", "SEIFERT'S ALGORITHM: 2 SEIFERT DISKS & 3 HALF-TWIST BANDS",
        "ORIENTATION-PRESERVING RESOLUTION OF 3 CROSSINGS -> EULER CHAR. CHI = 2 - 3 = -1 (GENUS g = 1)",
        "FIG. 02", "SEIFERT MATRIX V & ALEXANDER-CONWAY POLYNOMIAL INVARIANT",
        "DELTA_K(t) = DET(V - t * V^T) = t - 1 + t^-1 // SYMPLECTIC INTERSECTION FORM ON H_1(SIGMA; Z)",
    )

    # FIG. 01 Diagram: 2 Nested Seifert Disks (+N Sapphire, -N Crimson) + 3 Twisted Saddle Bridges
    dx, dy = LEFT_X + 145, CARD_Y_TOP + 215
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(LEFT_X + 28, CARD_Y_TOP + 86, 235.0, 245.0, 4)

    py5.stroke(*BINDING_GOLD)
    py5.stroke_weight(2.0)
    py5.fill(34, 142, 254, 95)
    py5.circle(dx, dy, 178.0)
    py5.fill(246, 48, 128, 145)
    py5.circle(dx, dy, 88.0)

    # 3 Half-twist bands at 120-degree intervals
    for k in range(3):
        ang = k * (2.0 * np.pi / 3.0) + tau * 0.35
        x_in, y_in = dx + 44.0 * np.cos(ang), dy + 44.0 * np.sin(ang)
        x_out, y_out = dx + 89.0 * np.cos(ang), dy + 89.0 * np.sin(ang)
        tx_p, ty_p = -14.0 * np.sin(ang), 14.0 * np.cos(ang)
        py5.stroke(*HOMOLOGY_CYAN)
        py5.stroke_weight(2.4)
        py5.line(x_in - tx_p, y_in - ty_p, x_out + tx_p, y_out + ty_p)
        py5.line(x_in + tx_p, y_in + ty_p, x_out - tx_p, y_out - ty_p)

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("KNOT TAXONOMY", "T(2,3) Right-Handed Trefoil (3_1)"),
        ("CROSSING NUMBER", "c(K) = 3 Minimal Alternating"),
        ("SEIFERT CIRCLES", "s = 2 Concentric Oriented Disks"),
        ("TWISTED BANDS", "b = 3 Half-Turn Saddle Strips"),
        ("EULER CHARACTER.", "chi(Sigma) = s - b = 2 - 3 = -1"),
        ("MINIMAL GENUS", "g(K) = (1 - chi) / 2 = 1 (Torus)"),
        ("BICOLLARED NORMAL", "Sigma x [-1, +1] Embedded in S^3"),
    ])

    # FIG. 02 Diagram: Homology Basis Loops [a], [b] & Seifert Matrix V = [[-1, 1], [0, -1]]
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    mx, my, mw, mh = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(mx, my, mw, mh, 4)

    # Intersecting homology basis cycles [a] and [b] with linking numbers lk(a+, a) = -1, lk(a+, b) = 1
    py5.no_fill()
    py5.stroke(*HOMOLOGY_CYAN)
    py5.stroke_weight(2.6)
    py5.ellipse(mx + 92, my + 122, 112.0, 88.0)
    py5.stroke(*NEG_CRIMSON)
    py5.ellipse(mx + 144, my + 122, 112.0, 88.0)
    py5.fill(*BINDING_GOLD)
    py5.no_stroke()
    py5.circle(mx + 118, my + 84, 9.0)
    py5.circle(mx + 118, my + 160, 9.0)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("FIRST HOMOLOGY", "H_1(Sigma; Z) = Z[a] (+) Z[b]"),
        ("SEIFERT PAIRING", "V_ij = lk(alpha_i^+, alpha_j) in S^3"),
        ("SEIFERT MATRIX V", "V = [[-1, 1], [0, -1]] (det V = 1)"),
        ("ALEXANDER POLY.", "Delta_K(t) = t - 1 + t^-1"),
        ("CONWAY POLYNOMIAL", "nabla_K(z) = 1 + z^2"),
        ("JONES POLYNOMIAL", "V_K(q) = q + q^3 - q^4"),
        ("KNOT SIGNATURE", "sigma(K) = sign(V + V^T) = -2"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "MILNOR OPEN-BOOK FIBRATION: z_1^2 + z_2^3 = 0 IN C^2",
        "PHI(z_1, z_2) = (z_1^2 + z_2^3) / |z_1^2 + z_2^3| in S^1 // MONODROMY M = (V^T)^-1 * V (M^6 = I)",
        "FIG. 04", "BICOLLARED ORIENTATION & MILNOR FIBER PALETTE",
        "TWO-SIDED NORMAL BUNDLE (+N / -N), CONJUGATE OPEN-BOOK PAGES & TREFOIL BINDING",
    )

    sx, sy, sw, sh = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(sx, sy, sw, sh, 4)

    # Open-Book Page Fan around central Binding Point K
    cx_ob, cy_ob = sx + sw * 0.5, sy + sh * 0.5
    for p_k in range(12):
        ang_p = p_k * (np.pi / 6.0) + tau
        col_p = POS_SAPPHIRE if p_k % 2 == 0 else PAGE2_EMERALD
        py5.stroke(int(col_p[0]), int(col_p[1]), int(col_p[2]), 185)
        py5.stroke_weight(2.0)
        py5.no_fill()
        x_end = cx_ob + 88.0 * np.cos(ang_p)
        y_end = cy_ob + 88.0 * np.sin(ang_p)
        py5.bezier(
            cx_ob, cy_ob,
            cx_ob + 45.0 * np.cos(ang_p + 0.5), cy_ob + 45.0 * np.sin(ang_p + 0.5),
            cx_ob + 70.0 * np.cos(ang_p - 0.3), cy_ob + 70.0 * np.sin(ang_p - 0.3),
            x_end, y_end,
        )
    py5.no_stroke()
    py5.fill(*BINDING_GOLD)
    py5.circle(cx_ob, cy_ob, 16.0)

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("CUSP POLYNOMIAL", "f(z_1, z_2) = z_1^2 + z_2^3 = 0"),
        ("MILNOR LINK", "K = f^-1(0) intersect S^3 = T(2,3)"),
        ("OPEN-BOOK BINDING", "d(F_theta) = K_{2,3} Fixed Boundary"),
        ("FIBER PAGE GENUS", "g(F_theta) = (2-1)*(3-1)/2 = 1"),
        ("MONODROMY MATRIX", "M = [[1, -1], [1, 0]] in SL(2, Z)"),
        ("PERIODICITY ORDER", "M^6 = Identity (6-Fold Periodic)"),
        ("MODULAR EQUIV.", "S^3 \\ K_{2,3} ~= SL(2, R) / SL(2, Z)"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (POS_SAPPHIRE, "PAGE I POSITIVE NORMAL (+N) // BICOLLARED SAPPHIRE-CERULEAN SHEET (#228EFE)"),
        (NEG_CRIMSON, "PAGE I NEGATIVE NORMAL (-N) // BICOLLARED ROSE-CRIMSON SHEET (#F63080)"),
        (PAGE2_EMERALD, "PAGE II CONJUGATE (+N) // MILNOR FIBER THETA + PI EMERALD (#14E4A8)"),
        (PAGE2_VIOLET, "PAGE II CONJUGATE (-N) // MILNOR FIBER THETA + PI HELIOTROPE (#AC54FC)"),
        (BINDING_GOLD, "OPEN-BOOK BINDING K_{2,3} // BRAIDED TORUS KNOT BOUNDARY GOLD (#FCC038)"),
        (HOMOLOGY_CYAN, "FIRST HOMOLOGY GENERATOR // H_1(SIGMA; Z) BASIS CYCLE CYAN (#38E8FF)"),
    ]
    for i, (col, label) in enumerate(swatches):
        sy_s = mid_y_bot + 78 + i * 54
        py5.stroke(236, 242, 252, 90)
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
        "FIG. 05", "TORUS KNOT TAXONOMY T(p, q) ON CLIFFORD TORUS S^1 x S^1",
        "COPRIME WINDING (p, q): GENUS g = (p-1)*(q-1)/2 & CROSSING NUMBER c = MIN(p*(q-1), q*(p-1))",
        "FIG. 06", "HISTORICAL KNOT THEORY & 3-MANIFOLD TOPOLOGY LEDGER",
        "FROM GAUSS (1833) & SEIFERT (1934) TO MILNOR (1968), THURSTON (1978) & GHYS (2006)",
    )

    dx, dy = RIGHT_X + 145, CARD_Y_TOP + 215
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0, 4)

    # T(2,3) Trefoil + T(2,5) Cinquefoil miniature locus
    ts_m = np.linspace(0.0, 2.0 * np.pi, 120)
    r_m = 64.0 + 24.0 * np.cos(3.0 * ts_m + tau)
    xm = dx + r_m * np.cos(2.0 * ts_m)
    ym = dy + r_m * np.sin(2.0 * ts_m)
    segs_m = np.empty((len(ts_m) - 1, 4), dtype=np.float32)
    segs_m[:, 0], segs_m[:, 1] = xm[:-1], ym[:-1]
    segs_m[:, 2], segs_m[:, 3] = xm[1:], ym[1:]
    py5.stroke(*BINDING_GOLD)
    py5.stroke_weight(2.4)
    py5.lines(segs_m)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("T(2,3) TREFOIL", "g = 1, c = 3, |Delta(-1)| = 3"),
        ("T(2,5) CINQUEFOIL", "g = 2, c = 5, Solomon's Seal Knot"),
        ("T(3,4) TORUS KNOT", "g = 3, c = 8, Non-Alternating 8_19"),
        ("T(3,5) TORUS KNOT", "g = 4, c = 10, E_8 Poincare Sphere"),
        ("FIBEREDNESS", "All Torus Knots T(p,q) are Fibered"),
        ("FUNDAMENTAL GROUP", "<a, b | a^2 = b^3> ~= Braid Group B_3"),
        ("SEIFERT FIBRATION", "2 Exceptional Fibers of Order (2, 3)"),
    ])

    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("LINKING INTEGRAL (1833)", "Carl Friedrich Gauss", "lk(C_1, C_2)", "Electrodynamic Double Integral"),
        ("KNOT POLYNOMIAL (1928)", "James W. Alexander", "Delta_K(t)", "First Algebraic Knot Invariant"),
        ("GESCHLECHT (1934)", "Herbert Seifert", "Seifert Surface", "Bicollared Genus & Matrix V"),
        ("HYPERSURFACES (1968)", "John W. Milnor", "Open-Book S^1", "z_1^p + z_2^q = 0 Fibration"),
        ("MODULAR KNOTS (2006)", "Etienne Ghys", "Lorenz = Modular", "Geodesic Flow on SL(2,Z)\\H"),
        ("OPEN-BOOK LIVE", "K_{2,3} in S^3", "g = 1 / chi = -1", "HARMONIC MILNOR PAGE FLOW"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(22, 38, 68, 215 if is_active else 115)
        py5.stroke(254, 206, 78 if is_active else 46, 200 if is_active else 110)
        py5.stroke_weight(1.6 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(TEXT_ACCENT if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*TEXT_SECONDARY)
        py5.text(author, RIGHT_X + 245, ry + 21)
        py5.fill(56, 232, 255 if not is_active else 254)
        py5.text(metric, RIGHT_X + 430, ry + 21)
        py5.fill(*TEXT_PRIMARY)
        py5.text(desc, RIGHT_X + 595, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "BRAID GROUP B_3 CLOSURE: SIGMA_1^3 = (SIGMA_1 * SIGMA_2)^3",
        "ALEXANDER'S THEOREM: K_{2,3} AS THE CLOSED 2-STRAND BRAID sigma_1^3 WITH WRITHE w = +3",
        "FIG. 08", "MILNOR PAGE PHASE & MONODROMY ACTION OSCILLOGRAM",
        "REAL-TIME SYMPLECTIC PERIODIC MONODROMY TRACES ON H_1(F_THETA; R)",
    )

    tx, ty, tw, th = RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(tx, ty, tw, th, 4)

    # 2-Strand Braid Closure sigma_1^3
    ys_b = np.linspace(ty + 24.0, ty + th - 24.0, 72)
    ph_b = np.linspace(0.0, 3.0 * np.pi, 72) - tau
    xb1 = tx + tw * 0.5 + 48.0 * np.cos(ph_b)
    xb2 = tx + tw * 0.5 - 48.0 * np.cos(ph_b)
    segs_b1 = np.empty((len(ys_b) - 1, 4), dtype=np.float32)
    segs_b2 = np.empty((len(ys_b) - 1, 4), dtype=np.float32)
    segs_b1[:, 0], segs_b1[:, 1] = xb1[:-1], ys_b[:-1]
    segs_b1[:, 2], segs_b1[:, 3] = xb1[1:], ys_b[1:]
    segs_b2[:, 0], segs_b2[:, 1] = xb2[:-1], ys_b[:-1]
    segs_b2[:, 2], segs_b2[:, 3] = xb2[1:], ys_b[1:]
    py5.stroke(*POS_SAPPHIRE)
    py5.stroke_weight(2.6)
    py5.lines(segs_b1)
    py5.stroke(*NEG_CRIMSON)
    py5.lines(segs_b2)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("BRAID WORD", "beta = sigma_1^3 in B_2 (2-Strand)"),
        ("3-STRAND WORD", "(sigma_1 * sigma_2)^2 in B_3"),
        ("BRAID INDEX", "b(K_{2,3}) = 2 Minimal Strands"),
        ("DIAGRAM WRITHE", "w(D) = +3 Right-Handed Chiral"),
        ("SELF-LINKING", "sl(K) = w - b = 3 - 2 = +1"),
        ("MILNOR FIBER VOL.", f"A(F_theta) = {4.0 * np.pi + 0.35 * np.sin(tau):.3f} sr"),
        ("PAGE PHASE THETA", f"theta = {(tau / (2.0 * np.pi)) * 360.0:.1f} DEG mod 360"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    ox, oy, ow, oh = RIGHT_X + 28, mid_y_bot + 78, CARD_W - 56, 265.0
    py5.fill(8, 12, 24)
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
    py5.stroke(30, 44, 72)
    py5.stroke_weight(1.0)
    py5.lines(np.array(grid_segs, dtype=np.float32))

    xs_osc = np.linspace(0.0, 1.0, 160)
    x_px = ox + 16.0 + xs_osc * (ow - 32.0)

    waves = [
        (34, 142, 254, 0.0, 1.0),
        (246, 48, 128, 2.0 * np.pi / 3.0, 0.88),
        (20, 228, 168, 4.0 * np.pi / 3.0, 0.76),
    ]
    for rc, gc, bc, p_shift, amp_s in waves:
        ph_w = xs_osc * 6.0 * np.pi - 2.0 * tau + p_shift
        y_sig = (0.72 * np.sin(ph_w) + 0.28 * np.cos(3.0 * ph_w)) * (oh * 0.34 * amp_s)
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
        "SAPPHIRE: PAGE I (+N) FLUX // CRIMSON: PAGE I (-N) FLUX // EMERALD: PAGE II MONODROMY ACTION",
        ox + 4, oy + oh + 14,
    )


def draw_header_and_footer(tau):
    py5.no_fill()
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(2.0)
    py5.rect(48, 42, WIDTH - 96, HEIGHT - 84, 10)

    py5.fill(*TEXT_PRIMARY)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(26)
    py5.text(
        "SEIFERT-FIBERED TREFOIL KNOT COMPLEMENT // MILNOR OPEN-BOOK FOLIATION",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "HERBERT SEIFERT BICOLLARED GENUS-1 SURFACE (1934), MILNOR FIBRATION z_1^2 + z_2^3 = 0 (1968) & ALEXANDER INVARIANT",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "BINDING K_{2,3} = d(F_THETA) // CHI(SIGMA) = 2 - 3 = -1 (g = 1) // DELTA_K(t) = t - 1 + t^-1 // MONODROMY M^6 = I",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ALGEBRAIC & 3-MANIFOLD TOPOLOGY // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_OBSIDIAN)

    draw_header_and_footer(tau)
    draw_seifert_fibration_viewport(tau)
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

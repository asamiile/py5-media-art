"""
kinetic_nacreous_polar_stratospheric_cloud_iridescence_2d

Polar Stratospheric Cloud (PSC Type II Water-Ice & Type Ib Supercooled Ternary
Solution HNO3-H2SO4-H2O) Mother-of-Pearl Nacreous Wave-Cloud Iridescence and
Orographic Gravity Lee-Wave Stratification, inspired by Carl Stormer's 1929-1932
photogrammetric altitude surveys of Perlemorskyer (22-28 km altitude in the
Arctic polar vortex at T < 188 K), Marcel Minnaert's Light and Color in the
Outdoors (1937), Gustav Mie & George Biddell Airy's small-particle coronal
diffraction theory (I(theta) ~ [2 J_1(x sin theta) / (x sin theta)]^2), and
sublime nocturnal-twilight atmospheric color fields.
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
WORK_NAME = "kinetic_nacreous_polar_stratospheric_cloud_iridescence_2d"
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
# Color Palette — Deep Polar Vortex Twilight & Nacreous Iridescence (Dark BG)
# ---------------------------------------------------------------------------
BG_OBSIDIAN = (6, 9, 18)          # #060912 Deep Polar Vortex & Mesopause Obsidian
CARD_BG = (11, 16, 30, 236)       # Translucent Stratospheric Telemetry Slate
CARD_BORDER = (46, 68, 108)       # Subtle Instrument Frame Rule
TEXT_PRIMARY = (236, 242, 252)    # Crisp Polar Alabaster
TEXT_SECONDARY = (150, 172, 206)  # Muted Azimuth Slate
TEXT_ACCENT = (250, 204, 86)      # Stormer Theodolite Brass Gold

# Nacreous Airy-Mie Diffraction & Stratospheric Twilight Palette
NACRE_PEARL_GOLD = np.array([255.0, 244.0, 176.0], dtype=np.float32)   # 0th/1st-Order Specular Pearl Gold
NACRE_APRICOT = np.array([255.0, 152.0, 64.0], dtype=np.float32)       # Grazing Sub-Horizon Solar Coral-Amber
NACRE_MAGENTA = np.array([248.0, 58.0, 146.0], dtype=np.float32)       # 1st-Order Tourmaline Rose-Magenta
NACRE_VIOLET = np.array([172.0, 82.0, 252.0], dtype=np.float32)        # 1st/2nd-Order Heliotrope Amethyst
NACRE_CYAN = np.array([38.0, 214.0, 252.0], dtype=np.float32)         # 2nd-Order Aquamarine Cerulean
NACRE_EMERALD = np.array([16.0, 234.0, 174.0], dtype=np.float32)       # 2nd-Order Mother-of-Pearl Emerald-Teal

# 11-Stop Pure Multi-Order Airy Diffraction Spectral LUT (Zero RGB Mud/Desaturation)
# Maps normalized diffraction phase phi in [0.0 (outer veil) -> 1.0 (inner frost core)]
LUT_PHI = np.array([0.00, 0.12, 0.24, 0.36, 0.48, 0.60, 0.72, 0.82, 0.91, 1.00], dtype=np.float32)
LUT_RGB = np.array([
    [48.0, 138.0, 238.0],    # 0.00: Outer Sub-Micron Evaporation Rim Cerulean
    [168.0, 78.0, 248.0],    # 0.12: 2nd-Order Outer Heliotrope Amethyst
    [248.0, 56.0, 144.0],    # 0.24: 2nd-Order Tourmaline Rose-Magenta
    [255.0, 162.0, 72.0],    # 0.36: 2nd-Order Warm Sunset Coral-Gold
    [18.0, 236.0, 176.0],    # 0.48: 2nd-Order Vivid Mother-of-Pearl Emerald
    [36.0, 216.0, 254.0],    # 0.60: 1st/2nd-Order Aquamarine Turquoise
    [182.0, 86.0, 252.0],    # 0.72: 1st-Order Royal Orchid Violet
    [252.0, 62.0, 142.0],    # 0.82: 1st-Order Crimson-Rose Magenta Fringe
    [255.0, 212.0, 108.0],   # 0.91: 1st-Order Luminous Amber-Gold
    [255.0, 252.0, 226.0],   # 1.00: 0th-Order Specular Mother-of-Pearl Core
], dtype=np.float32)

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

SKY_BANDS_VERTS = None
SKY_BANDS_COLORS = None
MOUNTAIN_POLYS = None
LENTICULAR_CLOUDS = None
ISENTROPE_X_NORM = None


def eval_nacreous_lut(phi):
    """Map scalar diffraction phase phi in [0, 1] to pure high-chroma Mother-of-Pearl RGB."""
    phi_c = np.clip(phi, 0.0, 1.0)
    r = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 0])
    g = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 1])
    b = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 2])
    return np.stack([r, g, b], axis=-1)


def init_stratospheric_domain():
    """Precompute the twilight sky dome bands, Scandes mountain silhouette, and wave-foil cloud decks."""
    global SKY_BANDS_VERTS, SKY_BANDS_COLORS, MOUNTAIN_POLYS, LENTICULAR_CLOUDS, ISENTROPE_X_NORM

    # 1. Precompute circular-clipped horizontal sky twilight gradient bands inside R_VIEWPORT
    n_bands = 84
    r_inner = R_VIEWPORT - 12.0
    y_vals = np.linspace(CY - r_inner, CY + r_inner, n_bands + 1)

    sky_verts = []
    sky_colors = []

    # Twilight gradient stops positioned so the warm sub-horizon solar glow sits right above
    # the Scandes mountain ridge (t_norm ~ 0.58 to 0.78)!
    stops_t = np.array([0.0, 0.24, 0.44, 0.56, 0.65, 0.73, 0.80, 1.0])
    stops_rgb = np.array([
        [5.0, 8.0, 18.0],       # 0.00: Upper Mesopause Obsidian (z = 32 km)
        [10.0, 22.0, 54.0],     # 0.24: Upper Stratosphere Polar Vortex Indigo
        [18.0, 52.0, 112.0],    # 0.44: Ozone Chappuis Absorption Royal Sapphire
        [44.0, 86.0, 148.0],    # 0.56: Lower Stratosphere Twilight Cerulean
        [136.0, 64.0, 108.0],   # 0.65: Sub-Horizon Purple-Magenta Belt
        [226.0, 96.0, 56.0],    # 0.73: Grazing Solar Crimson-Coral Horizon
        [252.0, 176.0, 74.0],   # 0.80: Golden Civil Twilight Crest above Scandes
        [18.0, 14.0, 28.0],     # 1.00: Deep Valley Shadow behind Mountains
    ])

    for i in range(n_bands):
        y0 = float(y_vals[i])
        y1 = float(y_vals[i + 1])
        ym = 0.5 * (y0 + y1)
        dy0 = np.clip((y0 - CY) / r_inner, -0.9999, 0.9999)
        dy1 = np.clip((y1 - CY) / r_inner, -0.9999, 0.9999)
        x_half0 = r_inner * np.sqrt(1.0 - dy0 * dy0)
        x_half1 = r_inner * np.sqrt(1.0 - dy1 * dy1)

        t_norm = (ym - (CY - r_inner)) / (2.0 * r_inner)
        r_c = int(np.interp(t_norm, stops_t, stops_rgb[:, 0]))
        g_c = int(np.interp(t_norm, stops_t, stops_rgb[:, 1]))
        b_c = int(np.interp(t_norm, stops_t, stops_rgb[:, 2]))

        sky_verts.append([
            [CX - x_half0, y0],
            [CX + x_half0, y0],
            [CX + x_half1, y1],
            [CX - x_half1, y1],
        ])
        sky_colors.append((r_c, g_c, b_c))

    SKY_BANDS_VERTS = np.array(sky_verts, dtype=np.float32)
    SKY_BANDS_COLORS = sky_colors

    # 2. Precompute Scandes Orographic Mountain Range Silhouettes (3 layered ridges at bottom of viewport)
    ISENTROPE_X_NORM = np.linspace(-0.98, 0.98, 128)
    mountain_layers = []
    ridge_configs = [
        # Distant twilight ridge (Kebnekaise / Sarek massif)
        {"base_y_frac": 0.69, "amp": 135.0, "seed": 11, "color": (28, 32, 62, 245), "rim": (252, 168, 86, 175)},
        # Mid-ground lee-wave generator ridge (Abisko / Tornetrask)
        {"base_y_frac": 0.75, "amp": 116.0, "seed": 23, "color": (14, 18, 38, 252), "rim": (232, 122, 78, 165)},
        # Foreground basalt/granite Scandes crest
        {"base_y_frac": 0.82, "amp": 94.0, "seed": 37, "color": (6, 9, 18, 255), "rim": (168, 128, 164, 145)},
    ]

    for cfg in ridge_configs:
        xs_n = np.linspace(-0.97, 0.97, 108)
        s = cfg["seed"]
        env = (
            np.exp(-2.4 * (xs_n + 0.22) ** 2)
            + 0.82 * np.exp(-3.6 * (xs_n - 0.28) ** 2)
            + 0.42 * np.exp(-5.2 * (xs_n + 0.64) ** 2)
            + 0.38 * np.exp(-5.5 * (xs_n - 0.66) ** 2)
        )
        crags = (
            0.18 * np.sin(7.5 * xs_n + s)
            + 0.11 * np.cos(16.0 * xs_n - 0.7 * s)
            + 0.05 * np.sin(31.0 * xs_n + 1.3 * s)
        )
        h_profile = cfg["amp"] * np.clip(env + crags * env, 0.02, 1.35)

        quads = []
        rim_segs = []
        for j in range(len(xs_n) - 1):
            x0 = CX + xs_n[j] * r_inner
            x1 = CX + xs_n[j + 1] * r_inner
            y_circ0 = CY + r_inner * np.sqrt(max(0.0, 1.0 - xs_n[j] ** 2))
            y_circ1 = CY + r_inner * np.sqrt(max(0.0, 1.0 - xs_n[j + 1] ** 2))

            y_base0 = min(y_circ0, CY + cfg["base_y_frac"] * r_inner - h_profile[j])
            y_base1 = min(y_circ1, CY + cfg["base_y_frac"] * r_inner - h_profile[j + 1])

            if y_base0 < y_circ0 or y_base1 < y_circ1:
                quads.append([
                    [x0, y_base0],
                    [x1, y_base1],
                    [x1, y_circ1],
                    [x0, y_circ0],
                ])
                rim_segs.append([x0, y_base0, x1, y_base1])

        mountain_layers.append({
            "quads": np.array(quads, dtype=np.float32),
            "rim_segs": np.array(rim_segs, dtype=np.float32),
            "color": cfg["color"],
            "rim_color": cfg["rim"],
        })
    MOUNTAIN_POLYS = mountain_layers

    # 3. Precompute 7 Aerodynamic Wave-Foil Lenticular Nacreous Cloud Decks on (U, V) Grid
    # Each cloud deck uses U in [-1, 1] (streamwise airfoil axis) and V in [-1, 1] (cross-stream lamina)
    # so there is zero polar seam and every diffraction band forms a smooth winged wave-foil!
    cloud_specs = [
        # 0: High-Altitude Mesopause Precursor Veil (29.2 km, upper-right)
        {"cx_n": 0.22, "cy_n": -0.60, "half_L": 330.0, "half_H": 56.0, "tilt": -0.06, "arch": 36.0, "s_wave": 16.0, "freq": 2.4, "phase_off": 3.8, "phi_shift": 0.08, "n_u": 44, "n_v": 22},
        # 1: Upper Stratospheric PSC Type II Water-Ice Crest (27.8 km, upper-left upstream tilt)
        {"cx_n": -0.22, "cy_n": -0.46, "half_L": 430.0, "half_H": 78.0, "tilt": -0.11, "arch": 48.0, "s_wave": 22.0, "freq": 2.8, "phase_off": 1.1, "phi_shift": 0.0, "n_u": 52, "n_v": 26},
        # 2: Mid-Upper Secondary Wavelet Crest (25.8 km, right-upper)
        {"cx_n": 0.34, "cy_n": -0.26, "half_L": 350.0, "half_H": 64.0, "tilt": -0.08, "arch": 38.0, "s_wave": 18.0, "freq": 3.0, "phase_off": 2.1, "phi_shift": 0.14, "n_u": 44, "n_v": 22},
        # 3: Primary Sovereign Mother-of-Pearl Lenticular Deck (24.5 km, grand central wave foil)
        {"cx_n": -0.03, "cy_n": -0.12, "half_L": 545.0, "half_H": 102.0, "tilt": -0.09, "arch": 64.0, "s_wave": 28.0, "freq": 3.2, "phase_off": 0.0, "phi_shift": 0.02, "n_u": 60, "n_v": 30},
        # 4: Downstream Lee-Wave Harmonic Lens (23.0 km, right-mid)
        {"cx_n": 0.32, "cy_n": 0.10, "half_L": 395.0, "half_H": 74.0, "tilt": -0.07, "arch": 42.0, "s_wave": 20.0, "freq": 2.7, "phase_off": 2.7, "phi_shift": 0.06, "n_u": 48, "n_v": 24},
        # 5: Lower Stratospheric NAT / STS Type Ib Lens (21.2 km, lower-left warm twilight rim)
        {"cx_n": -0.32, "cy_n": 0.15, "half_L": 410.0, "half_H": 76.0, "tilt": -0.10, "arch": 46.0, "s_wave": 21.0, "freq": 2.6, "phase_off": 4.6, "phi_shift": 0.10, "n_u": 48, "n_v": 24},
        # 6: Lower Trailing Horizon Wavelet (19.8 km, lower-center-right above golden glow)
        {"cx_n": 0.08, "cy_n": 0.32, "half_L": 380.0, "half_H": 62.0, "tilt": -0.04, "arch": 34.0, "s_wave": 16.0, "freq": 3.1, "phase_off": 5.4, "phi_shift": 0.16, "n_u": 44, "n_v": 22},
    ]

    LENTICULAR_CLOUDS = []
    for spec in cloud_specs:
        u = np.linspace(-1.0, 1.0, spec["n_u"] + 1, dtype=np.float32)
        v = np.linspace(-1.0, 1.0, spec["n_v"] + 1, dtype=np.float32)
        U, V = np.meshgrid(u, v, indexing="ij")  # shape (n_u+1, n_v+1)
        LENTICULAR_CLOUDS.append({
            "spec": spec,
            "U": U,
            "V": V,
        })


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

    init_stratospheric_domain()
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


# ---------------------------------------------------------------------------
# Main Viewport Rendering: Polar Stratospheric Nacreous Cloud Field
# ---------------------------------------------------------------------------
def draw_nacreous_stratospheric_viewport(tau):
    r_inner = R_VIEWPORT - 12.0

    # 1. Outer Instrument Bezel & Recessed Sky Viewport
    py5.no_stroke()
    py5.fill(14, 22, 42)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    # Batch-render the 84 twilight sky dome gradient bands
    for i in range(len(SKY_BANDS_VERTS)):
        rc, gc, bc = SKY_BANDS_COLORS[i]
        py5.fill(rc, gc, bc)
        py5.begin_shape(py5.QUADS)
        py5.vertices(SKY_BANDS_VERTS[i])
        py5.end_shape()

    # Sub-horizon solar grazing glow aureole right above the Scandes mountain ridge
    solar_x = CX - 85.0 * np.cos(tau + PHASE_OFFSET)
    solar_y = CY + r_inner * 0.48
    for k in range(12, 0, -1):
        frac = k / 12.0
        py5.fill(255, 168, 76, int(22 * (1.0 - frac * 0.72)))
        py5.ellipse(solar_x, solar_y, 980.0 * frac, 340.0 * frac)

    # 2. Orographic Internal Gravity Lee-Wave Streamlines (18 Potential Temperature Isentropes)
    xs_n = ISENTROPE_X_NORM
    xs_px = CX + xs_n * r_inner
    isentrope_segs_dim = []
    isentrope_segs_bright = []

    for m_idx in range(18):
        y_frac = -0.78 + m_idx * 0.080
        z_km = 29.5 - m_idx * 0.85
        kz_phase = z_km * 0.52 - tau + PHASE_OFFSET
        wave_env = np.exp(-1.6 * (xs_n + 0.06) ** 2) + 0.58 * np.exp(-2.8 * (xs_n - 0.34) ** 2)
        dy_wave = (
            32.0 * wave_env * np.sin(5.2 * xs_n + kz_phase)
            + 13.0 * wave_env * np.cos(10.4 * xs_n - kz_phase)
        )
        ys_px = CY + y_frac * r_inner - dy_wave

        dx_c = xs_px - CX
        dy_c = ys_px - CY
        inside = (dx_c * dx_c + dy_c * dy_c) < (r_inner - 6.0) ** 2

        for j in range(len(xs_px) - 1):
            if inside[j] and inside[j + 1]:
                seg = [xs_px[j], ys_px[j], xs_px[j + 1], ys_px[j + 1]]
                if m_idx % 3 == 0:
                    isentrope_segs_bright.append(seg)
                else:
                    isentrope_segs_dim.append(seg)

    if isentrope_segs_dim:
        py5.stroke(110, 168, 238, 52)
        py5.stroke_weight(1.1)
        py5.lines(np.array(isentrope_segs_dim, dtype=np.float32))
    if isentrope_segs_bright:
        py5.stroke(168, 224, 255, 92)
        py5.stroke_weight(1.5)
        py5.lines(np.array(isentrope_segs_bright, dtype=np.float32))

    # 3. Multi-Tiered Aerodynamic Wave-Foil Nacreous Cloud Decks (Pure Spectral LUT)
    py5.no_stroke()
    glint_segs = []

    for cloud in LENTICULAR_CLOUDS:
        spec = cloud["spec"]
        U = cloud["U"]
        V = cloud["V"]
        n_u, n_v = U.shape[0] - 1, U.shape[1] - 1

        p_off = spec["phase_off"] + PHASE_OFFSET
        cx_c = CX + spec["cx_n"] * r_inner + 16.0 * np.sin(tau + p_off)
        cy_c = CY + spec["cy_n"] * r_inner + 9.0 * np.cos(tau + p_off * 1.2)

        half_L = spec["half_L"] * (1.0 + 0.03 * np.sin(tau + p_off))
        half_H = spec["half_H"] * (1.0 + 0.04 * np.cos(tau - p_off))

        # Streamwise coordinate x_local in [-half_L, +half_L]
        x_local = U * half_L

        # Lenticular airfoil envelope: tapers smoothly to sharp cusps at U = -1 and U = +1
        env_u = np.maximum(0.0, 1.0 - U * U) ** 0.82
        # Asymmetric cambered upper/lower lenticular profile (flat/concave base, domed upper crest)
        camber = -spec["arch"] * (np.maximum(0.0, 1.0 - U * U) ** 1.15) * (0.72 - 0.28 * V)
        # Sinuous S-wave undulation along the gravity wave train + internal ripple
        s_wave = (
            spec["s_wave"] * np.sin(spec["freq"] * U - tau + p_off) * (0.35 + 0.65 * env_u)
            + 6.5 * np.cos(6.0 * U + 2.0 * V + tau) * env_u
        )
        y_local = V * half_H * env_u + camber + s_wave

        tilt = spec["tilt"] + 0.016 * np.sin(tau + p_off)
        ct, st = np.cos(tilt), np.sin(tilt)
        X = cx_c + x_local * ct - y_local * st
        Y = cy_c + x_local * st + y_local * ct

        # Clip gently inside circular viewport
        d_rad = np.hypot(X - CX, Y - CY)
        max_r = r_inner - 8.0
        scale_clip = np.where(d_rad > max_r, max_r / np.maximum(d_rad, 1.0), 1.0)
        X = CX + (X - CX) * scale_clip
        Y = CY + (Y - CY) * scale_clip

        # Evaluate cell center coordinates (U_m, V_m)
        U_m = 0.25 * (U[:-1, :-1] + U[1:, :-1] + U[1:, 1:] + U[:-1, 1:])
        V_m = 0.25 * (V[:-1, :-1] + V[1:, :-1] + V[1:, 1:] + V[:-1, 1:])

        # Elliptical streamline isotherm coordinate R_iso in [0 (core), 1 (outer edge)]
        # Incorporates subtle internal wave-crest bands so the Mother-of-Pearl fringes undulate!
        R_iso = np.sqrt(0.72 * (U_m ** 2) + 1.05 * (V_m ** 2))
        wave_mod = (
            0.11 * np.sin(4.5 * U_m - tau + p_off) * (1.0 - 0.5 * (V_m ** 2))
            + 0.06 * np.cos(7.5 * V_m + tau)
        )
        phi_field = np.clip(1.06 - 0.96 * R_iso + wave_mod - spec["phi_shift"], 0.0, 1.0)

        # Quantize phi_field into 18 discrete spectral contour bands for crisp, glowing Mother-of-Pearl ribbons
        n_bands_lut = 18
        band_idx = np.clip((phi_field * n_bands_lut).astype(np.int32), 0, n_bands_lut - 1)

        X00, Y00 = X[:-1, :-1], Y[:-1, :-1]
        X10, Y10 = X[1:, :-1], Y[1:, :-1]
        X11, Y11 = X[1:, 1:], Y[1:, 1:]
        X01, Y01 = X[:-1, 1:], Y[:-1, 1:]

        for b_i in range(n_bands_lut):
            mask = band_idx == b_i
            if not np.any(mask):
                continue
            phi_val = (b_i + 0.5) / n_bands_lut
            rgb = eval_nacreous_lut(phi_val)
            # Soft translucent veil at outer rim (b_i=0), rich luminous opacity across inner iridescent bands
            alpha_val = int(np.clip(45.0 + 195.0 * (phi_val ** 0.62), 42, 236))
            py5.fill(int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha_val)

            n_q = int(np.sum(mask))
            q_verts = np.empty((n_q * 4, 2), dtype=np.float32)
            q_verts[0::4, 0], q_verts[0::4, 1] = X00[mask], Y00[mask]
            q_verts[1::4, 0], q_verts[1::4, 1] = X10[mask], Y10[mask]
            q_verts[2::4, 0], q_verts[2::4, 1] = X11[mask], Y11[mask]
            q_verts[3::4, 0], q_verts[3::4, 1] = X01[mask], Y01[mask]
            py5.begin_shape(py5.QUADS)
            py5.vertices(q_verts)
            py5.end_shape()

        # Collect delicate laminar ice-crystal streamline glints along every 4th V-streamline
        for v_i in range(2, n_v - 1, 4):
            for u_i in range(4, n_u - 4, 2):
                glint_segs.append([X[u_i, v_i], Y[u_i, v_i], X[u_i + 1, v_i], Y[u_i + 1, v_i]])

    # Render laminar ice-crystal filament striations across the nacreous clouds
    if glint_segs:
        py5.stroke(255, 250, 228, 88)
        py5.stroke_weight(1.15)
        py5.lines(np.array(glint_segs, dtype=np.float32))

    # 4. Carl Stormer Photogrammetric Triangulation Sightlines & Stratospheric Altitude Grid
    st1_x, st1_y = CX - 420.0, CY + r_inner * 0.76
    st2_x, st2_y = CX + 420.0, CY + r_inner * 0.76
    tri_segs = []
    for c_idx in [1, 3, 4]:
        spec = LENTICULAR_CLOUDS[c_idx]["spec"]
        p_off = spec["phase_off"] + PHASE_OFFSET
        tx = CX + spec["cx_n"] * r_inner + 16.0 * np.sin(tau + p_off)
        ty = CY + spec["cy_n"] * r_inner + 9.0 * np.cos(tau + p_off * 1.2) - spec["arch"] * 0.65
        tri_segs.append([st1_x, st1_y, tx, ty])
        tri_segs.append([st2_x, st2_y, tx, ty])

    py5.stroke(250, 204, 86, 82)
    py5.stroke_weight(1.2)
    py5.lines(np.array(tri_segs, dtype=np.float32))

    # 5. Scandes Orographic Mountain Range Silhouettes (3 Layered Ridges at Bottom)
    for m_layer in MOUNTAIN_POLYS:
        rc, gc, bc, ac = m_layer["color"]
        py5.no_stroke()
        py5.fill(rc, gc, bc, ac)
        py5.begin_shape(py5.QUADS)
        py5.vertices(m_layer["quads"].reshape(-1, 2))
        py5.end_shape()

        r_r, g_r, b_r, a_r = m_layer["rim_color"]
        py5.stroke(r_r, g_r, b_r, a_r)
        py5.stroke_weight(1.8)
        py5.lines(m_layer["rim_segs"])

    # Theodolite triangulation station markers on the mountain ridge
    for sx, sy in [(st1_x, st1_y), (st2_x, st2_y)]:
        py5.stroke(250, 204, 86, 225)
        py5.stroke_weight(1.8)
        py5.fill(10, 16, 32, 235)
        py5.circle(sx, sy, 14.0)
        py5.fill(250, 204, 86)
        py5.no_stroke()
        py5.circle(sx, sy, 5.0)

    # 6. Precision Brass & Azimuth Photogrammetric Bezel Ring
    py5.no_fill()
    py5.stroke(46, 68, 108)
    py5.stroke_weight(3.0)
    py5.circle(CX, CY, R_VIEWPORT * 2.0)

    py5.stroke(250, 204, 86, 195)
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
# Side Panels & 8 Atmospheric / Stratospheric Optics Apparatuses
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

    # Top Section Header
    py5.fill(*TEXT_ACCENT)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(14)
    py5.text(f"{fig_top} // {title_top}", x + 28, y + 22)
    py5.fill(*TEXT_SECONDARY)
    py5.text_size(12)
    py5.text(sub_top, x + 28, y + 44)

    # Bottom Section Header
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
        "FIG. 01", "AIRY-MIE MONODISPERSE CORONAL DIFFRACTION",
        "I(THETA) = I_0 * [2 * J_1(x * SIN(THETA)) / (x * SIN(THETA))]^2, x = 2*PI*r / LAMBDA",
        "FIG. 02", "OROGRAPHIC GRAVITY LEE-WAVE ADIABATIC COOLING",
        "SCANDES WAVE PACKET: w' -> DELTA_T = -(g/c_p)*dz < T_NAT (195 K) & T_ICE (188 K)",
    )

    # FIG. 01 Diagram: Concentric Airy Diffraction Corona Rings using pure LUT
    dx, dy = LEFT_X + 145, CARD_Y_TOP + 215
    for k in range(14, 0, -1):
        frac = k / 14.0
        phi_ring = np.mod(1.0 - frac + 0.08 * np.sin(tau), 1.0)
        rgb = eval_nacreous_lut(phi_ring)
        py5.no_stroke()
        py5.fill(int(rgb[0]), int(rgb[1]), int(rgb[2]), 210)
        py5.circle(dx, dy, frac * 196.0)
    py5.fill(255, 252, 230)
    py5.circle(dx, dy, 24.0)
    py5.no_fill()
    py5.stroke(236, 242, 252, 130)
    py5.stroke_weight(1.2)
    py5.circle(dx, dy, 198.0)

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("SCATTERING REGIME", "Monodisperse Forward Airy-Mie"),
        ("DROPLET RADIUS (r)", "1.2 - 3.2 um Spherical STS / Ice"),
        ("SIZE PARAMETER (x)", "x = 2*pi*r/lambda in [14.0, 42.0]"),
        ("SCATTERING ANGLE", "theta_scat = 8.0 - 26.0 DEG Solar"),
        ("1ST BESSEL ZERO", "u_1 = 3.8317 (1st Magenta Ring)"),
        ("2ND BESSEL ZERO", "u_2 = 7.0156 (2nd Emerald Ring)"),
        ("DISPERSION RULE", "sigma_r / <r> < 0.08 Pure Pastel"),
    ])

    # FIG. 02 Diagram: Mountain Wave Streamlines & Adiabatic Cooling Pocket
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    bx, by, bw, bh = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(8, 12, 24)
    py5.stroke(46, 68, 108)
    py5.rect(bx, by, bw, bh, 4)

    xs_m = np.linspace(0.0, 1.0, 48)
    for k in range(5):
        yk_base = by + 42.0 + k * 34.0
        crest = (26.0 - k * 2.5) * np.exp(-14.0 * (xs_m - 0.52) ** 2) * np.cos(6.0 * (xs_m - 0.52) - tau * 0.5)
        segs = []
        for j in range(len(xs_m) - 1):
            segs.append([
                bx + 12 + xs_m[j] * (bw - 24), yk_base - crest[j],
                bx + 12 + xs_m[j + 1] * (bw - 24), yk_base - crest[j + 1],
            ])
        py5.stroke(56, 189, 248, 180 if k == 1 else 100)
        py5.stroke_weight(1.5)
        py5.lines(np.array(segs, dtype=np.float32))

    # Mini nacreous cap at crest
    py5.no_stroke()
    py5.fill(172, 82, 252, 210)
    py5.ellipse(bx + bw * 0.52, by + 62.0, 112.0, 26.0)
    py5.fill(248, 58, 146, 225)
    py5.ellipse(bx + bw * 0.52, by + 61.0, 86.0, 19.0)
    py5.fill(16, 234, 174, 235)
    py5.ellipse(bx + bw * 0.52, by + 60.0, 58.0, 12.0)
    py5.fill(255, 248, 210, 245)
    py5.ellipse(bx + bw * 0.52, by + 59.0, 30.0, 6.0)

    py5.fill(36, 52, 86)
    py5.triangle(bx + 45, by + bh - 6, bx + 118, by + bh - 56, bx + 195, by + bh - 6)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("OROGRAPHIC FORCING", "Scandes Ridge (68.4 N, Abisko)"),
        ("BRUNT-VAISALA FREQ", "N = sqrt((g/theta)*dtheta/dz)"),
        ("SCORER PARAMETER", "l^2(z) = N^2 / U^2 - (1/U)d^2U/dz^2"),
        ("VERTICAL WAVELENGTH", "lambda_z = 2*pi*U / N ~ 8.4 km"),
        ("WAVE COOLING AMPL.", "Delta_T = -12.5 K at Wave Crest"),
        ("PSC NUCLEATION", "T_local = 184.2 K < T_ice (188 K)"),
        ("SUB-HORIZON SUN", "Solar Depression alpha_s = -4.2 DEG"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "POLAR VORTEX TEMPERATURE PROFILE vs. T_NAT & T_ICE",
        "RADIOSONDE SOUNDING (z = 10-32 KM): ADIABATIC WAVE PERTURBATION T(z) = T_0(z) + T'(z)",
        "FIG. 04", "MOTHER-OF-PEARL NACREOUS DIFFRACTION PALETTE",
        "1ST & 2ND ORDER AIRY SPECTRAL BANDS, OZONE CHAPPUIS INDIGO & TWILIGHT GRAZING RIM",
    )

    px, py, pw, ph = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(46, 68, 108)
    py5.rect(px, py, pw, ph, 4)

    x_nat = px + 95.0
    x_ice = px + 62.0
    py5.stroke(248, 58, 146, 160)
    py5.line(x_nat, py + 12, x_nat, py + ph - 12)
    py5.stroke(38, 214, 252, 180)
    py5.line(x_ice, py + 12, x_ice, py + ph - 12)

    zs = np.linspace(0.0, 1.0, 48)
    ts_x = (
        px + 145.0
        - 68.0 * np.exp(-9.0 * (zs - 0.36) ** 2)
        - 28.0 * np.exp(-22.0 * (zs - 0.34) ** 2) * np.cos(8.0 * zs - tau)
    )
    t_segs = []
    for j in range(len(zs) - 1):
        t_segs.append([ts_x[j], py + 14 + zs[j] * (ph - 28), ts_x[j + 1], py + 14 + zs[j + 1] * (ph - 28)])
    py5.stroke(255, 244, 176)
    py5.stroke_weight(2.0)
    py5.lines(np.array(t_segs, dtype=np.float32))

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("POLAR VORTEX CORE", "T_synoptic = 193.5 K at 30 hPa"),
        ("NAT THRESHOLD", "T_NAT = 195.2 K (HNO3 . 3H2O)"),
        ("STS DROPLET ZONE", "T_STS = 191.4 K Ternary Solution"),
        ("WATER-ICE FROST PT", "T_ice = 188.0 K (Type II Nacreous)"),
        ("WAVE MINIMUM TEMP", f"T_min = {184.2 + 1.1 * np.sin(tau):.1f} K at z = 24.5 km"),
        ("ALTITUDE STRATUM", "z = 21.0 - 28.5 km Lower Strat."),
        ("OZONE CHAPPUIS BAND", "550 - 650 nm Twilight Filtering"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (NACRE_PEARL_GOLD, "0TH-ORDER SPECULAR PEARL GOLD // MONODISPERSE ICE CORE AUREOLE (r = 3.1 um)"),
        (NACRE_MAGENTA, "1ST-ORDER TOURMALINE ROSE-MAGENTA // AIRY BESSEL DIFFRACTION FRINGE (580-640 nm)"),
        (NACRE_EMERALD, "2ND-ORDER MOTHER-OF-PEARL EMERALD // CONSTRUCTIVE GREEN-TEAL LAMINA (515-545 nm)"),
        (NACRE_CYAN, "2ND-ORDER AQUAMARINE CERULEAN // HIGH-ALTITUDE ICE STREAMLINE RIM (465-495 nm)"),
        (NACRE_VIOLET, "1ST/2ND-ORDER HELIOTROPE AMETHYST // SUPERCOOLED TERNARY SOLUTION (STS) VEIL"),
        (NACRE_APRICOT, "SUB-HORIZON SOLAR GRAZING CORAL // -4.2 DEG DEPRESSION STRATOSPHERIC RAY"),
    ]
    for i, (col, label) in enumerate(swatches):
        sy = mid_y_bot + 78 + i * 54
        py5.stroke(236, 242, 252, 90)
        py5.stroke_weight(1.2)
        py5.fill(int(col[0]), int(col[1]), int(col[2]))
        py5.rect(LEFT_X + 28, sy, 48, 34, 4)
        py5.fill(*TEXT_PRIMARY)
        py5.no_stroke()
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(label, LEFT_X + 94, sy + 17)


def draw_right_cards(tau):
    # --- TOP-RIGHT CARD: FIG. 05 & FIG. 06 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_TOP, CARD_W, CARD_H_TOP,
        "FIG. 05", "POLAR STRATOSPHERIC CLOUD (PSC) MICROPHYSICAL TAXONOMY",
        "TYPE Ia (CRYSTALLINE NAT), TYPE Ib (LIQUID STS DROPLETS) & TYPE II (HEXAGONAL WATER ICE)",
        "FIG. 06", "HISTORICAL HIGH-ALTITUDE CLOUD & OPTICS OBSERVATION LEDGER",
        "FROM MOHN (1871) & STORMER (1929) TO MINNAERT (1937) & POLAR VORTEX LIDAR",
    )

    dx, dy = RIGHT_X + 145, CARD_Y_TOP + 215
    py5.fill(8, 12, 24)
    py5.stroke(46, 68, 108)
    py5.rect(RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0, 4)

    py5.no_stroke()
    py5.fill(248, 58, 146, 115)
    py5.circle(dx - 48, dy - 38, 76.0)
    py5.fill(16, 234, 174, 185)
    py5.circle(dx - 48, dy - 38, 48.0)
    py5.fill(255, 244, 176, 245)
    py5.circle(dx - 48, dy - 38, 22.0)

    hx, hy, hr = dx + 48, dy + 36, 46.0
    hex_pts = [[hx + hr * np.cos(k * np.pi / 3.0 + tau * 0.25), hy + hr * np.sin(k * np.pi / 3.0 + tau * 0.25)] for k in range(6)]
    py5.stroke(38, 214, 252, 235)
    py5.stroke_weight(2.0)
    py5.fill(38, 214, 252, 85)
    py5.begin_shape()
    for pt in hex_pts:
        py5.vertex(pt[0], pt[1])
    py5.end_shape(py5.CLOSE)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("PSC TYPE Ia (NAT)", "Crystalline HNO3.3H2O (r ~ 5-10 um)"),
        ("PSC TYPE Ib (STS)", "Supercooled H2SO4-HNO3-H2O (1-2 um)"),
        ("PSC TYPE II (ICE)", "Monodisperse H2O Ice (1.5-3.5 um)"),
        ("DEPOLARIZATION RATIO", "delta_L < 0.01 (Ib) vs 0.35 (II)"),
        ("COOLING RATE dT/dt", "> 15 K/hr in Orographic Gravity Wave"),
        ("IRIDESCENCE PURITY", "Type Ib + II Narrow Size Spectrum"),
        ("TWILIGHT GEOMETRY", "Forward Scatter Near Solar Azimuth"),
    ])

    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("CHRISTIANIA (1871)", "Henrik Mohn", "23-26 km Est.", "First Nacreous Monograph"),
        ("OSLO NETWORK (1929)", "Carl Stormer", "24.8 km Triang.", "Dual-Camera Photogrammetry"),
        ("OPTICS TREATISE (1937)", "Marcel Minnaert", "Airy Corona", "Monodisperse Diffraction"),
        ("WAVE THEORY (1949)", "R. S. Scorer", "Lee Parameter l^2", "Trapped Mountain Waves"),
        ("STS DISCOVERY (1994)", "Carslaw & Tabazadeh", "Ternary Liquid", "Type Ib Supercooled STS"),
        ("ABISKO VORTEX LIVE", "68.35 N / 24.5 km", "T_min = 184.2 K", "HARMONIC WAVE IRIDESCENCE"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(24, 38, 68, 210 if is_active else 115)
        py5.stroke(250, 204, 86 if is_active else 46, 190 if is_active else 110)
        py5.stroke_weight(1.5 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(TEXT_ACCENT if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*TEXT_SECONDARY)
        py5.text(author, RIGHT_X + 235, ry + 21)
        py5.fill(38, 214, 252 if not is_active else 254)
        py5.text(metric, RIGHT_X + 425, ry + 21)
        py5.fill(*TEXT_PRIMARY)
        py5.text(desc, RIGHT_X + 595, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "CARL STORMER PARALLACTIC PHOTOGRAMMETRY TRIANGULATION",
        "DUAL-STATION BASELINE B = 48.2 KM: ALTITUDE Z = B * SIN(ALPHA_1)*SIN(ALPHA_2) / SIN(DELTA_ALPHA)",
        "FIG. 08", "SPECTRAL AIRY INTENSITY & GRAVITY WAVE PHASE OSCILLOGRAM",
        "REAL-TIME RGB CORONAL DIFFRACTION ENVELOPE & ADIABATIC STREAMLINE DISPLACEMENT",
    )

    tx, ty, tw, th = RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(46, 68, 108)
    py5.rect(tx, ty, tw, th, 4)

    s1x, s1y = tx + 32.0, ty + th - 26.0
    s2x, s2y = tx + tw - 48.0, ty + th - 26.0
    px_t = tx + tw * 0.56 + 18.0 * np.sin(tau)
    py_t = ty + 48.0 + 10.0 * np.cos(tau)

    py5.stroke(150, 172, 206, 160)
    py5.line(s1x, s1y, s2x, s2y)
    py5.stroke(250, 204, 86, 220)
    py5.line(s1x, s1y, px_t, py_t)
    py5.stroke(38, 214, 252, 220)
    py5.line(s2x, s2y, px_t, py_t)
    py5.stroke(248, 58, 146, 180)
    py5.line(px_t, py_t, px_t, s1y)

    py5.no_stroke()
    py5.fill(248, 58, 146)
    py5.ellipse(px_t, py_t, 52.0, 14.0)
    py5.fill(255, 244, 176)
    py5.circle(s1x, s1y, 8.0)
    py5.circle(s2x, s2y, 8.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("STATION I (ABISKO)", "68.35 N, 18.82 E (Elev 388 m)"),
        ("STATION II (KIRUNA)", "67.85 N, 20.22 E (Elev 450 m)"),
        ("BASELINE LENGTH (B)", "B = 48.24 km Geodesic Arc"),
        ("PARALLAX ANGLE", f"Delta_alpha = {11.4 + 0.6 * np.sin(tau):.2f} DEG"),
        ("TRIANGULATED HEIGHT", f"Z_cloud = {24.6 + 0.4 * np.cos(tau):.2f} km ASL"),
        ("DRIFT VELOCITY", "V_drift = 64.0 m/s WNW Jet"),
        ("WAVE STATIONARITY", "Phase Locked to Mountain Crest"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    ox, oy, ow, oh = RIGHT_X + 28, mid_y_bot + 78, CARD_W - 56, 265.0
    py5.fill(8, 12, 24)
    py5.stroke(46, 68, 108)
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
        (248, 58, 146, 0.0, 1.0),
        (16, 234, 174, 1.15, 0.88),
        (38, 214, 252, 2.30, 0.78),
    ]
    for rc, gc, bc, p_shift, amp_s in waves:
        u_arg = 2.2 + xs_osc * 11.5
        env_decay = np.exp(-1.1 * xs_osc)
        y_sig = env_decay * np.cos(u_arg * 1.25 - tau + p_shift) * (oh * 0.36 * amp_s)
        y_px = oy + oh * 0.52 - y_sig
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
        "MAGENTA: 645 nm 1ST-ORDER // EMERALD: 532 nm 2ND-ORDER // CYAN: 448 nm CORONAL INTERFERENCE",
        ox + 4, oy + oh + 14,
    )


def draw_header_and_footer(tau):
    py5.no_fill()
    py5.stroke(46, 68, 108)
    py5.stroke_weight(2.0)
    py5.rect(48, 42, WIDTH - 96, HEIGHT - 84, 10)

    py5.fill(*TEXT_PRIMARY)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(26)
    py5.text(
        "POLAR STRATOSPHERIC CLOUD (PSC TYPE II) // NACREOUS WAVE IRIDESCENCE",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "CARL STORMER PARALLACTIC PHOTOGRAMMETRY (1929), AIRY-MIE MONODISPERSE CORONAL DIFFRACTION & OROGRAPHIC LEE WAVES",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "STRATOSPHERIC ALTITUDE z = 21.0 - 28.5 KM // T_MIN = 184.2 K < T_ICE (188.0 K) // SCANDES MOUNTAIN LEE-WAVE PACKET (68.4 N)",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K ATMOSPHERIC COLOR FIELD // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_OBSIDIAN)

    draw_header_and_footer(tau)
    draw_nacreous_stratospheric_viewport(tau)
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

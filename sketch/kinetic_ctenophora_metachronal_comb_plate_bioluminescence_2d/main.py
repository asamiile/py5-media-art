"""
kinetic_ctenophora_metachronal_comb_plate_bioluminescence_2d

Bathypelagic Ctenophore (Beroe / Mnemiopsis / Mertensia) 8-Row Metachronal
Comb-Plate (Ctene) Ciliary Propulsion, 2D Hexagonal Ciliary Photonic-Crystal
Rainbow Diffraction Iridescence, and Ca2+-Activated Photoprotein (Mnemiopsin /
Berovin, 488 nm) Gastrovascular Bioluminescence, inspired by Ernst Haeckel's
Kunstformen der Natur Plate 27 (Ctenophora, 1904), Carl Chun's Die Ctenophoren
des Golfes von Neapel (1880), and G. I. Taylor's low-Reynolds-number metachronal
ciliary hydrodynamics.
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
WORK_NAME = "kinetic_ctenophora_metachronal_comb_plate_bioluminescence_2d"
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
# Color Palette — Bathypelagic Darkfield Obsidian & Ctene Bragg Iridescence
# ---------------------------------------------------------------------------
BG_OBSIDIAN = (6, 9, 18)          # #060912 Deep Bathypelagic Darkfield Obsidian
CARD_BG = (11, 16, 30, 236)       # Translucent Pelagic Telemetry Slate
CARD_BORDER = (44, 68, 108)       # Instrument Frame Rule
TEXT_PRIMARY = (236, 242, 252)    # Crisp Alabaster White
TEXT_SECONDARY = (148, 172, 206)  # Muted Pelagic Slate
TEXT_ACCENT = (42, 218, 252)      # Bioluminescent Mnemiopsin Cyan

# Curated Palette Swatches
BIOLUM_CYAN = np.array([24.0, 218.0, 254.0], dtype=np.float32)       # 488 nm Photoprotein Peak Cyan
BIOLUM_VIRIDIAN = np.array([20.0, 242.0, 178.0], dtype=np.float32)   # 508 nm GFP/Coelenterazine Emerald
BRAGG_RUBY = np.array([250.0, 52.0, 138.0], dtype=np.float32)        # Ctene Power-Stroke Bragg Ruby-Magenta
BRAGG_GOLD = np.array([255.0, 208.0, 74.0], dtype=np.float32)        # Ctene Mid-Stroke Bragg Amber-Gold
BRAGG_VIOLET = np.array([174.0, 82.0, 254.0], dtype=np.float32)      # Ctene Recovery-Stroke Bragg Heliotrope
MESOGLEA_SAPPHIRE = np.array([34.0, 96.0, 212.0], dtype=np.float32)  # Hyaline Mesoglea Bell Sapphire

# 9-Stop Pure Bragg Ciliary Grating Diffraction LUT (lambda = 2 * d * n * sin(theta))
LUT_PHI = np.array([0.00, 0.14, 0.28, 0.42, 0.56, 0.70, 0.84, 1.00], dtype=np.float32)
LUT_RGB = np.array([
    [156.0, 74.0, 252.0],    # 0.00: Short-Wave Recovery Stroke Violet (420 nm)
    [36.0, 148.0, 254.0],    # 0.14: Deep Pelagic Sapphire-Blue (460 nm)
    [22.0, 226.0, 252.0],    # 0.28: Bioluminescent Electric Cyan (490 nm)
    [18.0, 244.0, 168.0],    # 0.42: Vivid Bragg Emerald-Viridian (525 nm)
    [186.0, 248.0, 78.0],    # 0.56: Chartreuse-Lime Diffraction Crest (555 nm)
    [255.0, 206.0, 68.0],    # 0.70: Golden-Amber Power Stroke (585 nm)
    [254.0, 98.0, 64.0],     # 0.84: Vermilion-Coral Bragg Peak (620 nm)
    [250.0, 48.0, 142.0],    # 1.00: Max-Angle Ruby-Magenta Fringe (660 nm)
], dtype=np.float32)

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

N_ROWS = 8
N_CTENES_PER_ROW = 34
ROW_X_FACTORS = np.array([-0.88, -0.62, -0.34, -0.11, 0.11, 0.34, 0.62, 0.88], dtype=np.float32)
ROW_IS_SUBTENTACULAR = np.array([True, False, False, True, True, False, False, True])


def eval_bragg_lut(phi):
    phi_c = np.mod(phi, 1.0)
    r = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 0])
    g = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 1])
    b = np.interp(phi_c, LUT_PHI, LUT_RGB[:, 2])
    return np.stack([r, g, b], axis=-1)


def ctenophore_bell_half_width(s_norm, tau):
    """
    Half-width R(s) of the ctenophore body bell from s=0 (aboral statocyst crown)
    to s=1 (oral lobes), with gentle peristaltic swimming undulation.
    """
    bell = (
        445.0 * (np.sin(np.clip(s_norm * 0.90 + 0.05, 0.0, 1.0) * np.pi) ** 0.68)
        + 62.0 * np.exp(-16.0 * (s_norm - 0.80) ** 2)
    )
    pulse = 1.0 + 0.026 * np.sin(tau - 3.0 * s_norm + PHASE_OFFSET)
    return bell * pulse


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

    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


# ---------------------------------------------------------------------------
# Main Viewport: Bathypelagic Ctenophore & 8 Metachronal Comb Rows
# ---------------------------------------------------------------------------
def draw_ctenophore_viewport(tau):
    r_inner = R_VIEWPORT - 12.0

    # 1. Outer Instrument Bezel & Deep Bathypelagic Darkfield Background
    py5.no_stroke()
    py5.fill(14, 22, 42)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    py5.fill(5, 8, 18)
    py5.circle(CX, CY, R_VIEWPORT * 2.0)

    # Subtle darkfield condenser ring illumination & concentric pelagic scale rings
    for k in range(8, 0, -1):
        frac = k / 8.0
        py5.fill(14, 30, 64, int(19 * (1.0 - frac * 0.7)))
        py5.circle(CX, CY - 25.0, R_VIEWPORT * 1.85 * frac)

    py5.no_fill()
    py5.stroke(24, 46, 86, 95)
    py5.stroke_weight(1.1)
    for r_g in [220.0, 420.0, 610.0, 755.0]:
        py5.circle(CX, CY, r_g * 2.0)

    # Vertical body axis from Aboral Pole (y_aboral) to Oral Lobe Rim (y_oral)
    y_aboral = CY - 555.0
    y_oral = CY + 455.0
    body_H = y_oral - y_aboral

    # 2. Twin Retractile Tentacles & Feathered Colloblast Tentilla Plumes
    # Arch gracefully from internal tentacle bulbs (s ~ 0.32), sweeping out to r ~ 690 px
    # and curling inward beneath the oral pole without ever hitting the outer viewport clamp!
    tentacle_segs_main = []
    tentacle_segs_tentilla = []
    colloblast_dots = []

    for side in [-1.0, 1.0]:
        n_t = 76
        ts = np.linspace(0.0, 1.0, n_t)
        x_bulb = CX + side * 155.0
        y_bulb = y_aboral + 0.34 * body_H

        # Smooth inward-curling lyrical S-plume staying comfortably inside r < 730 px
        arch_out = 485.0 * np.sin(ts * np.pi * 0.82) * (1.0 - 0.24 * ts)
        wave_lat = 34.0 * np.sin(5.0 * ts - tau + side * 0.8) * (ts ** 0.7)
        tx = x_bulb + side * (arch_out + wave_lat)
        ty = (
            y_bulb
            - 195.0 * np.sin(ts * np.pi * 0.45) * (1.0 - ts)
            + 780.0 * (ts ** 1.32)
            + 24.0 * np.cos(4.5 * ts - tau) * ts
        )

        for j in range(n_t - 1):
            tentacle_segs_main.append([tx[j], ty[j], tx[j + 1], ty[j + 1]])
            if j >= 6:
                dx_t = tx[j + 1] - tx[j]
                dy_t = ty[j + 1] - ty[j]
                norm_l = max(np.hypot(dx_t, dy_t), 1e-4)
                # Outward normal along the convex edge of the tentacle
                nx, ny = side * dy_t / norm_l, -side * dx_t / norm_l
                len_b = (26.0 + 38.0 * np.sin(ts[j] * np.pi)) * (0.72 + 0.28 * np.sin(j * 0.55 - tau * 2.0))
                bx1 = tx[j] + nx * len_b * 0.55
                by1 = ty[j] + ny * len_b * 0.55 + 10.0 * np.sin(j * 0.4 - tau)
                bx2 = bx1 + nx * len_b * 0.50 + side * 12.0 * np.cos(j * 0.4 - tau)
                by2 = by1 + ny * len_b * 0.50 + 14.0
                tentacle_segs_tentilla.append([tx[j], ty[j], bx1, by1])
                tentacle_segs_tentilla.append([bx1, by1, bx2, by2])
                if j % 2 == 0:
                    colloblast_dots.append([bx2, by2])

    if tentacle_segs_tentilla:
        py5.stroke(42, 206, 254, 130)
        py5.stroke_weight(1.35)
        py5.lines(np.array(tentacle_segs_tentilla, dtype=np.float32))
    if tentacle_segs_main:
        py5.stroke(136, 240, 255, 220)
        py5.stroke_weight(2.8)
        py5.lines(np.array(tentacle_segs_main, dtype=np.float32))

    if colloblast_dots:
        py5.no_stroke()
        py5.fill(186, 248, 255, 195)
        c_arr = np.array(colloblast_dots, dtype=np.float32)
        q_col = np.empty((len(c_arr) * 4, 2), dtype=np.float32)
        r_d = 2.4
        q_col[0::4, 0], q_col[0::4, 1] = c_arr[:, 0] - r_d, c_arr[:, 1] - r_d
        q_col[1::4, 0], q_col[1::4, 1] = c_arr[:, 0] + r_d, c_arr[:, 1] - r_d
        q_col[2::4, 0], q_col[2::4, 1] = c_arr[:, 0] + r_d, c_arr[:, 1] + r_d
        q_col[3::4, 0], q_col[3::4, 1] = c_arr[:, 0] - r_d, c_arr[:, 1] + r_d
        py5.begin_shape(py5.QUADS)
        py5.vertices(q_col)
        py5.end_shape()

    # 3. Hyaline Gelatinous Mesoglea Bell & Sculpted Haeckel Bilobed Oral Curtains
    n_bell = 68
    s_vals = np.linspace(0.0, 1.0, n_bell + 1)
    r_vals = ctenophore_bell_half_width(s_vals, tau)
    y_vals = y_aboral + s_vals * body_H
    sway_all = 9.0 * np.sin(tau + 2.2 * s_vals) * (s_vals ** 1.2)

    # Bilobed oral arch indentation at the bottom of the bell
    py5.no_stroke()
    for scale_w, col_rgba in [
        (1.00, (16, 46, 102, 62)),
        (0.91, (24, 72, 146, 52)),
        (0.76, (18, 114, 186, 42)),
        (0.52, (16, 158, 214, 34)),
    ]:
        py5.fill(*col_rgba)
        q_bell = np.empty((n_bell * 4, 2), dtype=np.float32)
        x_left = CX - r_vals * scale_w + sway_all
        x_right = CX + r_vals * scale_w + sway_all
        q_bell[0::4, 0], q_bell[0::4, 1] = x_left[:-1], y_vals[:-1]
        q_bell[1::4, 0], q_bell[1::4, 1] = x_right[:-1], y_vals[:-1]
        q_bell[2::4, 0], q_bell[2::4, 1] = x_right[1:], y_vals[1:]
        q_bell[3::4, 0], q_bell[3::4, 1] = x_left[1:], y_vals[1:]
        py5.begin_shape(py5.QUADS)
        py5.vertices(q_bell)
        py5.end_shape()

    # Sculpted Twin Oral Lobes & 4 Sinuous Ciliated Auricle Ribbons (Haeckel Plate 27 style)
    auricle_lines = []
    for side in [-1.0, 1.0]:
        u_lobe = np.linspace(0.0, 1.0, 44)
        ang_l = u_lobe * np.pi
        lx_c = CX + side * 168.0 + sway_all[-1]
        ly_c = y_oral - 42.0
        rx_out = 168.0 * (1.0 - 0.12 * np.cos(2.0 * ang_l))
        ry_out = (165.0 + 14.0 * np.sin(tau + side)) * (0.85 + 0.22 * np.sin(ang_l))

        x_out = lx_c + side * np.cos(ang_l - np.pi * 0.5) * rx_out * 0.45 + np.cos(ang_l) * rx_out * 0.85
        y_out = ly_c + np.sin(ang_l) * ry_out
        x_in = lx_c + np.cos(ang_l) * (rx_out * 0.48)
        y_in = ly_c + np.sin(ang_l) * (ry_out * 0.36)

        lobe_quads = []
        for j in range(len(u_lobe) - 1):
            lobe_quads.append([[x_in[j], y_in[j]], [x_out[j], y_out[j]], [x_out[j + 1], y_out[j + 1]], [x_in[j + 1], y_in[j + 1]]])
            auricle_lines.append([x_out[j], y_out[j], x_out[j + 1], y_out[j + 1]])

        py5.no_stroke()
        py5.fill(26, 138, 218, 78)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(lobe_quads, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

        # Inner Ribbon Auricles (Ciliated sensory/feeding appendages flanking the mouth)
        u_aur = np.linspace(0.0, 1.0, 32)
        ax = CX + side * (58.0 + 78.0 * np.sin(u_aur * np.pi) + 12.0 * np.cos(3.0 * u_aur * np.pi - tau))
        ay = y_oral - 65.0 + 135.0 * np.sin(u_aur * np.pi * 0.85)
        for j in range(len(u_aur) - 1):
            auricle_lines.append([ax[j], ay[j], ax[j + 1], ay[j + 1]])

    if auricle_lines:
        py5.stroke(86, 228, 255, 185)
        py5.stroke_weight(2.2)
        py5.lines(np.array(auricle_lines, dtype=np.float32))

    # Outer hyaline ectoderm rim contour lines
    rim_segs = []
    for j in range(n_bell):
        rim_segs.append([
            CX - r_vals[j] + sway_all[j], y_vals[j],
            CX - r_vals[j + 1] + sway_all[j + 1], y_vals[j + 1],
        ])
        rim_segs.append([
            CX + r_vals[j] + sway_all[j], y_vals[j],
            CX + r_vals[j + 1] + sway_all[j + 1], y_vals[j + 1],
        ])
    py5.stroke(92, 206, 255, 185)
    py5.stroke_weight(2.2)
    py5.lines(np.array(rim_segs, dtype=np.float32))

    # 4. Internal Stomodeum (Pharynx), Infundibulum & Branching Adradial Canals
    # Translucent axial pharynx spindle from y_oral up to infundibulum at s_norm = 0.28
    y_infund = y_aboral + 0.28 * body_H
    n_ph = 36
    u_ph = np.linspace(0.0, 1.0, n_ph + 1)
    y_ph = y_infund + u_ph * (y_oral - 30.0 - y_infund)
    w_ph = 46.0 * np.sin(u_ph * np.pi) * (1.0 + 0.08 * np.cos(4.0 * u_ph * np.pi - tau))
    sway_ph = 6.0 * np.sin(tau + 2.0 * u_ph)

    q_ph = np.empty((n_ph * 4, 2), dtype=np.float32)
    q_ph[0::4, 0], q_ph[0::4, 1] = CX - w_ph[:-1] + sway_ph[:-1], y_ph[:-1]
    q_ph[1::4, 0], q_ph[1::4, 1] = CX + w_ph[:-1] + sway_ph[:-1], y_ph[:-1]
    q_ph[2::4, 0], q_ph[2::4, 1] = CX + w_ph[1:] + sway_ph[1:], y_ph[1:]
    q_ph[3::4, 0], q_ph[3::4, 1] = CX - w_ph[1:] + sway_ph[1:], y_ph[1:]
    py5.no_stroke()
    py5.fill(24, 184, 238, 68)
    py5.begin_shape(py5.QUADS)
    py5.vertices(q_ph)
    py5.end_shape()

    # Twin Tentacle Bulbs flanking the stomodeum
    for side in [-1.0, 1.0]:
        bx_bulb = CX + side * 155.0
        by_bulb = y_aboral + 0.34 * body_H
        py5.fill(38, 224, 254, 145)
        py5.ellipse(bx_bulb, by_bulb, 28.0, 68.0)
        py5.fill(255, 238, 152, 220)
        py5.ellipse(bx_bulb, by_bulb, 12.0, 36.0)

    # Precompute the 8 Meridian Comb Row (Costae) Spine Curves & Bioluminescent Pulses
    s_ctene = np.linspace(0.05, 0.93, N_CTENES_PER_ROW)
    r_ctene_bell = ctenophore_bell_half_width(s_ctene, tau)
    y_ctene_base = y_aboral + s_ctene * body_H
    sway_ctene = 9.0 * np.sin(tau + 2.2 * s_ctene) * (s_ctene ** 1.2)

    canal_segs_base = []
    canal_segs_glow = []
    furrow_segs = []
    adradial_segs = []

    n_bragg_bins = 16
    ctene_quads_by_bin = [[] for _ in range(n_bragg_bins)]
    ctene_cilia_lines = []
    basal_cushion_quads = []

    for m_row in range(N_ROWS):
        xf = float(ROW_X_FACTORS[m_row])
        is_subtent = bool(ROW_IS_SUBTENTACULAR[m_row])
        row_phase = 0.0 if is_subtent else np.pi * 0.5

        x_row = CX + xf * r_ctene_bell + sway_ctene
        y_row = y_ctene_base - 18.0 * (1.0 - xf * xf) * np.sin(s_ctene * np.pi)

        # Ciliated groove (pacemaker furrow) from apical statocyst (CX, y_aboral) to top of comb row
        furrow_segs.append([CX, y_aboral, x_row[0], y_row[0]])

        # Adradial endodermal canal branching from central Infundibulum (CX, y_infund) to mid-upper row (k=8)
        adradial_segs.append([CX, y_infund, x_row[8], y_row[8]])

        for k in range(N_CTENES_PER_ROW - 1):
            seg = [x_row[k], y_row[k], x_row[k + 1], y_row[k + 1]]
            canal_segs_base.append(seg)
            ca_wave = np.sin(2.0 * tau - 0.32 * k + m_row * 0.7)
            if ca_wave > 0.22:
                canal_segs_glow.append(seg)

        dx_ds = np.gradient(x_row)
        dy_ds = np.gradient(y_row)
        ds_len = np.maximum(np.hypot(dx_ds, dy_ds), 1e-4)
        tx_u = dx_ds / ds_len
        ty_u = dy_ds / ds_len
        out_sign = -1.0 if xf < 0 else 1.0
        nx_u = out_sign * ty_u * (0.48 + 0.52 * abs(xf))
        ny_u = -out_sign * tx_u * (0.48 + 0.52 * abs(xf))

        for k in range(N_CTENES_PER_ROW):
            meta_phase = 3.0 * tau - 0.48 * k + row_phase + PHASE_OFFSET
            stroke_sin = np.sin(meta_phase)
            stroke_cos = np.cos(meta_phase)

            paddle_len = (28.0 + 18.0 * np.sin(s_ctene[k] * np.pi)) * (0.74 + 0.26 * abs(xf))
            paddle_w = 5.8 + 3.0 * (1.0 - 0.4 * abs(xf))

            bx0 = x_row[k] - tx_u[k] * (paddle_w * 0.5)
            by0 = y_row[k] - ty_u[k] * (paddle_w * 0.5)
            bx1 = x_row[k] + tx_u[k] * (paddle_w * 0.5)
            by1 = y_row[k] + ty_u[k] * (paddle_w * 0.5)

            # Transverse basal comb cushion (polster) bar
            cw_bar = 8.0 + 6.0 * (1.0 - 0.5 * abs(xf))
            basal_cushion_quads.append([
                [x_row[k] - nx_u[k] * cw_bar, y_row[k] - ny_u[k] * cw_bar - 2.2],
                [x_row[k] + nx_u[k] * 4.0, y_row[k] + ny_u[k] * 4.0 - 2.2],
                [x_row[k] + nx_u[k] * 4.0, y_row[k] + ny_u[k] * 4.0 + 2.2],
                [x_row[k] - nx_u[k] * cw_bar, y_row[k] - ny_u[k] * cw_bar + 2.2],
            ])

            sweep_tangent = -0.78 * stroke_sin - 0.22 * (stroke_cos ** 2)
            sweep_normal = 0.88 + 0.25 * stroke_cos

            mx_dir = nx_u[k] * sweep_normal + tx_u[k] * sweep_tangent
            my_dir = ny_u[k] * sweep_normal + ty_u[k] * sweep_tangent
            m_norm = max(np.hypot(mx_dir, my_dir), 1e-4)
            mx_dir /= m_norm
            my_dir /= m_norm

            bend = 0.42 * max(0.0, -stroke_cos)
            tx_dir = mx_dir * np.cos(bend) - out_sign * my_dir * np.sin(bend)
            ty_dir = mx_dir * np.sin(bend) + out_sign * my_dir * np.cos(bend)

            m0x = bx0 + mx_dir * (paddle_len * 0.52)
            m0y = by0 + my_dir * (paddle_len * 0.52)
            m1x = bx1 + mx_dir * (paddle_len * 0.52)
            m1y = by1 + my_dir * (paddle_len * 0.52)

            flare = 1.40
            t0x = m0x + tx_dir * (paddle_len * 0.48) - tx_u[k] * (paddle_w * 0.25 * flare)
            t0y = m0y + ty_dir * (paddle_len * 0.48) - ty_u[k] * (paddle_w * 0.25 * flare)
            t1x = m1x + tx_dir * (paddle_len * 0.48) + tx_u[k] * (paddle_w * 0.25 * flare)
            t1y = m1y + ty_dir * (paddle_len * 0.48) + ty_u[k] * (paddle_w * 0.25 * flare)

            phi_bragg = np.mod(0.5 + 0.48 * stroke_sin + 0.12 * s_ctene[k] + 0.06 * m_row, 1.0)
            bin_i = int(np.clip(phi_bragg * n_bragg_bins, 0, n_bragg_bins - 1))
            bin_i_tip = (bin_i + 2) % n_bragg_bins

            ctene_quads_by_bin[bin_i].append([[bx0, by0], [bx1, by1], [m1x, m1y], [m0x, m0y]])
            ctene_quads_by_bin[bin_i_tip].append([[m0x, m0y], [m1x, m1y], [t1x, t1y], [t0x, t0y]])

            cx_b, cy_b = 0.5 * (bx0 + bx1), 0.5 * (by0 + by1)
            cx_t, cy_t = 0.5 * (t0x + t1x), 0.5 * (t0y + t1y)
            ctene_cilia_lines.append([cx_b, cy_b, cx_t, cy_t])

    if adradial_segs:
        py5.stroke(34, 168, 232, 130)
        py5.stroke_weight(2.0)
        py5.lines(np.array(adradial_segs, dtype=np.float32))
    if furrow_segs:
        py5.stroke(250, 208, 92, 195)
        py5.stroke_weight(1.7)
        py5.lines(np.array(furrow_segs, dtype=np.float32))
    if canal_segs_base:
        py5.stroke(24, 118, 196, 165)
        py5.stroke_weight(3.0)
        py5.lines(np.array(canal_segs_base, dtype=np.float32))
    if canal_segs_glow:
        py5.stroke(46, 242, 255, 245)
        py5.stroke_weight(4.8)
        py5.lines(np.array(canal_segs_glow, dtype=np.float32))

    if basal_cushion_quads:
        py5.no_stroke()
        py5.fill(38, 246, 224, 215)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(basal_cushion_quads, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

    py5.no_stroke()
    for b_i in range(n_bragg_bins):
        q_list = ctene_quads_by_bin[b_i]
        if not q_list:
            continue
        phi_v = (b_i + 0.5) / n_bragg_bins
        rgb = eval_bragg_lut(phi_v)
        py5.fill(int(rgb[0]), int(rgb[1]), int(rgb[2]), 238)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(q_list, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

    if ctene_cilia_lines:
        py5.stroke(255, 252, 234, 155)
        py5.stroke_weight(1.25)
        py5.lines(np.array(ctene_cilia_lines, dtype=np.float32))

    # 5. Aboral Apical Sensory Organ (Statocyst Dome & Calcareous Statolith) & Infundibulum Node
    py5.no_stroke()
    py5.fill(42, 238, 255, 195)
    py5.circle(CX, y_infund, 22.0)
    py5.fill(255, 248, 210, 235)
    py5.circle(CX, y_infund, 10.0)

    py5.stroke(118, 236, 255, 225)
    py5.stroke_weight(2.0)
    py5.fill(14, 34, 68, 225)
    py5.arc(CX, y_aboral + 6.0, 68.0, 56.0, np.pi, 2.0 * np.pi, py5.CHORD)
    py5.no_stroke()
    py5.fill(255, 236, 142)
    py5.circle(CX, y_aboral - 6.0, 14.0)

    # 6. Precision Brass & Darkfield Goniometer Bezel Ring
    py5.no_fill()
    py5.stroke(44, 68, 108)
    py5.stroke_weight(3.0)
    py5.circle(CX, CY, R_VIEWPORT * 2.0)

    py5.stroke(42, 218, 252, 185)
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
    py5.stroke(110, 188, 238, 165)
    py5.stroke_weight(1.3)
    py5.lines(np.array(tick_segs, dtype=np.float32))


# ---------------------------------------------------------------------------
# Side Panels & 8 Marine Biology / Ciliary Photonics Apparatuses
# ---------------------------------------------------------------------------
def draw_card_shell(x, y, w, h, fig_top, title_top, sub_top, fig_bot, title_bot, sub_bot):
    py5.fill(*CARD_BG)
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    mid_y = y + h * 0.49
    py5.stroke(44, 68, 108, 160)
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
        "FIG. 01", "ANTIPLECTIC METACHRONAL CILIARY STROKE KINEMATICS",
        "NON-RECIPROCAL POWER STROKE (STIFF PADDLE) vs. RECOVERY STROKE (ROLLING UNBENDING)",
        "FIG. 02", "2D HEXAGONAL MACROCILIARY PHOTONIC CRYSTAL LATTICE",
        "9+3 AXONEME PACKING (d = 220 nm): BRAGG DIFFRACTION LAMBDA = 2 * d * n_eff * SIN(THETA)",
    )

    # FIG. 01 Diagram: 8 Comb Plates Executing a Metachronal Wave Envelope (Strictly bounded inside box!)
    bx, by, bw, bh = LEFT_X + 28, CARD_Y_TOP + 86, 235.0, 245.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(bx, by, bw, bh, 4)

    base_y = by + bh - 42.0
    py5.stroke(42, 218, 252, 180)
    py5.stroke_weight(2.0)
    py5.line(bx + 18, base_y, bx + bw - 18, base_y)

    for k in range(7):
        kx = bx + 36.0 + k * 25.0
        ph = 2.0 * tau - 0.68 * k
        ang = -0.5 * np.pi + 0.42 * np.sin(ph)
        rgb = eval_bragg_lut(0.5 + 0.48 * np.sin(ph))
        mx = kx + 38.0 * np.cos(ang)
        my = base_y + 38.0 * np.sin(ang)
        tx = np.clip(mx + 32.0 * np.cos(ang + 0.30 * max(0.0, -np.cos(ph))), bx + 14.0, bx + bw - 14.0)
        ty = my + 32.0 * np.sin(ang + 0.30 * max(0.0, -np.cos(ph)))
        py5.stroke(int(rgb[0]), int(rgb[1]), int(rgb[2]), 240)
        py5.stroke_weight(4.0)
        py5.line(kx, base_y, mx, my)
        py5.line(mx, my, tx, ty)

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("METACHRONAL MODE", "Antiplectic (Wave Opposite Power)"),
        ("COMB ROWS (COSTAE)", "8 Meridian Rows (4 Pairs)"),
        ("CTENES PER ROW", "34 Fused Macrociliary Paddles"),
        ("CILIA PER CTENE", "~10^4 - 10^5 Fused 9+3 Cilia"),
        ("BEAT FREQUENCY", "f_beat = 12.0 - 18.5 Hz Regulated"),
        ("REYNOLDS NUMBER", "Re_body ~ 150 (Inertial-Viscous)"),
        ("ASYMMETRY RATIO", "Purcell Scallop Theorem Bypass"),
    ])

    # FIG. 02 Diagram: 2D Hexagonal Axoneme Photonic Crystal Cross-Section
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    px, py, pw, ph = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(px, py, pw, ph, 4)

    py5.no_stroke()
    for r_i in range(-2, 3):
        for c_i in range(-2, 3):
            hx = px + pw * 0.5 + c_i * 34.0 + (r_i % 2) * 17.0
            hy = py + ph * 0.54 + r_i * 29.5
            rgb = eval_bragg_lut(0.18 * (r_i + 3) + 0.08 * c_i + tau / (2.0 * np.pi))
            py5.fill(int(rgb[0]), int(rgb[1]), int(rgb[2]), 220)
            py5.circle(hx, hy, 18.0)
            py5.fill(8, 12, 24)
            py5.circle(hx, hy, 7.0)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("AXONEME ULTRASTRUCT", "9+3 Microtubule + Compartmental Lamella"),
        ("LATTICE SPACING (d)", "d_hex = 218.0 nm Inter-Ciliary Pitch"),
        ("REFRACTIVE CONTRAST", "n_cilium = 1.42 vs n_seawater = 1.34"),
        ("STRUCTURAL COLOR", "2D Bragg Photonic Crystal Grating"),
        ("DIFFRACTION SPAN", "420 nm (Violet) -> 660 nm (Ruby)"),
        ("IRIDESCENCE vs BIO", "Rainbow = Diffraction / Cyan = Bio"),
        ("WELCH ET AL. (2006)", "Beroe Photonic Crystal Discovery"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "CA2+-PHOTOPROTEIN (MNEMIOPSIN / BEROVIN) BIOLUMINESCENCE",
        "COELENTERAZINE OXIDATION: APO-MNEMIOPSIN + O2 + 3 CA2+ -> EXCITED COELENTERAMIDE (488 nm)",
        "FIG. 04", "CTENE BRAGG IRIDESCENCE & BIOLUMINESCENT PALETTE",
        "488 nm MNEMIOPSIN CYAN, 508 nm VIRIDIAN & FULL-SPECTRUM CILIARY DIFFRACTION SWATCHES",
    )

    sx, sy, sw, sh = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(sx, sy, sw, sh, 4)

    xs_sp = np.linspace(0.0, 1.0, 64)
    sp_env = np.exp(-26.0 * (xs_sp - 0.42) ** 2) + 0.25 * np.exp(-18.0 * (xs_sp - 0.58) ** 2)
    sp_segs = []
    for j in range(len(xs_sp) - 1):
        x0_s = sx + 16.0 + xs_sp[j] * (sw - 32.0)
        x1_s = sx + 16.0 + xs_sp[j + 1] * (sw - 32.0)
        y0_s = sy + sh - 28.0 - sp_env[j] * (sh - 64.0)
        y1_s = sy + sh - 28.0 - sp_env[j + 1] * (sh - 64.0)
        sp_segs.append([x0_s, y0_s, x1_s, y1_s])
    py5.stroke(24, 218, 254)
    py5.stroke_weight(2.6)
    py5.lines(np.array(sp_segs, dtype=np.float32))

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("PHOTOPROTEIN", "Mnemiopsin-1 / Berovin (EF-Hand)"),
        ("CHROMOPHORE", "2-Hydroperoxycoelenterazine"),
        ("TRIGGER ION", "3 Ca2+ Binding to EF-Hand Loops"),
        ("EMISSION PEAK", "lambda_max = 488.0 nm Blue-Cyan"),
        ("PHOTOCYTE LOCUS", "Meridional Gastrovascular Canals"),
        ("PHOTO-INHIBITION", "Sunlight Inactivates / Dark Restores"),
        ("QUANTUM YIELD", "Phi_BL = 0.14 (Shimomura 1974)"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (BIOLUM_CYAN, "MNEMIOPSIN BIOLUMINESCENT CYAN // 488.0 nm CA2+-PHOTOPROTEIN FLASH (#18DAFE)"),
        (BIOLUM_VIRIDIAN, "COELENTERAMIDE VIRIDIAN // 508.0 nm ENDODERMAL CANAL AFTERGLOW (#14F2B2)"),
        (BRAGG_RUBY, "POWER-STROKE BRAGG RUBY // 650.0 nm MAX-INCLINATION CTENE GRATING (#FA348A)"),
        (BRAGG_GOLD, "MID-STROKE BRAGG AMBER GOLD // 585.0 nm CONSTRUCTIVE INTERFERENCE (#FFD04A)"),
        (BRAGG_VIOLET, "RECOVERY-STROKE BRAGG VIOLET // 430.0 nm GRAZING CILIARY DIFFRACTION (#AE52FE)"),
        (MESOGLEA_SAPPHIRE, "HYALINE MESOGLEA SAPPHIRE // COLLAGEN-PROTEOGLYCAN HYDROGEL BELL (#2260D4)"),
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
        "FIG. 05", "BIRADIAL OCTOMEROUS SYMMETRY & APICAL STATOCYST ORGAN",
        "SAGITTAL VS. TENTACULAR PLANES: CALCAREOUS STATOLITH ON 4 BALANCERS & 8 CILIATED GROOVES",
        "FIG. 06", "HISTORICAL CTENOPHORE MORPHOLOGY & BIOPHYSICS LEDGER",
        "FROM ESCHSCHOLTZ (1829) & CHUN (1880) TO HAECKEL (1904) & SHIMOMURA (1974)",
    )

    dx, dy = RIGHT_X + 145, CARD_Y_TOP + 215
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0, 4)

    py5.no_fill()
    py5.stroke(44, 68, 108)
    py5.circle(dx, dy, 185.0)
    py5.circle(dx, dy, 68.0)

    spoke_angles = [0.28, 0.72, 1.28, 1.72, 2.28, 2.72, 3.28, 3.72]
    for idx_s, ang_p in enumerate(spoke_angles):
        ang = ang_p * np.pi * 0.5
        rgb = eval_bragg_lut(idx_s / 8.0 + tau / (2.0 * np.pi))
        py5.stroke(int(rgb[0]), int(rgb[1]), int(rgb[2]), 230)
        py5.stroke_weight(3.2)
        py5.line(dx + 16.0 * np.cos(ang), dy + 16.0 * np.sin(ang), dx + 88.0 * np.cos(ang), dy + 88.0 * np.sin(ang))

    py5.no_stroke()
    py5.fill(255, 236, 142)
    py5.circle(dx, dy, 18.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("BODY SYMMETRY", "Biradial (D_2 Rotational + 2 Planes)"),
        ("APICAL PACEMAKER", "Aboral Statocyst & Calcareous Lith"),
        ("FOUR BALANCERS", "Mechanosensory Fused Cilia Tufts"),
        ("PACEMAKER FURROWS", "8 Ciliated Grooves (2 per Balancer)"),
        ("SUBTENTACULAR", "4 Outer Costae Flanking Tentacles"),
        ("SUBSAGITTAL", "4 Inner Costae on Stomodeal Plane"),
        ("GEOTACTIC REFLEX", "Differential Beat Tilts Body Axis"),
    ])

    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("SYSTEMATIK (1829)", "Johann F. Eschscholtz", "Ctenophora Taxon", "First Comb-Bearer Classification"),
        ("NAPLES MONOGR. (1880)", "Carl Chun", "8-Costae Ontogeny", "Ctenophoren des Golfes von Neapel"),
        ("PLATE 27 (1904)", "Ernst Haeckel", "Biradial Geometry", "Kunstformen der Natur Ctenophora"),
        ("CILIARY FLUIDS (1951)", "Sir G. I. Taylor", "Low-Re Sheet Wave", "Metachronal Propulsion Physics"),
        ("PHOTOPROTEIN (1974)", "Ward & Shimomura", "Mnemiopsin + Ca2+", "488 nm Coelenterazine Flash"),
        ("BATHYPELAGIC LIVE", "272 Articulated Ctenes", "Bragg + 488 nm Bio", "HARMONIC METACHRONAL WAVE"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(22, 38, 68, 215 if is_active else 115)
        py5.stroke(42, 218, 252 if is_active else 46, 200 if is_active else 110)
        py5.stroke_weight(1.6 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(TEXT_ACCENT if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*TEXT_SECONDARY)
        py5.text(author, RIGHT_X + 240, ry + 21)
        py5.fill(255, 208, 74 if is_active else 218)
        py5.text(metric, RIGHT_X + 430, ry + 21)
        py5.fill(*TEXT_PRIMARY)
        py5.text(desc, RIGHT_X + 605, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "LOW-REYNOLDS-NUMBER VORTEX SHEET & COLLOBLAST TENTILLA",
        "NON-RECIPROCAL METACHRONAL JET STREAMLINES & ADHESIVE COLLOBLAST GRANULES",
        "FIG. 08", "8-ROW METACHRONAL PHASE & CA2+ BIOLUMINESCENCE OSCILLOGRAM",
        "SYNCHRONOUS SUBTENTACULAR vs. SUBSAGITTAL CTENE STROKE & 488 nm PHOTOCYTE WAVE",
    )

    tx, ty, tw, th = RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(8, 12, 24)
    py5.stroke(*CARD_BORDER)
    py5.rect(tx, ty, tw, th, 4)

    for v_i in range(3):
        vy = ty + 55.0 + v_i * 72.0
        vx = tx + tw * 0.5 + 16.0 * np.sin(tau + v_i * 1.4)
        py5.no_fill()
        py5.stroke(42, 218, 252, 185)
        py5.stroke_weight(1.8)
        py5.ellipse(vx, vy, 138.0, 44.0)
        py5.stroke(250, 52, 138, 165)
        py5.ellipse(vx, vy, 82.0, 24.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("HYDRODYNAMIC JET", "Continuous Wake Without Jet Pulsing"),
        ("STEALTH PREDATION", "Minimal Shear Disturbance Field"),
        ("TENTILLA ARRAYS", "Lateral Branches on Main Tentacles"),
        ("COLLOBLAST CELLS", "Spiral Filament + Adhesive Granules"),
        ("PREY CAPTURE", "Copepods & Euphausiid Larvae"),
        ("SWIMMING SPEED", "v_swim = 18.5 mm/s Laminar Glide"),
        ("PROPULSIVE EFF.", "eta_hydro = 0.38 Metachronal Coupling"),
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
        (250, 52, 138, 0.0, 1.0),
        (255, 208, 74, np.pi * 0.5, 0.85),
        (24, 218, 254, np.pi * 1.1, 0.72),
    ]
    for rc, gc, bc, p_shift, amp_s in waves:
        ph_w = xs_osc * 5.0 * np.pi - 3.0 * tau + p_shift
        y_sig = (np.sin(ph_w) + 0.28 * np.sin(2.0 * ph_w)) * (oh * 0.30 * amp_s)
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
        "RUBY: SUBTENTACULAR COSTAE // GOLD: SUBSAGITTAL COSTAE // CYAN: 488 nm CA2+ PHOTOCYTE WAVE",
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
        "CTENOPHORA METACHRONAL COMB-PLATE IRIDESCENCE & BIOLUMINESCENCE",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "HAECKEL KUNSTFORMEN PLATE 27 (1904), 2D MACROCILIARY PHOTONIC CRYSTAL GRATING & 488 nm MNEMIOPSIN PHOTOPROTEIN",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "8 MERIDIAN COSTAE x 34 ARTICULATED CTENES // d_HEX = 218 nm BRAGG DIFFRACTION // CA2+-TRIGGERED COELENTERAZINE FLASH",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K BATHYPELAGIC MORPHOGENESIS // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_OBSIDIAN)

    draw_header_and_footer(tau)
    draw_ctenophore_viewport(tau)
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

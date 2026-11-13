"""
kinetic_breguet_tourbillon_swiss_lever_escapement_chronometer_2d

Abraham-Louis Breguet's June 26, 1801 Patent (Regulateur a Tourbillon, 7 Messidor
An IX), Thomas Mudge's Detached Ruby-Pallet Swiss Lever Escapement (Echappement
a Ancre Suisse), and Edouard Phillips's 1861 Isochronous Terminal Overcoil
Hairspring (Spiral Breguet), inspired by Breguet's 1801 watercolor patent plates,
Ferdinand Berthoud's Traite des Horloges Marines (1773), and George Daniels's
Watchmaking (1981).
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
WORK_NAME = "kinetic_breguet_tourbillon_swiss_lever_escapement_chronometer_2d"
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
# Color Palette — Warm Geneva Horological Patent Vellum & Movement Metals
# ---------------------------------------------------------------------------
BG_VELLUM = (246, 242, 232)       # #f6f2e8 Warm Breguet 1801 Patent Vellum
CARD_BG = (252, 249, 242, 238)    # Translucent Horological Plate Paper
CARD_BORDER = (184, 166, 136)     # Sepia & Brass Caliper Rule
TEXT_PRIMARY = (24, 30, 44)       # Deep Iron-Gall Ink
TEXT_SECONDARY = (94, 86, 74)     # Muted Sepia Specification Ink
TEXT_ACCENT = (186, 46, 56)       # Synthetic Ruby Corundum Crimson

PLATINE_DARK = (12, 18, 32)       # #0c1220 Recessed Rhodium-Anthracite Mainplate
COTES_SLATE = (22, 34, 58)        # Cotes de Geneve Bridge Striation Slate
GLUCYDUR_GOLD = (228, 174, 52)    # Glucydur Beryllium-Bronze Balance & Brass Gears
GLUCYDUR_HIGH = (254, 226, 118)   # Specular Diamond-Cut Chamfer Gold
STEEL_POLISHED = (196, 210, 232)  # Black-Polished (Speculaire) Tourbillon Cage Steel
STEEL_SHADOW = (118, 136, 168)    # Beveled Cage Flank
BLUED_STEEL = (38, 136, 246)      # 295 C Heat-Blued Steel Hairspring & Screws
BLUED_HIGH = (96, 188, 255)       # Specular Elinvar Overcoil Sheen
RUBY_JEWEL = (224, 34, 72)        # Synthetic Corundum Ruby Pallet & Pivot Jewel
RUBY_HIGH = (255, 112, 138)       # Specular Ruby Facet Glint

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

GRID_LINES = None
COTES_QUADS = None
FIXED_WHEEL_QUADS = None


def build_gear_ring_quads(cx, cy, r_root, r_pitch, r_tip, n_teeth, tooth_frac=0.46, rot_offset=0.0):
    """Build batched quads for an epicycloidal horological gear wheel rim + teeth."""
    quads = []
    d_ang = (2.0 * np.pi) / n_teeth
    r_inner_rim = r_root * 0.88

    for k in range(n_teeth):
        a0 = k * d_ang + rot_offset
        a1 = (k + 1.0) * d_ang + rot_offset
        # Rim segment
        quads.append([
            [cx + r_inner_rim * np.cos(a0), cy + r_inner_rim * np.sin(a0)],
            [cx + r_root * np.cos(a0), cy + r_root * np.sin(a0)],
            [cx + r_root * np.cos(a1), cy + r_root * np.sin(a1)],
            [cx + r_inner_rim * np.cos(a1), cy + r_inner_rim * np.sin(a1)],
        ])
        # Epicycloidal tooth (base -> ogival tip)
        ta0 = a0 + d_ang * (0.5 - 0.5 * tooth_frac)
        ta1 = a0 + d_ang * (0.5 + 0.5 * tooth_frac)
        ta_tip0 = a0 + d_ang * (0.5 - 0.22 * tooth_frac)
        ta_tip1 = a0 + d_ang * (0.5 + 0.22 * tooth_frac)
        quads.append([
            [cx + r_root * np.cos(ta0), cy + r_root * np.sin(ta0)],
            [cx + r_tip * np.cos(ta_tip0), cy + r_tip * np.sin(ta_tip0)],
            [cx + r_tip * np.cos(ta_tip1), cy + r_tip * np.sin(ta_tip1)],
            [cx + r_root * np.cos(ta1), cy + r_root * np.sin(ta1)],
        ])
    return np.array(quads, dtype=np.float32)


def init_horology_geometry():
    """Precompute background drafting grid, Cotes de Geneve stripes, and Fixed Fourth Wheel."""
    global GRID_LINES, COTES_QUADS, FIXED_WHEEL_QUADS

    g_segs = []
    for x in range(80, WIDTH - 80, 60):
        g_segs.append([float(x), 55.0, float(x), float(HEIGHT - 55)])
    for y in range(60, HEIGHT - 60, 60):
        g_segs.append([80.0, float(y), float(WIDTH - 80), float(y)])
    GRID_LINES = np.array(g_segs, dtype=np.float32)

    # Cotes de Geneve vertical damaskeening stripes clipped to R_cotes = 765 px
    cotes = []
    r_cotes = 765.0
    n_stripes = 28
    xs = np.linspace(CX - r_cotes, CX + r_cotes, n_stripes + 1)
    for i in range(0, n_stripes, 2):
        x0 = float(xs[i])
        x1 = float(xs[i + 1])
        dx0 = np.clip((x0 - CX) / r_cotes, -0.999, 0.999)
        dx1 = np.clip((x1 - CX) / r_cotes, -0.999, 0.999)
        yh0 = r_cotes * np.sqrt(1.0 - dx0 * dx0)
        yh1 = r_cotes * np.sqrt(1.0 - dx1 * dx1)
        cotes.append([
            [x0, CY - yh0],
            [x1, CY - yh1],
            [x1, CY + yh1],
            [x0, CY + yh0],
        ])
    COTES_QUADS = np.array(cotes, dtype=np.float32)

    # Stationary Fixed Fourth Wheel (Roue de Champ Fixe, Z = 90 teeth at R = 540..572 px)
    FIXED_WHEEL_QUADS = build_gear_ring_quads(CX, CY, 536.0, 554.0, 572.0, 90, 0.48)


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

    init_horology_geometry()
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


def draw_ruby_chaton(x, y, r_gold=22.0, r_ruby=14.0, r_hole=5.0, n_screws=3, rot=0.0):
    """Render a traditional gold-mounted synthetic ruby chaton with heat-blued screws."""
    py5.stroke(142, 98, 24)
    py5.stroke_weight(1.5)
    py5.fill(*GLUCYDUR_HIGH)
    py5.circle(x, y, r_gold * 2.0)

    py5.no_stroke()
    py5.fill(*RUBY_JEWEL)
    py5.circle(x, y, r_ruby * 2.0)
    py5.fill(*RUBY_HIGH)
    py5.circle(x - r_ruby * 0.28, y - r_ruby * 0.28, r_ruby * 0.55)
    py5.fill(*PLATINE_DARK)
    py5.circle(x, y, r_hole * 2.0)

    for k in range(n_screws):
        ang = rot + k * (2.0 * np.pi / n_screws)
        sx = x + (r_gold + 10.0) * np.cos(ang)
        sy = y + (r_gold + 10.0) * np.sin(ang)
        py5.fill(*BLUED_STEEL)
        py5.no_stroke()
        py5.circle(sx, sy, 11.0)
        py5.stroke(236, 242, 252)
        py5.stroke_weight(1.2)
        py5.line(sx - 4.0 * np.cos(ang), sy - 4.0 * np.sin(ang), sx + 4.0 * np.cos(ang), sy + 4.0 * np.sin(ang))


# ---------------------------------------------------------------------------
# Main Medallion: Breguet Tourbillon Carriage, Balance, Overcoil & Escapement
# ---------------------------------------------------------------------------
def draw_tourbillon_medallion(tau):
    # Tourbillon carriage rotates 1 full turn (2*pi) across the 720-frame loop!
    theta_cage = tau + PHASE_OFFSET * 0.25

    # Balance wheel executes N_OSC = 12 full harmonic cycles (24 ticks) per carriage revolution!
    n_osc = 12
    osc_phase = n_osc * tau
    # Balance amplitude Theta_max = 265 deg (4.62 rad)
    theta_bal_rel = 2.45 * np.sin(osc_phase)
    theta_bal = theta_cage + theta_bal_rel

    # Escape wheel advances in discrete Lock-Impulse-Drop steps (24 steps per revolution)
    step_float = (osc_phase / np.pi)
    step_int = np.floor(step_float)
    step_frac = step_float - step_int
    # Smooth impulse jump near zero crossing of balance (when cos(osc_phase) is max -> step_frac ~ 0.0 or 0.5)
    escape_advance = (step_int + 1.0 / (1.0 + np.exp(-16.0 * (step_frac - 0.5)))) * (2.0 * np.pi / 30.0)

    # 1. Outer Chronometer Chapter Ring & Cotes de Geneve Mainplate
    py5.no_stroke()
    py5.fill(*GLUCYDUR_GOLD)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    py5.fill(*PLATINE_DARK)
    py5.circle(CX, CY, R_MEDALLION * 2.0)

    # Cotes de Geneve damaskeening stripes
    py5.fill(18, 28, 48, 175)
    py5.begin_shape(py5.QUADS)
    py5.vertices(COTES_QUADS.reshape(-1, 2))
    py5.end_shape()

    # Recessed Tourbillon Well (Aperture in the mainplate, R = 605 px)
    py5.stroke(*GLUCYDUR_GOLD)
    py5.stroke_weight(2.6)
    py5.fill(8, 13, 24)
    py5.circle(CX, CY, 608.0 * 2.0)

    # Perlage (circular engine-turned graining) rings inside the tourbillon well
    py5.no_fill()
    py5.stroke(26, 42, 74, 120)
    py5.stroke_weight(1.2)
    for r_p in [180.0, 310.0, 440.0, 520.0]:
        py5.circle(CX, CY, r_p * 2.0)

    # Outer Mainplate Ruby Jewels & Heat-Blued Bridge Screws on the Cotes de Geneve surround
    for k in range(6):
        ang_j = k * (np.pi / 3.0) + np.pi / 6.0
        jx = CX + 692.0 * np.cos(ang_j)
        jy = CY + 692.0 * np.sin(ang_j)
        draw_ruby_chaton(jx, jy, r_gold=20.0, r_ruby=12.5, r_hole=4.5, n_screws=2, rot=ang_j)

    # 2. Stationary Fixed Fourth Wheel (Roue de Champ Fixe, R = 536..572 px)
    py5.no_stroke()
    py5.fill(*GLUCYDUR_GOLD)
    py5.begin_shape(py5.QUADS)
    py5.vertices(FIXED_WHEEL_QUADS.reshape(-1, 2))
    py5.end_shape()

    py5.no_fill()
    py5.stroke(*GLUCYDUR_HIGH)
    py5.stroke_weight(2.0)
    py5.circle(CX, CY, 536.0 * 2.0)

    # -----------------------------------------------------------------------
    # 3. Planetarily Orbiting 15-Tooth Club-Foot Escape Wheel & Swiss Lever (Ancre)
    # Mounted on the rotating Tourbillon Carriage at R_orbit = 335 px!
    # -----------------------------------------------------------------------
    r_orbit = 335.0
    ang_esc_pos = theta_cage + np.pi * 0.5
    ex = CX + r_orbit * np.cos(ang_esc_pos)
    ey = CY + r_orbit * np.sin(ang_esc_pos)
    r_esc = 128.0
    n_esc_teeth = 15
    rot_esc = -4.0 * theta_cage + escape_advance

    # Escape wheel 5 spokes
    esc_spokes = []
    for k in range(5):
        a_sp = rot_esc + k * (2.0 * np.pi / 5.0)
        esc_spokes.append([ex, ey, ex + (r_esc * 0.78) * np.cos(a_sp), ey + (r_esc * 0.78) * np.sin(a_sp)])
    py5.stroke(214, 154, 38)
    py5.stroke_weight(5.5)
    py5.lines(np.array(esc_spokes, dtype=np.float32))

    # Escape wheel rim & 15 club-foot impulse teeth (Dents a Talon)
    esc_quads = build_gear_ring_quads(ex, ey, r_esc * 0.76, r_esc * 0.88, r_esc * 1.12, n_esc_teeth, 0.34, rot_esc)
    py5.no_stroke()
    py5.fill(*GLUCYDUR_HIGH)
    py5.begin_shape(py5.QUADS)
    py5.vertices(esc_quads.reshape(-1, 2))
    py5.end_shape()

    draw_ruby_chaton(ex, ey, r_gold=18.0, r_ruby=11.5, r_hole=4.0, n_screws=0)

    # Swiss Lever (Ancre a Levees en Rubis) pivoting at R_pallet = 195 px between Escape Wheel and Center
    r_pallet = 195.0
    px_pal = CX + r_pallet * np.cos(ang_esc_pos)
    py_pal = CY + r_pallet * np.sin(ang_esc_pos)
    # Lever rocks between +12 deg and -12 deg according to sign of cos(osc_phase)
    lever_tilt = 0.22 * np.tanh(4.0 * np.cos(osc_phase))
    ang_lever = ang_esc_pos + lever_tilt

    # Lever fork pointing toward center (CX, CY) + 2 pallet arms embracing Escape Wheel
    fx_end = px_pal - 135.0 * np.cos(ang_lever)
    fy_end = py_pal - 135.0 * np.sin(ang_lever)
    p_left_x = px_pal + 88.0 * np.cos(ang_lever - 0.62)
    p_left_y = py_pal + 88.0 * np.sin(ang_lever - 0.62)
    p_right_x = px_pal + 88.0 * np.cos(ang_lever + 0.62)
    p_right_y = py_pal + 88.0 * np.sin(ang_lever + 0.62)

    py5.stroke(*STEEL_POLISHED)
    py5.stroke_weight(6.5)
    py5.line(px_pal, py_pal, fx_end, fy_end)
    py5.line(px_pal, py_pal, p_left_x, p_left_y)
    py5.line(px_pal, py_pal, p_right_x, p_right_y)

    # Entrance & Exit Synthetic Ruby Pallet Stones (Levees d'Entree et de Sortie)
    py5.no_stroke()
    py5.fill(*RUBY_JEWEL)
    for rx_p, ry_p, a_off in [(p_left_x, p_left_y, -0.4), (p_right_x, p_right_y, 0.4)]:
        ca, sa = np.cos(ang_lever + a_off), np.sin(ang_lever + a_off)
        py5.begin_shape(py5.QUADS)
        py5.vertex(rx_p - 12 * ca - 5 * sa, ry_p - 12 * sa + 5 * ca)
        py5.vertex(rx_p + 12 * ca - 5 * sa, ry_p + 12 * sa + 5 * ca)
        py5.vertex(rx_p + 12 * ca + 5 * sa, ry_p + 12 * sa - 5 * ca)
        py5.vertex(rx_p - 12 * ca + 5 * sa, ry_p - 12 * sa - 5 * ca)
        py5.end_shape()

    draw_ruby_chaton(px_pal, py_pal, r_gold=14.0, r_ruby=9.0, r_hole=3.5, n_screws=0)

    # -----------------------------------------------------------------------
    # 4. Concentric Oscillating Glucydur Balance Wheel (Balancier a Vis de Reglage)
    # -----------------------------------------------------------------------
    r_bal_out = 438.0
    r_bal_in = 392.0

    # Balance wheel 4 beveled spokes rotating at theta_bal
    bal_spoke_quads = []
    for k in range(4):
        a_b = theta_bal + k * (np.pi * 0.5)
        ca, sa = np.cos(a_b), np.sin(a_b)
        nx, ny = -sa, ca
        w_in, w_out = 14.0, 9.0
        bal_spoke_quads.append([
            [CX + 46.0 * ca - w_in * nx, CY + 46.0 * sa - w_in * ny],
            [CX + 46.0 * ca + w_in * nx, CY + 46.0 * sa + w_in * ny],
            [CX + r_bal_in * ca + w_out * nx, CY + r_bal_in * sa + w_out * ny],
            [CX + r_bal_in * ca - w_out * nx, CY + r_bal_in * sa - w_out * ny],
        ])

    # Balance wheel circular rim quads (64 segments) + 16 Gold Timing/Poise Screws
    n_rim = 64
    rim_angles = np.linspace(0.0, 2.0 * np.pi, n_rim + 1) + theta_bal
    rim_quads = []
    for j in range(n_rim):
        a0, a1 = rim_angles[j], rim_angles[j + 1]
        rim_quads.append([
            [CX + r_bal_in * np.cos(a0), CY + r_bal_in * np.sin(a0)],
            [CX + r_bal_out * np.cos(a0), CY + r_bal_out * np.sin(a0)],
            [CX + r_bal_out * np.cos(a1), CY + r_bal_out * np.sin(a1)],
            [CX + r_bal_in * np.cos(a1), CY + r_bal_in * np.sin(a1)],
        ])

    screw_stem_quads = []
    screw_head_quads = []
    for k in range(16):
        a_sc = theta_bal + k * (2.0 * np.pi / 16.0)
        ca, sa = np.cos(a_sc), np.sin(a_sc)
        nx, ny = -sa, ca
        # Stem from r_bal_out to r_bal_out + 14
        r0_s, r1_s, r2_s = r_bal_out, r_bal_out + 12.0, r_bal_out + 24.0
        screw_stem_quads.append([
            [CX + r0_s * ca - 4.0 * nx, CY + r0_s * sa - 4.0 * ny],
            [CX + r0_s * ca + 4.0 * nx, CY + r0_s * sa + 4.0 * ny],
            [CX + r1_s * ca + 4.0 * nx, CY + r1_s * sa + 4.0 * ny],
            [CX + r1_s * ca - 4.0 * nx, CY + r1_s * sa - 4.0 * ny],
        ])
        screw_head_quads.append([
            [CX + r1_s * ca - 9.5 * nx, CY + r1_s * sa - 9.5 * ny],
            [CX + r1_s * ca + 9.5 * nx, CY + r1_s * sa + 9.5 * ny],
            [CX + r2_s * ca + 9.5 * nx, CY + r2_s * sa + 9.5 * ny],
            [CX + r2_s * ca - 9.5 * nx, CY + r2_s * sa - 9.5 * ny],
        ])

    py5.no_stroke()
    py5.fill(*GLUCYDUR_GOLD)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.vstack([
        np.array(bal_spoke_quads, dtype=np.float32).reshape(-1, 2),
        np.array(rim_quads, dtype=np.float32).reshape(-1, 2),
        np.array(screw_stem_quads, dtype=np.float32).reshape(-1, 2),
    ]))
    py5.end_shape()

    py5.fill(*GLUCYDUR_HIGH)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(screw_head_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.no_fill()
    py5.stroke(148, 98, 22)
    py5.stroke_weight(2.0)
    py5.circle(CX, CY, r_bal_in * 2.0)
    py5.circle(CX, CY, r_bal_out * 2.0)

    # -----------------------------------------------------------------------
    # 5. Breathing Breguet Overcoil Hairspring (Spiral Breguet a Courbe Phillips)
    # -----------------------------------------------------------------------
    # 6.5-turn Archimedean spiral from inner collet (Virole, r=36 px) to outer stud (Piton, r=215 px)
    # Radial breathing expansion/contraction proportional to theta_bal_rel!
    n_sp_pts = 320
    u_sp = np.linspace(0.0, 1.0, n_sp_pts)
    n_turns = 6.5
    # Inner end rotates with theta_bal; outer end is pinned to the Tourbillon Carriage at theta_cage!
    phi_sp = theta_cage + u_sp * (n_turns * 2.0 * np.pi) + (1.0 - u_sp ** 1.35) * theta_bal_rel
    breath = 1.0 - 0.11 * np.sin(osc_phase) * np.sin(u_sp * np.pi)
    r_sp = (38.0 + u_sp * 178.0) * breath

    x_sp = CX + r_sp * np.cos(phi_sp)
    y_sp = CY + r_sp * np.sin(phi_sp)

    sp_segs = np.empty((n_sp_pts - 1, 4), dtype=np.float32)
    sp_segs[:, 0], sp_segs[:, 1] = x_sp[:-1], y_sp[:-1]
    sp_segs[:, 2], sp_segs[:, 3] = x_sp[1:], y_sp[1:]

    py5.stroke(*BLUED_STEEL)
    py5.stroke_weight(3.4)
    py5.lines(sp_segs)

    # Elevated Phillips Terminal Overcoil Curve (Courbe Terminale Phillips) arching inward to the Piton stud
    u_ov = np.linspace(0.0, 1.0, 64)
    ang_ov_start = phi_sp[-1]
    ang_ov = ang_ov_start + u_ov * (1.35 * np.pi)
    r_ov = r_sp[-1] * (1.0 - 0.34 * np.sin(u_ov * np.pi * 0.85))
    x_ov = CX + r_ov * np.cos(ang_ov)
    y_ov = CY + r_ov * np.sin(ang_ov)
    ov_segs = np.empty((len(u_ov) - 1, 4), dtype=np.float32)
    ov_segs[:, 0], ov_segs[:, 1] = x_ov[:-1], y_ov[:-1]
    ov_segs[:, 2], ov_segs[:, 3] = x_ov[1:], y_ov[1:]

    py5.stroke(*BLUED_HIGH)
    py5.stroke_weight(4.6)
    py5.lines(ov_segs)

    # Stud holder (Piton) pinned on the rotating Tourbillon carriage
    py5.fill(*GLUCYDUR_HIGH)
    py5.stroke(94, 72, 32)
    py5.stroke_weight(1.5)
    py5.circle(float(x_ov[-1]), float(y_ov[-1]), 16.0)

    # -----------------------------------------------------------------------
    # 6. Rotating Three-Arm Black-Polished Steel Tourbillon Carriage (Cage de Tourbillon)
    # -----------------------------------------------------------------------
    r_cage_ring = 498.0
    cage_arm_quads = []
    cage_bevel_lines = []

    for k in range(3):
        a_c = theta_cage + k * (2.0 * np.pi / 3.0)
        ca, sa = np.cos(a_c), np.sin(a_c)
        nx, ny = -sa, ca
        # Sculpted tapered steel carriage arm from center hub (r=44) to outer cage ring (r=498)
        n_seg_arm = 16
        us_a = np.linspace(44.0, r_cage_ring, n_seg_arm + 1)
        for j in range(n_seg_arm):
            r0_a, r1_a = us_a[j], us_a[j + 1]
            # Lyre-flared arm width profile
            w0 = 11.0 + 7.0 * np.sin((j / n_seg_arm) * np.pi)
            w1 = 11.0 + 7.0 * np.sin(((j + 1) / n_seg_arm) * np.pi)
            p0 = [CX + r0_a * ca - w0 * nx, CY + r0_a * sa - w0 * ny]
            p1 = [CX + r0_a * ca + w0 * nx, CY + r0_a * sa + w0 * ny]
            p2 = [CX + r1_a * ca + w1 * nx, CY + r1_a * sa + w1 * ny]
            p3 = [CX + r1_a * ca - w1 * nx, CY + r1_a * sa - w1 * ny]
            cage_arm_quads.append([p0, p1, p2, p3])
            cage_bevel_lines.append([p0[0], p0[1], p3[0], p3[1]])
            cage_bevel_lines.append([p1[0], p1[1], p2[0], p2[1]])

        # Gold-blued carriage pillar screw at outer end of each arm
        px_pil = CX + r_cage_ring * ca
        py_pil = CY + r_cage_ring * sa
        py5.no_stroke()
        py5.fill(*GLUCYDUR_HIGH)
        py5.circle(px_pil, py_pil, 24.0)
        py5.fill(*BLUED_STEEL)
        py5.circle(px_pil, py_pil, 12.0)

    # Outer Tourbillon Carriage Ring (r = 486..508 px)
    n_cr = 72
    cr_angles = np.linspace(0.0, 2.0 * np.pi, n_cr + 1) + theta_cage
    for j in range(n_cr):
        a0, a1 = cr_angles[j], cr_angles[j + 1]
        cage_arm_quads.append([
            [CX + 486.0 * np.cos(a0), CY + 486.0 * np.sin(a0)],
            [CX + 510.0 * np.cos(a0), CY + 510.0 * np.sin(a0)],
            [CX + 510.0 * np.cos(a1), CY + 510.0 * np.sin(a1)],
            [CX + 486.0 * np.cos(a1), CY + 486.0 * np.sin(a1)],
        ])

    py5.no_stroke()
    py5.fill(*STEEL_POLISHED)
    py5.begin_shape(py5.QUADS)
    py5.vertices(np.array(cage_arm_quads, dtype=np.float32).reshape(-1, 2))
    py5.end_shape()

    py5.stroke(245, 250, 255, 220)
    py5.stroke_weight(1.6)
    py5.lines(np.array(cage_bevel_lines, dtype=np.float32))

    # Stationary Breguet Horizontal Upper Tourbillon Bridge (Pont de Tourbillon)
    # Spanning across the well from Left Mainplate (CX - 665) to Right Mainplate (CX + 665)
    py5.stroke(110, 128, 158)
    py5.stroke_weight(2.4)
    py5.fill(178, 194, 218, 220)
    py5.rect(CX - 680.0, CY - 16.0, 1360.0, 32.0, 14)
    draw_ruby_chaton(CX - 635.0, CY, r_gold=22.0, r_ruby=13.0, r_hole=5.0, n_screws=2, rot=0.0)
    draw_ruby_chaton(CX + 635.0, CY, r_gold=22.0, r_ruby=13.0, r_hole=5.0, n_screws=2, rot=0.0)

    # Central Balance & Tourbillon Upper Pivot Ruby Chaton & Shock-Spring (Pare-Chute / Incabloc)
    draw_ruby_chaton(CX, CY, r_gold=34.0, r_ruby=21.0, r_hole=7.0, n_screws=3, rot=theta_cage)

    # 7. Outer 1/5th-Second Chronometer Chapter Ring & Vernier Ticks
    py5.no_fill()
    py5.stroke(94, 72, 38)
    py5.stroke_weight(3.2)
    py5.circle(CX, CY, R_MEDALLION * 2.0)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    tick_segs = []
    for t_i in range(300):
        rad = (t_i / 300.0) * 2.0 * np.pi
        r0 = R_MEDALLION + 3.0
        r1 = R_RING_OUTER - 3.0 if t_i % 25 == 0 else (R_MEDALLION + 19.0 if t_i % 5 == 0 else R_MEDALLION + 10.0)
        tick_segs.append([
            CX + r0 * np.cos(rad), CY + r0 * np.sin(rad),
            CX + r1 * np.cos(rad), CY + r1 * np.sin(rad),
        ])
    py5.stroke(78, 58, 28, 195)
    py5.stroke_weight(1.3)
    py5.lines(np.array(tick_segs, dtype=np.float32))


# ---------------------------------------------------------------------------
# Side Panels & 8 Horological Mechanics / Isochronism Apparatuses
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
        "FIG. 01", "SWISS LEVER ESCAPEMENT: LOCK, IMPULSE & DRAW ANGLES",
        "15-TOOTH CLUB-FOOT ESCAPE WHEEL & SYNTHETIC CORUNDUM RUBY ENTRANCE/EXIT PALLETS",
        "FIG. 02", "EDOUARD PHILLIPS (1861) ISOCHRONOUS TERMINAL OVERCOIL",
        "CONCENTRIC BREATHING CONDITION: INTEGRAL(y ds) = 0, x_G = 0, y_G = R_0^2 / L_OVERCOIL",
    )

    # FIG. 01 Diagram: Swiss Lever Pallet Stones Engaging Escape Wheel Teeth
    bx, by, bw, bh = LEFT_X + 28, CARD_Y_TOP + 86, 235.0, 245.0
    py5.fill(*PLATINE_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(bx, by, bw, bh, 4)

    # Mini escape wheel arc at bottom + rocking ruby-pallet anchor above
    ex_m, ey_m = bx + bw * 0.5, by + bh - 36.0
    q_esc_m = build_gear_ring_quads(ex_m, ey_m, 64.0, 74.0, 92.0, 15, 0.34, -tau * 2.0)
    # Clip teeth inside box
    q_esc_m[..., 0] = np.clip(q_esc_m[..., 0], bx + 8.0, bx + bw - 8.0)
    q_esc_m[..., 1] = np.clip(q_esc_m[..., 1], by + 8.0, by + bh - 8.0)
    py5.no_stroke()
    py5.fill(*GLUCYDUR_HIGH)
    py5.begin_shape(py5.QUADS)
    py5.vertices(q_esc_m.reshape(-1, 2))
    py5.end_shape()

    rock_m = 0.18 * np.sin(tau * 6.0)
    px_m, py_m = bx + bw * 0.5, by + 68.0
    py5.stroke(*STEEL_POLISHED)
    py5.stroke_weight(4.5)
    py5.line(px_m, py_m, px_m - 58.0 * np.cos(0.45 + rock_m), py_m + 58.0 * np.sin(0.45 + rock_m))
    py5.line(px_m, py_m, px_m + 58.0 * np.cos(0.45 - rock_m), py_m + 58.0 * np.sin(0.45 - rock_m))
    py5.no_stroke()
    py5.fill(*RUBY_JEWEL)
    py5.circle(px_m - 58.0 * np.cos(0.45 + rock_m), py_m + 58.0 * np.sin(0.45 + rock_m), 12.0)
    py5.circle(px_m + 58.0 * np.cos(0.45 - rock_m), py_m + 58.0 * np.sin(0.45 - rock_m), 12.0)

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("ESCAPEMENT TYPE", "Detached Swiss Lever (Ancre Suisse)"),
        ("ESCAPE TEETH (Z_e)", "15 Club-Foot Teeth (Dents a Talon)"),
        ("LIFT ANGLE", "52.0 DEG Balance Roller Impulse"),
        ("DRAW ANGLE", "12.0 - 15.0 DEG Locking Safety"),
        ("PALLET JEWELS", "Monocrystalline Corundum Al2O3:Cr"),
        ("FRICTION COEFF.", "mu_ruby_steel = 0.10 Epilame Treated"),
        ("DETACHMENT RATIO", "92% Free Isochronous Oscillation"),
    ])

    # FIG. 02 Diagram: Phillips Terminal Overcoil Curve & Center of Gravity Locus
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    px, py, pw, ph = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(*PLATINE_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(px, py, pw, ph, 4)

    cx_p, cy_p = px + pw * 0.5, py + ph * 0.5
    u_p = np.linspace(0.0, 1.0, 160)
    ang_p = u_p * 4.5 * 2.0 * np.pi
    r_p = (14.0 + u_p * 74.0) * (1.0 + 0.08 * np.sin(tau * 4.0) * np.sin(u_p * np.pi))
    segs_p = np.empty((len(u_p) - 1, 4), dtype=np.float32)
    segs_p[:, 0] = cx_p + r_p[:-1] * np.cos(ang_p[:-1])
    segs_p[:, 1] = cy_p + r_p[:-1] * np.sin(ang_p[:-1])
    segs_p[:, 2] = cx_p + r_p[1:] * np.cos(ang_p[1:])
    segs_p[:, 3] = cy_p + r_p[1:] * np.sin(ang_p[1:])
    py5.stroke(*BLUED_STEEL)
    py5.stroke_weight(2.2)
    py5.lines(segs_p)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("MEMOIR AUTHOR", "Edouard Phillips (Acad. Sci., 1861)"),
        ("FIRST CONDITION", "x_G = 0 (CG on Perpendicular Axis)"),
        ("SECOND CONDITION", "y_G = R_0^2 / L_terminal"),
        ("RADIAL PRESSURE", "Zero Lateral Pivot Side-Thrust"),
        ("ALLOY THERMAL", "Nivarox / Elinvar (dE/dT ~ 0)"),
        ("QUALITY FACTOR Q", "Q_osc ~ 620 in Air at 21,600 vph"),
        ("AMPLITUDE ISOCH.", "Delta_T / T < 1.5 s/day (180-300 DEG)"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "GRAVITATIONAL POISE ERROR & TOURBILLON AVERAGING",
        "RATE VARIATION DELTA_R(THETA_CAGE) = (m*g*e / (I*w_0^2)) * J_1(THETA_0) * COS(THETA_CAGE)",
        "FIG. 04", "HAUTE HORLOGERIE METALS, RUBY & BLUED STEEL PALETTE",
        "GLUCYDUR BERYLLIUM-BRONZE, 295 C HEAT-BLUED STEEL, CORUNDUM RUBY & COTES DE GENEVE",
    )

    sx, sy, sw, sh = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(*PLATINE_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(sx, sy, sw, sh, 4)

    # Polar Bessel J_1 positional rate error rosette averaged to zero by rotating cage
    cx_b, cy_b = sx + sw * 0.5, sy + sh * 0.5
    py5.no_fill()
    py5.stroke(46, 68, 108)
    py5.circle(cx_b, cy_b, 168.0)

    angs_b = np.linspace(0.0, 2.0 * np.pi, 96)
    r_err = 52.0 + 32.0 * np.cos(angs_b - tau)
    segs_err = np.empty((len(angs_b) - 1, 4), dtype=np.float32)
    segs_err[:, 0] = cx_b + r_err[:-1] * np.cos(angs_b[:-1])
    segs_err[:, 1] = cy_b + r_err[:-1] * np.sin(angs_b[:-1])
    segs_err[:, 2] = cx_b + r_err[1:] * np.cos(angs_b[1:])
    segs_err[:, 3] = cy_b + r_err[1:] * np.sin(angs_b[1:])
    py5.stroke(*GLUCYDUR_HIGH)
    py5.stroke_weight(2.2)
    py5.lines(segs_err)

    py5.stroke(*RUBY_JEWEL)
    py5.circle(cx_b, cy_b, 104.0)  # Zero-error Tourbillon mean circle!

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("BREGUET PATENT", "7 Messidor An IX (June 26, 1801)"),
        ("VERTICAL ERROR", "Static Poise Eccentricity e_cg"),
        ("BESSEL ZERO PT.", "J_1(Theta_0) = 0 at Theta_0 = 219.8 DEG"),
        ("CAGE ROTATION", "omega_cage = 1.0 rev / 60.0 s"),
        ("INTEGRAL CANC.", "int_0^T cos(omega_cage * t) dt = 0"),
        ("CAGE MASS", "0.28 g Grade-5 Titanium & Steel"),
        ("GEAR RATIO", "Z_fixed / Z_esc_pinion = 90 / 10 = 9:1"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (GLUCYDUR_GOLD, "GLUCYDUR & LAITON DORE // BERYLLIUM-BRONZE BALANCE & EPICYCLOIDAL GEARS (#E4AE34)"),
        (BLUED_STEEL, "ACIER BLEUI A LA FLAMME // 295 C OXIDE FILM OVERCOIL & BRIDGE SCREWS (#2688F6)"),
        (RUBY_JEWEL, "RUBIS SYNTHETIQUE VERNEUIL // CORUNDUM AL2O3:CR PALLET & PIVOT CHATONS (#E02248)"),
        (STEEL_POLISHED, "POLI NOIR SPECULAIRE // ZINC-LAPPED THREE-ARM TOURBILLON CARRIAGE (#C4D2E8)"),
        (PLATINE_DARK, "MAILLECHORT RHODIE // ANTHRACITE COTES DE GENEVE & PERLAGE MAINPLATE (#0C1220)"),
        (BG_VELLUM, "VELIN BREVET AN IX // 1801 PARIS MINISTERE DE L'INTERIEUR PATENT PAPER (#F6F2E8)"),
    ]
    for i, (col, label) in enumerate(swatches):
        sy_s = mid_y_bot + 78 + i * 54
        py5.stroke(94, 86, 74, 150)
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
        "FIG. 05", "EPICYCLOIDAL HOROLOGICAL GEAR TOOTH CONJUGATION",
        "CYCLOIDAL DEDENDUM FLANK + EPICYCLOIDAL ADDENDUM OGIVE FOR LOW-TORQUE GOING TRAINS",
        "FIG. 06", "HISTORICAL PRECISION HOROLOGY & CHRONOMETER LEDGER",
        "FROM HUYGENS (1675) & MUDGE (1755) TO HARRISON (1759), BREGUET (1801) & DANIELS (1975)",
    )

    dx, dy = RIGHT_X + 145, CARD_Y_TOP + 215
    py5.fill(*PLATINE_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0, 4)

    # Meshing Gear Wheel + Pinion Leaves inside FIG. 05
    q_g1 = build_gear_ring_quads(dx - 42.0, dy + 16.0, 48.0, 56.0, 68.0, 16, 0.48, tau * 1.5)
    q_g2 = build_gear_ring_quads(dx + 52.0, dy - 22.0, 26.0, 34.0, 46.0, 8, 0.44, -tau * 3.0 + 0.2)
    py5.no_stroke()
    py5.fill(*GLUCYDUR_GOLD)
    py5.begin_shape(py5.QUADS)
    py5.vertices(q_g1.reshape(-1, 2))
    py5.end_shape()
    py5.fill(*STEEL_POLISHED)
    py5.begin_shape(py5.QUADS)
    py5.vertices(q_g2.reshape(-1, 2))
    py5.end_shape()

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("TOOTH PROFILE", "Swiss Horological Epicycloid (NHS 56702)"),
        ("ADDENDUM CURVE", "Epicycloid Generated by Auxiliary Roll"),
        ("DEDENDUM FLANK", "Radial / Hypocycloid Straight Flank"),
        ("ENGAGEMENT ARC", "Minimized Sliding Before Line of Centers"),
        ("WHEEL MATERIAL", "CuZn37 Brass Driving Hardened Steel"),
        ("FOURTH WHEEL", "Z_4 = 90 Stationary Crown Ring"),
        ("ESCAPE PINION", "Z_p = 10 Leaves Orbiting on Cage"),
    ])

    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("SPIRAL BALANCE (1675)", "Christiaan Huygens", "F = -k * theta", "First Isochronous Hairspring"),
        ("LEVER ESCAP. (1755)", "Thomas Mudge", "Detached Anchor", "Free Balance Impulse Geometry"),
        ("H4 CHRONOMETER (1759)", "John Harrison", "Longitude Prize", "5.1 s Error Across Atlantic"),
        ("TOURBILLON (1801)", "A.-L. Breguet", "Rotating Cage", "Gravity Error Cancellation"),
        ("OVERCOIL MEMOIR (1861)", "Edouard Phillips", "Terminal Curve", "Concentric Spiral Breathing"),
        ("CALIBRE LIVE", "21,600 vph / 3 Hz", "15-Tooth / 3-Arm", "HARMONIC TOURBILLON BEAT"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(*(PLATINE_DARK if is_active else (240, 234, 220)))
        py5.stroke(*(TEXT_ACCENT if is_active else CARD_BORDER))
        py5.stroke_weight(1.6 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(GLUCYDUR_HIGH if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*(STEEL_POLISHED if is_active else TEXT_SECONDARY))
        py5.text(author, RIGHT_X + 245, ry + 21)
        py5.fill(*(BLUED_HIGH if is_active else TEXT_ACCENT))
        py5.text(metric, RIGHT_X + 435, ry + 21)
        py5.fill(*(STEEL_POLISHED if is_active else TEXT_PRIMARY))
        py5.text(desc, RIGHT_X + 605, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "HAMILTONIAN PHASE PORTRAIT (THETA_BAL vs. OMEGA_BAL)",
        "LIMIT CYCLE MAINTAINED BY IMPULSE KICKS DELTA_E AT ZERO CROSSING THETA = 0",
        "FIG. 08", "VIBROGRAPH ACOUSTIC TICK-TOCK & BALANCE DISPLACEMENT",
        "SYNCHRONOUS UNLOCK-IMPULSE-DROP ACOUSTIC TRANSIENTS & HARMONIC OVERCOIL STRAIN",
    )

    tx, ty, tw, th = RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(*PLATINE_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(tx, ty, tw, th, 4)

    # Limit cycle ellipse with impulse jump steps at theta = 0 (top and bottom of phase loop)
    cx_lc, cy_lc = tx + tw * 0.5, ty + th * 0.5
    py5.stroke(44, 64, 98)
    py5.line(tx + 14, cy_lc, tx + tw - 14, cy_lc)
    py5.line(cx_lc, ty + 14, cx_lc, ty + th - 14)

    angs_lc = np.linspace(0.0, 2.0 * np.pi, 120)
    r_jump = 1.0 + 0.12 * np.sign(np.sin(angs_lc)) * np.exp(-8.0 * (np.cos(angs_lc) ** 2))
    xlc = cx_lc + 82.0 * np.cos(angs_lc)
    ylc = cy_lc + 82.0 * np.sin(angs_lc) * r_jump
    segs_lc = np.empty((len(angs_lc) - 1, 4), dtype=np.float32)
    segs_lc[:, 0], segs_lc[:, 1] = xlc[:-1], ylc[:-1]
    segs_lc[:, 2], segs_lc[:, 3] = xlc[1:], ylc[1:]
    py5.stroke(*BLUED_HIGH)
    py5.stroke_weight(2.4)
    py5.lines(segs_lc)

    # Active phase dot
    pt_ang = 12.0 * tau
    py5.no_stroke()
    py5.fill(*RUBY_JEWEL)
    py5.circle(cx_lc + 82.0 * np.cos(pt_ang), cy_lc + 82.0 * np.sin(pt_ang), 12.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("FREQUENCY", "f_0 = 3.0 Hz (21,600 vph / 6 bps)"),
        ("BALANCE INERTIA", "I_bal = 14.5 mg . cm^2 Glucydur"),
        ("SPRING TORQUE", "C_sp = 1.85e-6 N.m / rad"),
        ("OPERATING AMPL.", "Theta_max = 280.0 DEG Isochronous"),
        ("BEAT ERROR", "0.0 ms Symmetric Escapement"),
        ("CAGE AZIMUTH", f"theta_cage = {(tau / (2.0 * np.pi)) * 360.0:.1f} DEG"),
        ("CHRONOMETER CERT.", "COSC / Poincon de Geneve Spec."),
    ])

    # FIG. 08 Oscillogram: Acoustic Tick-Tock Transients & Sinusoidal Balance Wave
    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    ox, oy, ow, oh = RIGHT_X + 28, mid_y_bot + 78, CARD_W - 56, 265.0
    py5.fill(*PLATINE_DARK)
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
    py5.stroke(28, 44, 72)
    py5.stroke_weight(1.0)
    py5.lines(np.array(grid_segs, dtype=np.float32))

    xs_osc = np.linspace(0.0, 1.0, 200)
    x_px = ox + 16.0 + xs_osc * (ow - 32.0)

    # 1. Smooth Balance Wheel Displacement Curve (Gold)
    ph_o = xs_osc * 6.0 * np.pi - 12.0 * tau
    y_bal = oy + oh * 0.50 - (oh * 0.34) * np.sin(ph_o)
    segs_bal = np.empty((len(xs_osc) - 1, 4), dtype=np.float32)
    segs_bal[:, 0], segs_bal[:, 1] = x_px[:-1], y_bal[:-1]
    segs_bal[:, 2], segs_bal[:, 3] = x_px[1:], y_bal[1:]
    py5.stroke(*GLUCYDUR_HIGH)
    py5.stroke_weight(2.2)
    py5.lines(segs_bal)

    # 2. Vibrograph Acoustic Tick-Tock Impulse Bursts at zero crossings cos(ph_o) ~ +-1 (Ruby Crimson)
    imp_env = np.exp(-28.0 * (np.sin(ph_o) ** 2)) * np.cos(ph_o * 12.0)
    y_imp = oy + oh * 0.50 - (oh * 0.38) * imp_env
    segs_imp = np.empty((len(xs_osc) - 1, 4), dtype=np.float32)
    segs_imp[:, 0], segs_imp[:, 1] = x_px[:-1], y_imp[:-1]
    segs_imp[:, 2], segs_imp[:, 3] = x_px[1:], y_imp[1:]
    py5.stroke(*RUBY_HIGH)
    py5.stroke_weight(1.8)
    py5.lines(segs_imp)

    py5.no_stroke()
    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(12)
    py5.text(
        "GOLD: BALANCE WHEEL ANGLE THETA(t) // RUBY: VIBROGRAPH UNLOCK-IMPULSE-DROP ACOUSTIC TRANSIENTS",
        ox + 4, oy + oh + 14,
    )


def draw_header_and_footer(tau):
    py5.stroke(224, 214, 194, 130)
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
        "BREGUET TOURBILLON REGULATOR & SWISS LEVER ESCAPEMENT CHRONOMETER",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "BREVET DU 7 MESSIDOR AN IX (1801), PHILLIPS TERMINAL OVERCOIL (1861) & DETACHED RUBY-PALLET ESCAPEMENT",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "3-ARM ROTATING TOURBILLON CAGE // 15-TOOTH CLUB-FOOT ESCAPE WHEEL // GLUCYDUR BALANCE & BLUED PHILLIPS SPIRAL",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K HOROLOGICAL MICRO-KINETICS // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_VELLUM)

    draw_header_and_footer(tau)
    draw_tourbillon_medallion(tau)
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


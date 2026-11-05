# py5 Media Art — Autonomous Animation
# Work: kinetic_ferrite_magnetic_core_matrix_coincident_current_memory_2d
# Genre: Signal / Glitch / Digital Artifacts (Genre 3)
# Background Polarity: Dark (#060912 Deep MIT Whirlwind & Apollo AGC Backplane Obsidian)

from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import py5

WORK_NAME = "kinetic_ferrite_magnetic_core_matrix_coincident_current_memory_2d"
SIZE = (3840, 2160)
FPS = 60
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC  # 720 frames

OUT_DIR = Path(__file__).parent
FRAMES_DIR = OUT_DIR / "frames"
PREVIEW_PATH = OUT_DIR / f"{WORK_NAME}_p1.png"
VIDEO_PATH = OUT_DIR / "output.mp4"

# Palette — Deep MIT Whirlwind & Apollo AGC Backplane Obsidian (#060912)
BG_OBSIDIAN = (6, 9, 18)
CARD_BG = (11, 16, 30)
CARD_HEADER_BG = (17, 25, 45)
VIEWPORT_BG = (8, 12, 23)
CERAMIC_FRAME = (22, 31, 52)
CERAMIC_INNER = (13, 19, 35)

# Hardware & Signal Chromatics
GOLD_PIN = (246, 186, 58)
GOLD_BRIGHT = (255, 224, 122)
GOLD_DARK = (164, 114, 28)

X_BUS_AMBER = (252, 168, 42)
X_BUS_DIM = (118, 78, 26)
Y_BUS_CYAN = (40, 216, 254)
Y_BUS_DIM = (24, 96, 126)
SENSE_RUBY = (248, 52, 132)
SENSE_DIM = (116, 28, 68)
INHIBIT_EMERALD = (24, 232, 164)
INHIBIT_DIM = (18, 96, 72)

# Ferrite Toroid States (+Br = Bit 1, -Br = Bit 0, Switching Avalanche)
FERRITE_BODY = (38, 46, 66)
FERRITE_RIM = (76, 90, 122)
BIT1_CORE = (246, 146, 38)
BIT1_GLOW = (255, 206, 86)
BIT0_CORE = (32, 118, 216)
BIT0_GLOW = (76, 184, 255)
SWITCH_AVALANCHE = (250, 56, 138)
HALF_SELECT_TINT = (168, 112, 248)

INK_IVORY = (236, 240, 248)
INK_SILVER = (166, 178, 204)
INK_MUTED = (106, 120, 148)
GRID_LINE = (24, 34, 58)
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

# 12x12 Coincident-Current Ferrite Matrix Geometry
N_GRID = 12
GRID_SPAN = 770.0  # spans [-385, +385] inside the 678px radius circle
CELL_STEP = GRID_SPAN / (N_GRID - 1)  # 70.0 px spacing
CORE_R_OUT = 23.5
CORE_R_IN = 11.2

# Runtime seed and precomputed geometry
SEED_OFFSET = 0
FONT_MONO = None
FONT_SANS = None

# Precomputed 12x12 initial bit matrix (Apollo AGC LUMINARY 116 12-bit instruction table)
AGC_WORDS_12BIT = [
    (0o5421, "TCF   LUNAR_LAND"),
    (0o3146, "CA    ALT_RATE"),
    (0o6253, "AD    THRUST_CMD"),
    (0o1532, "CCS   PITCH_ERR"),
    (0o0006, "EXTEND          "),
    (0o4715, "DV    MASS_PROP"),
    (0o3624, "DCA   VEL_VECTOR"),
    (0o2351, "DAS   GUID_ACCUM"),
    (0o5163, "INDEX GIMBAL_PTR"),
    (0o1645, "BZF   THROTTLE_Q"),
    (0o6512, "BZMF  ABORT_CHK"),
    (0o4271, "NDX   KALMAN_WGT"),
]

INITIAL_BITS = np.zeros((N_GRID, N_GRID), dtype=np.int32)
for r_idx, (oct_val, _) in enumerate(AGC_WORDS_12BIT):
    for c_idx in range(N_GRID):
        INITIAL_BITS[r_idx, c_idx] = (oct_val >> (N_GRID - 1 - c_idx)) & 1

# Precomputed unit circle tables for fast vectorized toroid rendering
N_TOROID_SEG = 28
THETA_TOROID = np.linspace(0.0, 2.0 * np.pi, N_TOROID_SEG + 1, dtype=np.float32)
COS_T = np.cos(THETA_TOROID)
SIN_T = np.sin(THETA_TOROID)


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


def draw_frame_border_and_header(phi: float, active_r: int, active_c: int, cycle_phase: float):
    # Outer architectural frame
    py5.no_fill()
    py5.stroke(*BORDER_SLATE, 220)
    py5.stroke_weight(2.0)
    py5.rect(42, 36, W - 84, H - 72, 8)
    py5.stroke(*GOLD_PIN, 130)
    py5.stroke_weight(1.0)
    py5.rect(50, 44, W - 100, H - 88, 6)

    # Top title banner
    py5.fill(*CARD_HEADER_BG, 235)
    py5.stroke(*BORDER_SLATE, 210)
    py5.stroke_weight(1.5)
    py5.rect(84, 58, W - 168, 94, 6)

    # Title typography
    py5.text_font(FONT_SANS)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(27)
    py5.text(
        "COINCIDENT-CURRENT FERRITE MAGNETIC CORE MATRIX MEMORY // MIT WHIRLWIND & APOLLO AGC BLOCK II",
        114,
        72,
    )

    py5.text_font(FONT_MONO)
    py5.fill(*INK_SILVER)
    py5.text_size(16)
    oct_word, mnemonic = AGC_WORDS_12BIT[active_r]
    if cycle_phase < 0.38:
        mode_str = "DESTRUCTIVE READ (+Im/2 COINCIDENCE)"
    elif cycle_phase < 0.52:
        mode_str = "SENSE STROBE DISCRIMINATION (dPhi/dt)"
    elif cycle_phase < 0.88:
        mode_str = "RESTORE / WRITE (-Im/2 + INHIBIT)"
    else:
        mode_str = "POST-WRITE FLUX RELAXATION"

    py5.text(
        f"PLANE: 12x12 MnZnFe2O4 TOROID ARRAY (4-WIRE 3D)   |   ADDR: [X_{active_c:02d}, Y_{active_r:02d}]   "
        f"|   WORD {active_r:02d}: {oct_word:04o}o ({mnemonic.strip()})   |   STATE: {mode_str}",
        114,
        114,
    )

    # Right header badge
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.fill(*Y_BUS_CYAN)
    py5.text_size(17)
    py5.text("US PAT. 2,736,880 (J. W. FORRESTER, 1951) // HC = 1.35 Oe, BR = 2.15 kG", W - 114, 76)
    py5.fill(*SENSE_RUBY)
    py5.text_size(15)
    py5.text(f"CYCLE T_c = 11.7 us   |   STROBE WINDOW = 0.48 us   |   PHASE = {phi / (2.0 * np.pi) * 100.0:05.1f}%", W - 114, 114)


def draw_flank_card(x: float, y: float, w: float, h: float, code1: str, title1: str, code2: str, title2: str):
    py5.fill(*CARD_BG, 242)
    py5.stroke(*BORDER_SLATE, 220)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    # Top sub-header
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, y + 2, w - 4, 42, 6)
    py5.stroke(*BORDER_SLATE, 180)
    py5.stroke_weight(1.0)
    py5.line(x, y + 44, x + w, y + 44)

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.fill(*GOLD_PIN)
    py5.text_size(16)
    py5.text(code1, x + 18, y + 23)
    py5.fill(*INK_IVORY)
    py5.text_size(16)
    py5.text(title1, x + 112, y + 23)

    # Mid divider + second sub-header
    mid_y = y + h * 0.5
    py5.fill(*CARD_HEADER_BG)
    py5.no_stroke()
    py5.rect(x + 2, mid_y, w - 4, 42)
    py5.stroke(*BORDER_SLATE, 180)
    py5.stroke_weight(1.0)
    py5.line(x, mid_y, x + w, mid_y)
    py5.line(x, mid_y + 42, x + w, mid_y + 42)

    py5.fill(*GOLD_PIN)
    py5.text(code2, x + 18, mid_y + 21)
    py5.fill(*INK_IVORY)
    py5.text(title2, x + 112, mid_y + 21)


def draw_central_ferrite_matrix_medallion(phi: float, active_r: int, active_c: int, cycle_phase: float, bit_val: int):
    # Outer recessed shadow & ceramic carrier ring
    py5.fill(*CERAMIC_FRAME)
    py5.stroke(*BORDER_SLATE, 240)
    py5.stroke_weight(2.6)
    py5.circle(CX, CY, MEDALLION_R * 2.0)

    # Gold-plated perimeter pin ring ticks (64 wire-wrap terminals)
    n_pins = 64
    angles = np.linspace(0.0, 2.0 * np.pi, n_pins, endpoint=False)
    r_p1 = INNER_R + 6.0
    r_p2 = MEDALLION_R - 8.0
    segs = np.zeros((n_pins, 4), dtype=np.float32)
    segs[:, 0] = CX + r_p1 * np.cos(angles)
    segs[:, 1] = CY + r_p1 * np.sin(angles)
    segs[:, 2] = CX + r_p2 * np.cos(angles)
    segs[:, 3] = CY + r_p2 * np.sin(angles)
    py5.stroke(*GOLD_PIN, 175)
    py5.stroke_weight(2.2)
    py5.lines(segs)

    # Inner dark backplane recess
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*GOLD_PIN, 210)
    py5.stroke_weight(2.0)
    py5.circle(CX, CY, INNER_R * 2.0)

    # Subtle polar & Cartesian reference grid inside viewport
    py5.stroke(*GRID_LINE, 140)
    py5.stroke_weight(1.0)
    py5.no_fill()
    for rad in (220.0, 440.0, 620.0):
        py5.circle(CX, CY, rad * 2.0)

    # Compute 12x12 grid coordinates
    x0 = CX - GRID_SPAN * 0.5
    y0 = CY - GRID_SPAN * 0.5
    xs = x0 + np.arange(N_GRID, dtype=np.float32) * CELL_STEP
    ys = y0 + np.arange(N_GRID, dtype=np.float32) * CELL_STEP

    # Determine electrical currents at current cycle_phase in [0, 1)
    # 0.00..0.38: Read (+Im/2 on X_c and Y_r)
    # 0.38..0.52: Sense Strobe peak
    # 0.52..0.88: Restore/Write (-Im/2 on X_c and Y_r; +Im/2 on Inhibit if bit_val == 0)
    # 0.88..1.00: Relaxation
    read_env = np.exp(-((cycle_phase - 0.22) / 0.12) ** 2)
    write_env = np.exp(-((cycle_phase - 0.70) / 0.12) ** 2)
    strobe_env = np.exp(-((cycle_phase - 0.36) / 0.065) ** 2)
    inhibit_active = (bit_val == 0) and (0.50 <= cycle_phase <= 0.88)

    # 1. Draw Inhibit Winding (Emerald bus running parallel to rows with serpentine turnarounds)
    inhibit_segs = []
    for r in range(N_GRID):
        yc = ys[r] - 7.5
        inhibit_segs.append([x0 - 52.0, yc, x0 + GRID_SPAN + 52.0, yc])
        if r < N_GRID - 1:
            turn_x = x0 + GRID_SPAN + 52.0 if (r % 2 == 0) else x0 - 52.0
            inhibit_segs.append([turn_x, yc, turn_x, ys[r + 1] - 7.5])
    inhibit_arr = np.array(inhibit_segs, dtype=np.float32)
    if inhibit_active:
        py5.stroke(*INHIBIT_EMERALD, int(130 + 115 * write_env))
        py5.stroke_weight(2.2)
    else:
        py5.stroke(*INHIBIT_DIM, 130)
        py5.stroke_weight(1.4)
    py5.lines(inhibit_arr)

    # 2. Draw Horizontal Y-Select Drive Wires (Cyan bus lines) & Vertical X-Select Drive Wires (Amber-Gold bus lines)
    for r in range(N_GRID):
        yc = ys[r]
        is_sel_r = (r == active_r)
        if is_sel_r:
            py5.stroke(*Y_BUS_CYAN, 250)
            py5.stroke_weight(3.6)
        else:
            py5.stroke(*Y_BUS_DIM, 165)
            py5.stroke_weight(1.7)
        py5.line(x0 - 68.0, yc, x0 + GRID_SPAN + 68.0, yc)

        # Row terminal pad & label
        py5.fill(*(Y_BUS_CYAN if is_sel_r else CERAMIC_FRAME))
        py5.stroke(*(GOLD_BRIGHT if is_sel_r else BORDER_SLATE))
        py5.stroke_weight(1.4)
        py5.rect(x0 - 114.0, yc - 10.0, 42.0, 20.0, 3)
        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*(BG_OBSIDIAN if is_sel_r else INK_SILVER))
        py5.text_size(11)
        py5.text(f"Y{r:02d}", x0 - 93.0, yc)

    for c in range(N_GRID):
        xc = xs[c]
        is_sel_c = (c == active_c)
        if is_sel_c:
            py5.stroke(*X_BUS_AMBER, 250)
            py5.stroke_weight(3.6)
        else:
            py5.stroke(*X_BUS_DIM, 165)
            py5.stroke_weight(1.7)
        py5.line(xc, y0 - 68.0, xc, y0 + GRID_SPAN + 68.0)

        # Column terminal pad & label
        py5.fill(*(X_BUS_AMBER if is_sel_c else CERAMIC_FRAME))
        py5.stroke(*(GOLD_BRIGHT if is_sel_c else BORDER_SLATE))
        py5.stroke_weight(1.4)
        py5.rect(xc - 21.0, y0 - 102.0, 42.0, 20.0, 3)
        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*(BG_OBSIDIAN if is_sel_c else INK_SILVER))
        py5.text_size(11)
        py5.text(f"X{c:02d}", xc, y0 - 92.0)

    # 3. Draw Checkerboard Diagonal Sense Wire (Ruby-magenta noise-canceling weave through all 144 cores)
    sense_segs = []
    for r in range(N_GRID):
        for c in range(N_GRID):
            xc, yc = xs[c], ys[r]
            orient = 1.0 if ((r + c) % 2 == 0) else -1.0
            d = CELL_STEP * 0.48
            sense_segs.append([xc - d, yc - orient * d, xc + d, yc + orient * d])
    sense_arr = np.array(sense_segs, dtype=np.float32)
    sense_glow = strobe_env if bit_val == 1 else strobe_env * 0.35
    py5.stroke(*SENSE_RUBY, int(145 + 110 * sense_glow))
    py5.stroke_weight(1.8 + 1.6 * sense_glow)
    py5.lines(sense_arr)

    # 4. Batch-Render all 144 Sintered Ferrite Toroid Cores via py5.QUADS
    r_mid = 0.5 * (CORE_R_OUT + CORE_R_IN)
    cos0, sin0 = COS_T[:-1], SIN_T[:-1]
    cos1, sin1 = COS_T[1:], SIN_T[1:]

    # Unit ring quad template (N_TOROID_SEG x 4 x 2)
    q_inner_unit = np.zeros((N_TOROID_SEG * 4, 2), dtype=np.float32)
    q_inner_unit[0::4, 0] = CORE_R_IN * cos0
    q_inner_unit[0::4, 1] = CORE_R_IN * sin0
    q_inner_unit[1::4, 0] = r_mid * cos0
    q_inner_unit[1::4, 1] = r_mid * sin0
    q_inner_unit[2::4, 0] = r_mid * cos1
    q_inner_unit[2::4, 1] = r_mid * sin1
    q_inner_unit[3::4, 0] = CORE_R_IN * cos1
    q_inner_unit[3::4, 1] = CORE_R_IN * sin1

    q_outer_unit = np.zeros((N_TOROID_SEG * 4, 2), dtype=np.float32)
    q_outer_unit[0::4, 0] = r_mid * cos0
    q_outer_unit[0::4, 1] = r_mid * sin0
    q_outer_unit[1::4, 0] = CORE_R_OUT * cos0
    q_outer_unit[1::4, 1] = CORE_R_OUT * sin0
    q_outer_unit[2::4, 0] = CORE_R_OUT * cos1
    q_outer_unit[2::4, 1] = CORE_R_OUT * sin1
    q_outer_unit[3::4, 0] = r_mid * cos1
    q_outer_unit[3::4, 1] = r_mid * sin1

    # Group toroid quads by state color bin for ultra-fast single-pass QUADS rendering per bin
    bins = {
        "switch_inner": (SWITCH_AVALANCHE, []),
        "switch_outer": (GOLD_BRIGHT, []),
        "half1_inner": ((218, 134, 118), []),
        "half0_inner": ((96, 115, 232), []),
        "bit1_inner": (BIT1_CORE, []),
        "bit1_outer": ((88, 72, 62), []),
        "bit0_inner": (BIT0_CORE, []),
        "bit0_outer": ((42, 64, 98), []),
        "spec_arc1": (BIT1_GLOW, []),
        "spec_arc0": (BIT0_GLOW, []),
    }

    # Rotating azimuthal flux highlight slice (8 segments of the inner ring)
    rot_idx = int((phi / (2.0 * np.pi)) * N_TOROID_SEG) % N_TOROID_SEG

    for r in range(N_GRID):
        yc = ys[r]
        is_r = (r == active_r)
        for c in range(N_GRID):
            xc = xs[c]
            is_c = (c == active_c)
            b_orig = INITIAL_BITS[r, c]
            offset = np.array([xc, yc], dtype=np.float32)

            if is_r and is_c:
                cur_bit = 0 if (0.26 <= cycle_phase <= 0.64) else b_orig
                is_coincident = True
                is_half = False
            elif is_r or is_c:
                cur_bit = b_orig
                is_coincident = False
                is_half = True
            else:
                cur_bit = b_orig
                is_coincident = False
                is_half = False

            q_in = q_inner_unit + offset
            q_out = q_outer_unit + offset

            if is_coincident and (0.16 <= cycle_phase <= 0.44 or (b_orig == 1 and 0.58 <= cycle_phase <= 0.82)):
                bins["switch_inner"][1].append(q_in)
                bins["switch_outer"][1].append(q_out)
            elif is_half:
                if cur_bit == 1:
                    bins["half1_inner"][1].append(q_in)
                    bins["bit1_outer"][1].append(q_out)
                else:
                    bins["half0_inner"][1].append(q_in)
                    bins["bit0_outer"][1].append(q_out)
            else:
                if cur_bit == 1:
                    bins["bit1_inner"][1].append(q_in)
                    bins["bit1_outer"][1].append(q_out)
                else:
                    bins["bit0_inner"][1].append(q_in)
                    bins["bit0_outer"][1].append(q_out)

            # Add rotating magnetic domain specular arc (6 segments)
            s_seg = (rot_idx + r + c) % N_TOROID_SEG if cur_bit == 1 else (N_TOROID_SEG - rot_idx + r + c) % N_TOROID_SEG
            if s_seg + 5 <= N_TOROID_SEG:
                arc_q = q_in[s_seg * 4 : (s_seg + 5) * 4]
                if cur_bit == 1:
                    bins["spec_arc1"][1].append(arc_q)
                else:
                    bins["spec_arc0"][1].append(arc_q)

    py5.no_stroke()
    for b_col, b_list in bins.values():
        if b_list:
            v_all = np.vstack(b_list)
            py5.fill(*b_col, 255)
            with py5.begin_shape(py5.QUADS):
                py5.vertices(v_all)

    # 5. Draw Over-Pass Wire Bridges through each Toroid Aperture (authentic physical over/under weave!)
    over_x_segs = []
    over_y_segs = []
    for r in range(N_GRID):
        yc = ys[r]
        for c in range(N_GRID):
            xc = xs[c]
            # Alternating checkerboard over/under pass across the toroid rim
            if (r + c) % 2 == 0:
                over_x_segs.append([xc, yc - CORE_R_OUT - 3.0, xc, yc + CORE_R_OUT + 3.0])
            else:
                over_y_segs.append([xc - CORE_R_OUT - 3.0, yc, xc + CORE_R_OUT + 3.0, yc])

    py5.stroke(*X_BUS_AMBER, 215)
    py5.stroke_weight(2.0)
    py5.lines(np.array(over_x_segs, dtype=np.float32))

    py5.stroke(*Y_BUS_CYAN, 215)
    py5.stroke_weight(2.0)
    py5.lines(np.array(over_y_segs, dtype=np.float32))

    # 6. Highlight the Active Coincident Address Intersection [active_c, active_r]
    ax = xs[active_c]
    ay = ys[active_r]
    pulse_r = CORE_R_OUT + 8.0 + 5.0 * np.sin(phi * 6.0)
    py5.no_fill()
    py5.stroke(*GOLD_BRIGHT, 245)
    py5.stroke_weight(2.6)
    py5.circle(ax, ay, pulse_r * 2.0)

    # Propagating Sense Voltage Wave Packet along the diagonal Sense line during Strobe
    if strobe_env > 0.04:
        wave_dist = ((cycle_phase - 0.22) / 0.28) * 420.0
        if wave_dist > 0.0:
            py5.stroke(*SENSE_RUBY, int(245 * strobe_env))
            py5.stroke_weight(3.2)
            py5.circle(ax, ay, (CORE_R_OUT + min(wave_dist, 145.0)) * 2.0)

    # Bottom viewport telemetry caption inside the medallion rim
    py5.fill(*CARD_HEADER_BG, 230)
    py5.stroke(*GOLD_PIN, 180)
    py5.stroke_weight(1.4)
    py5.rect(CX - 340.0, CY + GRID_SPAN * 0.5 + 82.0, 680.0, 52.0, 6)
    py5.text_font(FONT_MONO)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(14)
    vs_mv = 64.8 * strobe_env if bit_val == 1 else 8.4 * strobe_env
    py5.text(
        f"COINCIDENT CELL ({active_c:02d},{active_r:02d})  |  STORED BIT = {bit_val}  |  "
        f"I_total = {(read_env - write_env) * 820.0:+06.1f} mA  |  V_sense = {vs_mv:04.1f} mV",
        CX,
        CY + GRID_SPAN * 0.5 + 108.0,
    )


def draw_left_top_card(phi: float, cycle_phase: float, bit_val: int):
    x, y, w, h = LEFT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 01",
        "SQUARE-LOOP FERRITE B-H HYSTERESIS (MnZnFe2O4)",
        "FIG. 02",
        "SINGLE TOROID 4-WIRE 3D INTERLACE & FLUX VECTOR",
    )

    # --- FIG. 01: B-H Hysteresis Loop ---
    bx, by, bw, bh = x + 36.0, y + 64.0, 540.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(bx, by, bw, bh, 6)

    cx_h = bx + bw * 0.5
    cy_h = by + bh * 0.5
    # Grid & axes
    py5.stroke(*GRID_LINE, 180)
    py5.stroke_weight(1.0)
    for dx in (-180.0, -90.0, 90.0, 180.0):
        py5.line(cx_h + dx, by + 16, cx_h + dx, by + bh - 16)
    for dy in (-120.0, -60.0, 60.0, 120.0):
        py5.line(bx + 16, cy_h + dy, bx + bw - 16, cy_h + dy)
    py5.stroke(*INK_MUTED, 210)
    py5.stroke_weight(1.5)
    py5.line(bx + 18, cy_h, bx + bw - 18, cy_h)
    py5.line(cx_h, by + 18, cx_h, by + bh - 18)

    # Coercive threshold dashed vertical markers (-Hc, -Hm/2, +Hm/2, +Hc)
    hc_px = 112.0
    hm_px = 188.0
    br_px = 112.0
    py5.stroke(*X_BUS_AMBER, 140)
    py5.stroke_weight(1.2)
    for x_mark in (-hm_px, -hc_px, -hm_px * 0.5, hm_px * 0.5, hc_px, hm_px):
        py5.line(cx_h + x_mark, by + 24, cx_h + x_mark, by + bh - 24)

    # Parametric Square-Loop Ferrite Hysteresis curve
    t_vals = np.linspace(0.0, 2.0 * np.pi, 160, dtype=np.float32)
    h_curve = hm_px * np.cos(t_vals)
    b_curve = br_px * np.tanh(3.2 * np.sin(t_vals) + 1.85 * np.cos(t_vals))
    pts_bh = np.column_stack((cx_h + h_curve, cy_h - b_curve))
    segs_bh = np.hstack((pts_bh[:-1], pts_bh[1:]))
    py5.stroke(*Y_BUS_CYAN, 235)
    py5.stroke_weight(2.6)
    py5.lines(segs_bh)

    # Remanent state nodes (+Br = Bit 1, -Br = Bit 0)
    py5.fill(*BIT1_CORE)
    py5.stroke(*GOLD_BRIGHT)
    py5.stroke_weight(1.8)
    py5.circle(cx_h, cy_h - br_px * 0.94, 13)
    py5.fill(*BIT0_CORE)
    py5.circle(cx_h, cy_h + br_px * 0.94, 13)

    # Live operating point on the B-H curve
    theta_op = cycle_phase * 2.0 * np.pi
    op_x = cx_h + hm_px * np.cos(theta_op)
    op_y = cy_h - br_px * np.tanh(3.2 * np.sin(theta_op) + 1.85 * np.cos(theta_op))
    py5.fill(*SENSE_RUBY)
    py5.stroke(*INK_IVORY)
    py5.stroke_weight(2.0)
    py5.circle(op_x, op_y, 16)

    # Labels inside B-H plot
    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.fill(*GOLD_BRIGHT)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("+Br (BIT 1)", cx_h + 10, cy_h - br_px - 14)
    py5.fill(*Y_BUS_CYAN)
    py5.text("-Br (BIT 0)", cx_h + 10, cy_h + br_px - 4)
    py5.fill(*INK_SILVER)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text("-Hm", cx_h - hm_px, cy_h + 6)
    py5.text("-Hc", cx_h - hc_px, cy_h + 6)
    py5.text("+Hm/2", cx_h + hm_px * 0.5, cy_h + 6)
    py5.text("+Hc", cx_h + hc_px, cy_h + 6)
    py5.text("+Hm", cx_h + hm_px, cy_h + 6)

    # Right side explanatory telemetry panel of FIG. 01
    rx = bx + bw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(15)
    py5.text("SQUARE-LOOP COINCIDENCE", rx, by + 8)
    py5.fill(*INK_SILVER)
    py5.text_size(13)
    specs_f1 = [
        ("MATERIAL", "Mn0.6Zn0.4Fe2O4"),
        ("SQUARENESS Rs", "Br / Bmax = 0.91"),
        ("COERCIVITY Hc", "1.35 Oersted"),
        ("REMANENCE Br", "2.15 kiloGauss"),
        ("HALF-SELECT", "Hm/2 = 0.82 Oe < Hc"),
        ("FULL-SELECT", "Hm = 1.64 Oe > Hc"),
        ("PEAKING TIME", "t_p = 0.48 us"),
        ("SWITCHING TIME", "t_s = 0.95 us"),
        ("ACTIVE BIT", f"STATE = {bit_val} ({'+Br' if bit_val == 1 else '-Br'})"),
    ]
    for i, (k_lbl, v_lbl) in enumerate(specs_f1):
        yy = by + 44.0 + i * 32.0
        py5.fill(*INK_MUTED)
        py5.text(k_lbl, rx, yy)
        py5.fill(*(GOLD_BRIGHT if i == 8 else INK_IVORY))
        py5.text(v_lbl, rx + 158.0, yy)

    # --- FIG. 02: Single Toroid 4-Wire Interlace Diagram ---
    mid_y = y + h * 0.5
    tx, ty, tw, th = x + 36.0, mid_y + 62.0, 540.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(tx, ty, tw, th, 6)

    tcx = tx + tw * 0.5
    tcy = ty + th * 0.5
    r_big = 124.0
    r_hole = 58.0

    # Under-wires passing behind the toroid
    py5.stroke(*X_BUS_AMBER, 235)
    py5.stroke_weight(4.5)
    py5.line(tcx - 190, tcy - 14, tcx + 190, tcy - 14)
    py5.stroke(*Y_BUS_CYAN, 235)
    py5.line(tcx - 14, tcy - 150, tcx - 14, tcy + 150)
    py5.stroke(*INHIBIT_EMERALD, 235)
    py5.stroke_weight(3.5)
    py5.line(tcx - 190, tcy + 18, tcx + 190, tcy + 18)
    py5.stroke(*SENSE_RUBY, 240)
    py5.line(tcx - 135, tcy - 135, tcx + 135, tcy + 135)

    # Draw macro ferrite toroid body
    py5.fill(*FERRITE_BODY)
    py5.stroke(*GOLD_PIN, 230)
    py5.stroke_weight(2.5)
    py5.circle(tcx, tcy, r_big * 2.0)

    # Circumferential magnetic flux arrows inside the ferrite ring
    n_flux = 16
    f_ang = np.linspace(0.0, 2.0 * np.pi, n_flux, endpoint=False) + (1.0 if bit_val == 1 else -1.0) * phi
    r_f = 0.5 * (r_big + r_hole)
    py5.stroke(*(BIT1_GLOW if bit_val == 1 else BIT0_GLOW), 230)
    py5.stroke_weight(2.2)
    py5.no_fill()
    py5.circle(tcx, tcy, r_f * 2.0)
    for a in f_ang:
        px = tcx + r_f * np.cos(a)
        py = tcy + r_f * np.sin(a)
        py5.fill(*(BIT1_GLOW if bit_val == 1 else BIT0_GLOW))
        py5.no_stroke()
        py5.circle(px, py, 7.0)

    # Inner aperture hole
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*GOLD_PIN, 210)
    py5.stroke_weight(2.0)
    py5.circle(tcx, tcy, r_hole * 2.0)

    # Over-wire bridges passing through the inner aperture and over top/right rim
    py5.stroke(*X_BUS_AMBER, 255)
    py5.stroke_weight(4.5)
    py5.line(tcx - r_hole + 6, tcy - 14, tcx + r_big + 18, tcy - 14)
    py5.stroke(*Y_BUS_CYAN, 255)
    py5.line(tcx - 14, tcy - r_big - 18, tcx - 14, tcy + r_hole - 6)
    py5.stroke(*SENSE_RUBY, 255)
    py5.stroke_weight(3.5)
    py5.line(tcx - 36, tcy - 36, tcx + 98, tcy + 98)

    # Right telemetry legend for FIG. 02
    rx2 = tx + tw + 26.0
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(15)
    py5.text("3D 4-WIRE CONDUCTORS", rx2, ty + 8)
    wire_items = [
        (X_BUS_AMBER, "1. X-DRIVE LINE (AWG 38)", "Half-select Ix = +/- 410 mA"),
        (Y_BUS_CYAN, "2. Y-DRIVE LINE (AWG 38)", "Half-select Iy = +/- 410 mA"),
        (SENSE_RUBY, "3. DIAGONAL SENSE WIRE", "Induced EMF Vs = -dPhi/dt"),
        (INHIBIT_EMERALD, "4. INHIBIT WINDING (Iz)", "Cancels Write if Bit = 0"),
    ]
    for i, (wcol, wtitle, wdesc) in enumerate(wire_items):
        yy = ty + 48.0 + i * 74.0
        py5.fill(*wcol)
        py5.no_stroke()
        py5.rect(rx2, yy + 3, 16, 16, 3)
        py5.fill(*INK_IVORY)
        py5.text_size(13)
        py5.text(wtitle, rx2 + 26.0, yy)
        py5.fill(*INK_SILVER)
        py5.text_size(12)
        py5.text(wdesc, rx2 + 26.0, yy + 22.0)


def draw_left_bottom_card(phi: float, cycle_phase: float):
    x, y, w, h = LEFT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 03",
        "SENSE AMPLIFIER STROBE & DELTA-NOISE DISCRIMINATION",
        "FIG. 04",
        "WHIRLWIND & APOLLO AGC FERRITE HARDWARE PALETTE",
    )

    # --- FIG. 03: Sense Voltage Peaking vs. Half-Select Shuttle Noise ---
    sx, sy, sw, sh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(sx, sy, sw, sh, 6)

    base_y = sy + sh - 56.0
    left_p = sx + 68.0
    plot_w = sw - 104.0

    # Grid lines
    py5.stroke(*GRID_LINE, 180)
    py5.stroke_weight(1.0)
    for frac in (0.2, 0.4, 0.6, 0.8):
        py5.line(left_p + plot_w * frac, sy + 20, left_p + plot_w * frac, base_y)
    for dy in (60.0, 120.0, 180.0, 240.0):
        py5.line(left_p, base_y - dy, left_p + plot_w, base_y - dy)

    # Strobe time window highlight band (t = 0.42 .. 0.54 us)
    st_x1 = left_p + plot_w * 0.42
    st_x2 = left_p + plot_w * 0.54
    py5.fill(*GOLD_PIN, 42)
    py5.stroke(*GOLD_BRIGHT, 190)
    py5.stroke_weight(1.4)
    py5.rect(st_x1, sy + 22, st_x2 - st_x1, base_y - sy - 22)

    # Curves: 1) Switching Voltage ("1" -> "0", peaks at t=0.48us, ~65mV)
    #         2) Half-Select / "0" Disturb Shuttle Spike (peaks early at t=0.16us, ~18mV, decays before Strobe!)
    t_arr = np.linspace(0.0, 1.0, 180, dtype=np.float32)
    px_arr = left_p + t_arr * plot_w
    v_one = 228.0 * np.exp(-((t_arr - 0.48) / 0.14) ** 2) + 46.0 * np.exp(-((t_arr - 0.15) / 0.05) ** 2)
    v_zero = 78.0 * np.exp(-((t_arr - 0.15) / 0.055) ** 2) + 12.0 * np.exp(-((t_arr - 0.48) / 0.16) ** 2)

    pts_one = np.column_stack((px_arr, base_y - v_one))
    pts_zero = np.column_stack((px_arr, base_y - v_zero))
    py5.stroke(*SENSE_RUBY, 245)
    py5.stroke_weight(3.0)
    py5.lines(np.hstack((pts_one[:-1], pts_one[1:])))

    py5.stroke(*Y_BUS_CYAN, 225)
    py5.stroke_weight(2.4)
    py5.lines(np.hstack((pts_zero[:-1], pts_zero[1:])))

    # Threshold discriminator line (V_thresh = 32 mV)
    py5.stroke(*INHIBIT_EMERALD, 200)
    py5.stroke_weight(1.5)
    py5.line(left_p, base_y - 115.0, left_p + plot_w, base_y - 115.0)

    # Animated sweep cursor
    cur_x = left_p + ((cycle_phase * 2.0) % 1.0) * plot_w
    py5.stroke(*GOLD_BRIGHT, 230)
    py5.stroke_weight(1.8)
    py5.line(cur_x, sy + 22, cur_x, base_y)

    # Labels inside FIG. 03
    py5.text_font(FONT_MONO)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.fill(*SENSE_RUBY)
    py5.text("SWITCHING EMF ('1' -> '0' FLUX REVERSAL: 65 mV AT t_p = 0.48 us)", left_p + 16, sy + 28)
    py5.fill(*Y_BUS_CYAN)
    py5.text("ELASTIC DISTURB ('0' + HALF-SELECT DELTA NOISE: < 9 mV AT STROBE)", left_p + 16, sy + 50)
    py5.fill(*INHIBIT_EMERALD)
    py5.text("DISCRIMINATOR THRESHOLD V_th = 32.0 mV", left_p + plot_w - 310, base_y - 134)
    py5.fill(*GOLD_BRIGHT)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text("STROBE", 0.5 * (st_x1 + st_x2), sy + 76)
    py5.fill(*INK_SILVER)
    py5.text("t = 0.0 us", left_p + 20, base_y + 12)
    py5.text("t_d = 0.15 us (SHUTTLE)", left_p + plot_w * 0.18, base_y + 12)
    py5.text("t_p = 0.48 us (STROBE)", left_p + plot_w * 0.48, base_y + 12)
    py5.text("t_s = 1.00 us", left_p + plot_w - 30, base_y + 12)

    # --- FIG. 04: Hardware Chromatic Palette Swatches ---
    mid_y = y + h * 0.5
    swatches = [
        (BIT1_CORE, "REMANENT +Br (BIT 1)", "#F69226 // CW FLUX"),
        (BIT0_CORE, "REMANENT -Br (BIT 0)", "#2076D8 // CCW FLUX"),
        (X_BUS_AMBER, "X-ADDRESS BUS (Ix)", "#FCA82A // +Im/2 COL"),
        (Y_BUS_CYAN, "Y-ADDRESS BUS (Iy)", "#28D8FE // +Im/2 ROW"),
        (SENSE_RUBY, "DIAGONAL SENSE LINE", "#F83484 // dPhi/dt"),
        (INHIBIT_EMERALD, "INHIBIT WINDING (Iz)", "#18E8A4 // WRITE 0"),
    ]
    sw_w = (w - 96.0) / 3.0
    sw_h = 152.0
    for i, (scol, sname, sdesc) in enumerate(swatches):
        col_i = i % 3
        row_i = i // 3
        bx_s = x + 36.0 + col_i * (sw_w + 12.0)
        by_s = mid_y + 62.0 + row_i * (sw_h + 18.0)
        py5.fill(*VIEWPORT_BG)
        py5.stroke(*BORDER_SLATE, 190)
        py5.stroke_weight(1.4)
        py5.rect(bx_s, by_s, sw_w, sw_h, 6)

        py5.fill(*scol)
        py5.no_stroke()
        py5.rect(bx_s + 14, by_s + 14, sw_w - 28, 66, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.fill(*INK_IVORY)
        py5.text_size(13)
        py5.text(sname, bx_s + 14, by_s + 92)
        py5.fill(*INK_SILVER)
        py5.text_size(12)
        py5.text(sdesc, bx_s + 14, by_s + 116)


def draw_right_top_card(phi: float, active_r: int):
    x, y, w, h = RIGHT_X, TOP_CARD_Y, CARD_W, TOP_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 05",
        "APOLLO AGC BLOCK II WOVEN CORE ROPE ROM ('LOL MEMORY')",
        "FIG. 06",
        "NON-VOLATILE MAGNETIC CORE MEMORY TAXONOMY (1949-1966)",
    )

    # --- FIG. 05: Woven Core Rope Fixed Memory Diagram (1 Core = 192 Bits!) ---
    rx, ry, rw, rh = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(rx, ry, rw, rh, 6)

    # Draw 4 switch cores horizontally and 8 braided sense lines threading through ("1") or bypassing ("0")
    core_xs = [rx + 170.0 + k * 195.0 for k in range(4)]
    core_y = ry + 162.0
    oct_word, mnemonic = AGC_WORDS_12BIT[active_r]

    # Draw braided sense wires first
    n_rope_wires = 6
    for w_i in range(n_rope_wires):
        wy_base = ry + 48.0 + w_i * 44.0
        pts_w = [[rx + 28.0, wy_base]]
        for k, cx_k in enumerate(core_xs):
            bit_k = (oct_word >> (11 - (w_i + k) % 12)) & 1
            if bit_k == 1:
                # Threads directly through the permalloy core center ("BIT 1")
                pts_w.append([cx_k - 36.0, core_y + (w_i - 2.5) * 4.5])
                pts_w.append([cx_k + 36.0, core_y + (w_i - 2.5) * 4.5])
            else:
                # Bypasses outside the core rim ("BIT 0")
                bypass_y = core_y - 88.0 - w_i * 4.0 if (w_i % 2 == 0) else core_y + 88.0 + w_i * 4.0
                pts_w.append([cx_k - 32.0, bypass_y])
                pts_w.append([cx_k + 32.0, bypass_y])
        pts_w.append([rx + rw - 28.0, wy_base])
        pts_arr = np.array(pts_w, dtype=np.float32)
        segs_w = np.hstack((pts_arr[:-1], pts_arr[1:]))
        w_col = [SENSE_RUBY, GOLD_PIN, Y_BUS_CYAN, INHIBIT_EMERALD, X_BUS_AMBER, HALF_SELECT_TINT][w_i]
        py5.stroke(*w_col, 225)
        py5.stroke_weight(2.2)
        py5.lines(segs_w)

    # Draw the 4 Permalloy Bobbin Switch Cores over the wires
    for k, cx_k in enumerate(core_xs):
        active_core = (k == (active_r % 4))
        py5.fill(*FERRITE_BODY)
        py5.stroke(*(GOLD_BRIGHT if active_core else BORDER_SLATE), 240)
        py5.stroke_weight(2.6 if active_core else 1.8)
        py5.circle(cx_k, core_y, 114.0)
        py5.fill(*VIEWPORT_BG)
        py5.circle(cx_k, core_y, 54.0)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.TOP)
        py5.fill(*(GOLD_BRIGHT if active_core else INK_IVORY))
        py5.text_size(12)
        py5.text(f"ROPE CORE {k:02d}", cx_k, core_y + 66.0)

    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*INK_SILVER)
    py5.text_size(12)
    py5.text(
        f"RAYTHEON / MIT INSTRUMENTATION LAB CORE ROPE: THREAD THROUGH RING = '1' | BYPASS RING = '0'  (ACTIVE: {mnemonic.strip()})",
        rx + 22.0,
        ry + rh - 12.0,
    )

    # --- FIG. 06: Historical Magnetic Core Taxonomy Table ---
    mid_y = y + h * 0.5
    tx, ty, tw, th = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(tx, ty, tw, th, 6)

    headers = ["YEAR", "SYSTEM / ARCHITECT", "TOPOLOGY & CORE OD", "CYCLE TIME", "CAPACITY"]
    col_xs = [tx + 20, tx + 96, tx + 390, tx + 680, tx + 815]
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
        ("1949", "An Wang (Harvard Pulse Device)", "1D Shift Register (Deltamax)", "25.0 us", "32 bits/mod"),
        ("1951", "Jay Forrester (MIT Whirlwind I)", "3D 4-Wire Coincident (2.0 mm)", "9.0 us", "2,048 x 16b"),
        ("1953", "Jan Rajchman (RCA Myriabit)", "Matrix Transfluxor Plane", "12.5 us", "10,000 bits"),
        ("1956", "Ken Olsen (MIT Lincoln Lab TX-0)", "Transistorized 3D (1.2 mm)", "6.0 us", "65,536 x 18b"),
        ("1964", "IBM System/360 (2361 Core LCS)", "2.5D 3-Wire Ferrite (0.5 mm)", "8.0 us", "2,097,152 B"),
        ("1966", "Apollo AGC Block II (MIT/Raytheon)", "Erasable 3D + Core Rope ROM", "11.7 us", "2K RAM / 36K ROM"),
    ]
    for r_i, r_vals in enumerate(rows):
        ry_row = ty + 52.0 + r_i * 47.0
        if r_i % 2 == 1:
            py5.fill(*CARD_HEADER_BG, 110)
            py5.no_stroke()
            py5.rect(tx + 8, ry_row - 8, tw - 16, 40, 3)
        for c_i, (cx_c, val_str) in enumerate(zip(col_xs, r_vals)):
            py5.fill(*(GOLD_PIN if c_i == 0 else (Y_BUS_CYAN if r_i == 5 else INK_IVORY)))
            py5.text_size(12)
            py5.text(val_str, cx_c, ry_row + 12)


def draw_right_bottom_card(phi: float, active_r: int, active_c: int, cycle_phase: float, bit_val: int):
    x, y, w, h = RIGHT_X, BOT_CARD_Y, CARD_W, BOT_CARD_H
    draw_flank_card(
        x,
        y,
        w,
        h,
        "FIG. 07",
        "SYNCHRONOUS COINCIDENT-CURRENT READ / RESTORE TIMING",
        "FIG. 08",
        "16-BIT AGC WORD REGISTER & SENSE EMF OSCILLOGRAM",
    )

    # --- FIG. 07: 5-Channel Read / Restore Pulse Timing Diagram ---
    px, py, pw, ph = x + 36.0, y + 64.0, w - 72.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(px, py, pw, ph, 6)

    left_x = px + 168.0
    trace_w = pw - 196.0
    t_s = np.linspace(0.0, 1.0, 200, dtype=np.float32)
    tx_arr = left_x + t_s * trace_w

    # 5 synchronous timing waveforms across [0, 1] cycle
    ix_wave = np.exp(-((t_s - 0.22) / 0.09) ** 2) - np.exp(-((t_s - 0.70) / 0.09) ** 2)
    iy_wave = np.exp(-((t_s - 0.22) / 0.09) ** 2) - np.exp(-((t_s - 0.70) / 0.09) ** 2)
    iz_wave = (1.0 if bit_val == 0 else 0.12) * np.exp(-((t_s - 0.70) / 0.09) ** 2)
    vs_wave = (1.0 if bit_val == 1 else 0.18) * np.exp(-((t_s - 0.36) / 0.045) ** 2) + 0.25 * np.exp(-((t_s - 0.14) / 0.03) ** 2)
    str_wave = np.exp(-((t_s - 0.36) / 0.03) ** 2)

    channels = [
        ("Ix (COL DRIVE)", X_BUS_AMBER, ix_wave),
        ("Iy (ROW DRIVE)", Y_BUS_CYAN, iy_wave),
        ("Iz (INHIBIT)", INHIBIT_EMERALD, iz_wave),
        ("Vs (SENSE EMF)", SENSE_RUBY, vs_wave),
        ("MBR STROBE", GOLD_BRIGHT, str_wave),
    ]

    for idx_ch, (ch_lbl, ch_col, ch_y) in enumerate(channels):
        cy_ch = py + 44.0 + idx_ch * 62.0
        py5.stroke(*GRID_LINE, 170)
        py5.stroke_weight(1.0)
        py5.line(left_x, cy_ch, left_x + trace_w, cy_ch)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.fill(*ch_col)
        py5.text_size(12)
        py5.text(ch_lbl, px + 18.0, cy_ch)

        pts_c = np.column_stack((tx_arr, cy_ch - ch_y * 22.0))
        py5.stroke(*ch_col, 240)
        py5.stroke_weight(2.2)
        py5.lines(np.hstack((pts_c[:-1], pts_c[1:])))

    # Cycle phase sweep cursor
    cur_tx = left_x + cycle_phase * trace_w
    py5.stroke(*GOLD_BRIGHT, 235)
    py5.stroke_weight(2.0)
    py5.line(cur_tx, py + 16.0, cur_tx, py + ph - 16.0)

    # --- FIG. 08: 16-Bit AGC Memory Buffer Register (MBR) + Continuous Oscillogram ---
    mid_y = y + h * 0.5
    ox, oy, ow, oh = x + 36.0, mid_y + 62.0, w - 72.0, 344.0
    py5.fill(*VIEWPORT_BG)
    py5.stroke(*BORDER_SLATE, 190)
    py5.stroke_weight(1.4)
    py5.rect(ox, oy, ow, oh, 6)

    # Top row inside FIG. 08: 16-Bit AGC Register cells (12 matrix bits + 3 opcode extension + 1 odd parity)
    oct_word, mnemonic = AGC_WORDS_12BIT[active_r]
    row_bits = INITIAL_BITS[active_r]
    parity_bit = int((np.sum(row_bits) + 1) % 2)
    reg_bits = list(row_bits) + [1, 0, 1, parity_bit]

    cell_w = (ow - 48.0) / 16.0
    for b_i, b_v in enumerate(reg_bits):
        bx_i = ox + 24.0 + b_i * cell_w
        by_i = oy + 18.0
        is_active_bit = (b_i == active_c)
        if is_active_bit:
            py5.fill(*SENSE_RUBY, 235)
            py5.stroke(*GOLD_BRIGHT)
        elif b_v == 1:
            py5.fill(*BIT1_CORE, 210)
            py5.stroke(*GOLD_PIN)
        else:
            py5.fill(*CERAMIC_INNER, 230)
            py5.stroke(*BORDER_SLATE)
        py5.stroke_weight(1.6 if is_active_bit else 1.2)
        py5.rect(bx_i + 2, by_i, cell_w - 4, 52.0, 4)

        py5.text_font(FONT_MONO)
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.fill(*INK_IVORY)
        py5.text_size(16)
        py5.text(str(b_v), bx_i + cell_w * 0.5, by_i + 20.0)
        py5.fill(*INK_SILVER)
        py5.text_size(10)
        py5.text("P" if b_i == 15 else f"B{15 - b_i:02d}", bx_i + cell_w * 0.5, by_i + 41.0)

    # Lower half of FIG. 08: Continuous 3-trace Barkhausen Flux & Sense Oscillogram
    osc_y0 = oy + 96.0
    osc_h = oh - 114.0
    osc_cy = osc_y0 + osc_h * 0.5
    py5.stroke(*GRID_LINE, 180)
    py5.stroke_weight(1.0)
    py5.line(ox + 24.0, osc_cy, ox + ow - 24.0, osc_cy)

    u_osc = np.linspace(0.0, 1.0, 220, dtype=np.float32)
    x_osc = ox + 24.0 + u_osc * (ow - 48.0)
    w1 = 68.0 * np.sin(6.0 * np.pi * u_osc - 3.0 * phi) * np.cos(2.0 * np.pi * u_osc + phi)
    w2 = 54.0 * np.cos(10.0 * np.pi * u_osc - 4.0 * phi) * np.exp(-1.2 * ((u_osc - 0.5) ** 2))
    w3 = 42.0 * np.sin(14.0 * np.pi * u_osc - 6.0 * phi)

    for w_arr, w_col in ((w1, X_BUS_AMBER), (w2, Y_BUS_CYAN), (w3, SENSE_RUBY)):
        pts_o = np.column_stack((x_osc, osc_cy - w_arr))
        py5.stroke(*w_col, 230)
        py5.stroke_weight(2.2)
        py5.lines(np.hstack((pts_o[:-1], pts_o[1:])))

    py5.text_font(FONT_MONO)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.fill(*GOLD_BRIGHT)
    py5.text_size(12)
    py5.text(
        f"AGC MBR = {oct_word:04o}o ({mnemonic.strip()})   |   PARITY = {parity_bit} (ODD)   |   BARKHAUSEN EMF SPECTRUM",
        ox + 28.0,
        oy + oh - 10.0,
    )


def draw():
    frame_idx = py5.frame_count - 1
    t_norm = frame_idx / float(TOTAL_FRAMES)
    phi = 2.0 * np.pi * t_norm

    py5.background(*BG_OBSIDIAN)

    # 24 memory access cycles across the 720-frame loop (30 frames = 0.5s per full Read/Strobe/Restore cycle)
    n_cycles = 24
    cycle_pos = t_norm * n_cycles
    cycle_idx = int(cycle_pos) % n_cycles
    cycle_phase = cycle_pos - int(cycle_pos)

    # Deterministic diagonal traversal through the 12x12 matrix so every row & column is exercised
    active_r = (cycle_idx + SEED_OFFSET) % N_GRID
    active_c = (cycle_idx * 5 + 3 + SEED_OFFSET) % N_GRID
    bit_val = int(INITIAL_BITS[active_r, active_c])

    draw_frame_border_and_header(phi, active_r, active_c, cycle_phase)
    draw_central_ferrite_matrix_medallion(phi, active_r, active_c, cycle_phase, bit_val)
    draw_left_top_card(phi, cycle_phase, bit_val)
    draw_left_bottom_card(phi, cycle_phase)
    draw_right_top_card(phi, active_r)
    draw_right_bottom_card(phi, active_r, active_c, cycle_phase, bit_val)

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

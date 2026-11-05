"""
kinetic_jacquard_verdol_punched_card_lampas_brocade_loom_2d

Joseph-Marie Jacquard's 1804 Programmable Silk Brocade Loom (Metier Jacquard),
Jean-Baptiste Falcon's Laced Punched Card Chain (1728), and Lyon Grand Faconne
Lampas Silk-and-Gold Brocade Weaving Mechanics, inspired by Philippe de Lasalle's
18th-century Lyon botanical silk brocades, Charles Babbage & Ada Lovelace's 1843
Notes on the Analytical Engine, and Jules Verdol's continuous paper-tape index.
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
WORK_NAME = "kinetic_jacquard_verdol_punched_card_lampas_brocade_loom_2d"
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
# Color Palette — Warm Lyon Mise-en-Carte Vellum (Light BG) & Lampas Brocade
# ---------------------------------------------------------------------------
BG_VELLUM = (246, 242, 232)       # #f6f2e8 Warm Lyon Canut Mise-en-Carte Vellum
CARD_BG = (252, 249, 242, 238)    # Translucent Atelier Drafting Paper
CARD_BORDER = (186, 168, 138)     # Sepia & Brass Rule
TEXT_PRIMARY = (26, 32, 46)       # Deep Iron-Gall Ink
TEXT_SECONDARY = (94, 86, 74)     # Muted Sepia Annotation
TEXT_ACCENT = (178, 52, 38)       # Lyon Cochineal Vermilion Seal Ink

LOOM_DARK = (13, 21, 38)          # #0d1526 Recessed Loom Timber & Satin Ground
MANILA_CARD = (234, 212, 164)     # Buff Perforated Jacquard Pasteboard Card
MANILA_SHADOW = (196, 170, 118)   # Card Bevel & Punch Shadow
CRAMOISI_SILK = (216, 44, 74)     # Lyon Cochineal Crimson Silk Weft
CRAMOISI_HIGH = (248, 112, 132)   # Specular Crimson Fibroin Sheen
FIL_DOR_GOLD = (230, 162, 28)     # 24K Gold-Wrapped Lyon Brocade Thread
FIL_DOR_HIGH = (254, 232, 124)    # Specular Gold-Leaf Highlight
CELADON_SILK = (20, 158, 126)     # Botanical Malachite-Celadon Silk Weft
CELADON_HIGH = (84, 218, 184)     # Specular Celadon Fibroin Sheen
BLEU_ROI_SATIN = (34, 92, 178)    # Royal Indigo Satin Ground Warp (Chaine de Fond)
BLEU_ROI_HIGH = (88, 154, 238)    # Satin Warp Float Highlight

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
FONT_MAIN = None
START_TIME = 0.0
PHASE_OFFSET = 0.0

# Precomputed 48-row x 32-column Lampas Brocade Pattern Matrix (Tileable vertically)
# Values: 0 = Bleu de Roi 8-end Satin Ground, 1 = Fil d'Or Gold Weft Float,
#         2 = Cramoisi Crimson Floral Float, 3 = Celadon Botanical Leaf Float
PATTERN_ROWS = 48
PATTERN_COLS = 32
BROCADE_MATRIX = None
BINARY_PUNCH_MATRIX = None
GRID_LINES = None


def init_jacquard_pattern():
    """Construct a symmetric 48x32 Lyon Grand Faconne Lampas botanical medallion repeat."""
    global BROCADE_MATRIX, BINARY_PUNCH_MATRIX, GRID_LINES

    mat = np.zeros((PATTERN_ROWS, PATTERN_COLS), dtype=np.int32)
    # Use mirror symmetry across columns c in [0..15] <-> [31..16]
    for r in range(PATTERN_ROWS):
        y_n = (r - PATTERN_ROWS * 0.5) / (PATTERN_ROWS * 0.5)  # [-1, 1]
        for c in range(16):
            x_n = (15.5 - c) / 15.5  # [0.03, 1.0] distance from center axis

            # 1. Outer Ogival Trellis Frame of Fil d'Or Gold Acanthus Scroll
            ogive_dist = abs(x_n - (0.58 + 0.30 * np.cos(y_n * np.pi)))
            is_trellis_gold = ogive_dist < 0.11
            is_trellis_emerald = (ogive_dist >= 0.11) and (ogive_dist < 0.19) and ((r + c) % 2 == 0)

            # 2. Central Lyon Pomegranate & Tudor Rose Medallion around (x_n=0, y_n=0)
            rad_c = np.hypot(x_n * 1.15, y_n * 1.25)
            ang_c = np.arctan2(y_n, x_n + 1e-5)
            petal_r = 0.44 + 0.10 * np.cos(6.0 * ang_c)
            is_core_gold = (rad_c < 0.16) or (abs(rad_c - 0.30) < 0.055)
            is_petal_crimson = (rad_c >= 0.16) and (rad_c < petal_r) and (not is_core_gold)

            # 3. Crown & Basal Fleur-de-Lis / Palmette Finials at top/bottom of repeat (|y_n| -> 0.78)
            rad_p = np.hypot(x_n * 1.35, (abs(y_n) - 0.82) * 1.45)
            is_palmette_crimson = rad_p < 0.24
            is_palmette_gold = (rad_p >= 0.24) and (rad_p < 0.33)

            # 4. radiating Celadon Botanical Laurel Leaves flanking the medallion
            leaf_curve = abs(abs(y_n) - (0.28 + 0.52 * x_n))
            is_leaf_celadon = (x_n > 0.24) and (x_n < 0.82) and (leaf_curve < 0.095)

            val = 0
            if is_Leaf := is_leaf_celadon or is_trellis_emerald:
                val = 3  # Celadon Weft Float
            if is_petal_crimson or is_palmette_crimson:
                val = 2  # Cramoisi Crimson Weft Float
            if is_trellis_gold or is_core_gold or is_palmette_gold:
                val = 1  # Fil d'Or 24K Gold Weft Float

            mat[r, c] = val
            mat[r, PATTERN_COLS - 1 - c] = val

    BROCADE_MATRIX = mat
    # Binary punch matrix: 1 if any brocade weft float is active (hook lifted), plus 8-end satin binding points
    satin_step = 3  # 8-end regular satin step (3 is coprime to 8)
    satin_bind = np.zeros_like(mat)
    for r in range(PATTERN_ROWS):
        for c in range(PATTERN_COLS):
            if (r * satin_step + c) % 8 == 0:
                satin_bind[r, c] = 1
    BINARY_PUNCH_MATRIX = np.where(mat > 0, 1, satin_bind)

    # Precompute subtle Mise-en-Carte point-paper grid lines on background vellum
    g_segs = []
    for x in range(80, WIDTH - 80, 60):
        g_segs.append([float(x), 55.0, float(x), float(HEIGHT - 55)])
    for y in range(60, HEIGHT - 60, 60):
        g_segs.append([80.0, float(y), float(WIDTH - 80), float(y)])
    GRID_LINES = np.array(g_segs, dtype=np.float32)


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

    init_jacquard_pattern()
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")


# ---------------------------------------------------------------------------
# Main Medallion Rendering: Jacquard Punched Cards, Harness & Lampas Brocade
# ---------------------------------------------------------------------------
def draw_jacquard_loom_medallion(tau):
    r_inner = R_MEDALLION - 14.0

    # Scroll phase: advances exactly 24 picks (half pattern or full harmonic cycle) per 720-frame loop
    # Make it advance 1 full 48-row pattern repeat over 720 frames -> 15 frames per pick!
    pick_float = (tau / (2.0 * np.pi)) * PATTERN_ROWS
    pick_int = int(np.floor(pick_float)) % PATTERN_ROWS
    pick_frac = pick_float - np.floor(pick_float)  # [0, 1) within current pick cycle

    # 1. Outer Brass Frame & Dark Recessed Canut Loom Interior
    py5.no_stroke()
    py5.fill(198, 152, 64)
    py5.circle(CX, CY, R_RING_OUTER * 2.0)

    py5.fill(*LOOM_DARK)
    py5.circle(CX, CY, R_MEDALLION * 2.0)

    # Subtle radial Jacquard atelier depth rings
    py5.no_fill()
    py5.stroke(30, 46, 78, 120)
    py5.stroke_weight(1.2)
    for r_ring in [260.0, 480.0, 660.0, 775.0]:
        py5.circle(CX, CY, r_ring * 2.0)

    # Geometry zones inside the circular medallion (top to bottom):
    # Zone A (y = CY - 735 to CY - 445): Laced Chain of 5 Perforated Jacquard Pasteboard Cards
    # Zone B (y = CY - 445 to CY - 265): 32 Brass Hooks (Crochets), Griffe Bar, Arcades Harness Fan & Comber Board
    # Zone C (y = CY - 265 to CY - 215): Open Warp Shed (Foule) & Flying Boxwood Shuttle (Navette)
    # Zone D (y = CY - 215 to CY + 545): Woven Lyon Grand Faconne Lampas Silk & Gold Brocade Cloth (32x38 picks)
    # Zone E (y = CY + 545 to CY + 745): Cloth Beam (Ensouple) & 32 Oscillating Lead Lingoes (Plombs)

    # -----------------------------------------------------------------------
    # ZONE A: Laced Chain of Perforated Jacquard Pasteboard Cards (Top Arc)
    # -----------------------------------------------------------------------
    card_w = 780.0
    card_h = 46.0
    card_x0 = CX - card_w * 0.5
    n_visible_cards = 5
    card_base_y = CY - 690.0

    lacing_segs = []
    punch_quads_dark = []
    punch_quads_active = []

    for c_k in range(n_visible_cards):
        # Cards advance smoothly downward toward the reading cylinder at c_k == 3
        cy_card = card_base_y + (c_k + pick_frac) * 54.0
        row_idx = (pick_int - c_k + 3) % PATTERN_ROWS
        is_reading_card = (c_k == 3)

        # Clip card width to fit inside circular medallion at top
        dy_top = abs((cy_card - CY) / r_inner)
        max_half_w = r_inner * np.sqrt(max(0.05, 1.0 - dy_top * dy_top)) - 28.0
        cw_eff = min(card_w, max_half_w * 2.0)
        cx_eff0 = CX - cw_eff * 0.5

        # Pasteboard card body
        if is_reading_card:
            py5.stroke(250, 204, 86, 240)
            py5.stroke_weight(2.2)
            py5.fill(244, 224, 176)
        else:
            py5.stroke(*MANILA_SHADOW)
            py5.stroke_weight(1.4)
            py5.fill(*MANILA_CARD)
        py5.rect(cx_eff0, cy_card, cw_eff, card_h, 4)

        # Lateral sprocket peg holes on left & right card margins
        py5.no_stroke()
        py5.fill(*LOOM_DARK)
        py5.circle(cx_eff0 + 18.0, cy_card + card_h * 0.5, 12.0)
        py5.circle(cx_eff0 + cw_eff - 18.0, cy_card + card_h * 0.5, 12.0)

        # Green linen lacing twine connecting adjacent cards
        if c_k < n_visible_cards - 1:
            for lx_off in [18.0, 34.0, cw_eff - 34.0, cw_eff - 18.0]:
                lacing_segs.append([
                    cx_eff0 + lx_off, cy_card + card_h - 4.0,
                    cx_eff0 + lx_off, cy_card + 54.0 + 4.0,
                ])

        # 32 Columns x 2 Sub-rows of Binary Punch Perforations across the card
        inner_w = cw_eff - 96.0
        inner_x0 = CX - inner_w * 0.5
        col_step = inner_w / PATTERN_COLS

        for col in range(PATTERN_COLS):
            hx = inner_x0 + (col + 0.5) * col_step
            for sub_r in range(2):
                r_lookup = (row_idx + sub_r) % PATTERN_ROWS
                bit = BINARY_PUNCH_MATRIX[r_lookup, col]
                hy = cy_card + 13.0 + sub_r * 20.0
                if bit == 1:
                    # Punched perforation hole!
                    r_h = 4.6
                    q = [[hx - r_h, hy - r_h], [hx + r_h, hy - r_h], [hx + r_h, hy + r_h], [hx - r_h, hy + r_h]]
                    if is_reading_card and sub_r == 0:
                        punch_quads_active.append(q)
                    else:
                        punch_quads_dark.append(q)
                else:
                    # Solid unpunched card position (faint embossed dot)
                    pass

    if punch_quads_dark:
        py5.no_stroke()
        py5.fill(13, 21, 38, 240)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(punch_quads_dark, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

    if punch_quads_active:
        py5.no_stroke()
        py5.fill(254, 218, 88)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(punch_quads_active, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

    if lacing_segs:
        py5.stroke(24, 178, 136, 220)
        py5.stroke_weight(2.4)
        py5.lines(np.array(lacing_segs, dtype=np.float32))

    # -----------------------------------------------------------------------
    # ZONE B: Brass Hooks (Crochets), Griffe Knife Bar & Arcades Harness Fan
    # -----------------------------------------------------------------------
    y_hooks_top = CY - 405.0
    y_comber = CY - 265.0
    cloth_w = 880.0
    cloth_x0 = CX - cloth_w * 0.5
    warp_step = cloth_w / PATTERN_COLS

    # Reading Cylinder (Cylindre Carre) & Griffe Knife Bar
    griffe_lift = 16.0 * np.sin(pick_frac * np.pi)
    y_griffe = y_hooks_top + 28.0 - griffe_lift
    py5.stroke(230, 162, 28, 220)
    py5.stroke_weight(3.0)
    py5.line(CX - 360.0, y_griffe, CX + 360.0, y_griffe)

    # Comber Board (Planche d'Empoutage) horizontal perforated boxwood bar
    py5.fill(186, 134, 68)
    py5.stroke(244, 198, 108)
    py5.stroke_weight(1.8)
    py5.rect(cloth_x0 - 18.0, y_comber - 8.0, cloth_w + 36.0, 16.0, 3)

    harness_lifted_segs = []
    harness_dropped_segs = []
    hook_caps = []

    top_span_w = 640.0
    top_x0 = CX - top_span_w * 0.5
    top_step = top_span_w / PATTERN_COLS

    for col in range(PATTERN_COLS):
        bit = BINARY_PUNCH_MATRIX[pick_int, col]
        lift_dy = -griffe_lift if bit == 1 else 0.0
        hx_top = top_x0 + (col + 0.5) * top_step
        hy_top = y_hooks_top + 38.0 + lift_dy
        wx_bot = cloth_x0 + (col + 0.5) * warp_step

        seg = [hx_top, hy_top, wx_bot, y_comber]
        if bit == 1:
            harness_lifted_segs.append(seg)
            hook_caps.append((hx_top, hy_top - 12.0, True))
        else:
            harness_dropped_segs.append(seg)
            hook_caps.append((hx_top, hy_top - 6.0, False))

    if harness_dropped_segs:
        py5.stroke(136, 152, 184, 115)
        py5.stroke_weight(1.3)
        py5.lines(np.array(harness_dropped_segs, dtype=np.float32))
    if harness_lifted_segs:
        py5.stroke(254, 216, 96, 225)
        py5.stroke_weight(2.0)
        py5.lines(np.array(harness_lifted_segs, dtype=np.float32))

    py5.no_stroke()
    for hx, hy, is_up in hook_caps:
        if is_up:
            py5.fill(254, 218, 92)
            py5.rect(hx - 3.5, hy, 7.0, 14.0, 2)
        else:
            py5.fill(118, 134, 166)
            py5.rect(hx - 3.0, hy, 6.0, 10.0, 2)

    # -----------------------------------------------------------------------
    # ZONE C: Open Warp Shed (Foule) & Flying Boxwood Shuttle (Navette)
    # -----------------------------------------------------------------------
    y_shed_mid = CY - 236.0
    # Shuttle oscillates horizontally across the shed once per pick cycle
    shuttle_dir = 1 if (pick_int % 2 == 0) else -1
    shuttle_u = (pick_frac * 2.0 - 1.0) * shuttle_dir
    shuttle_x = CX + shuttle_u * (cloth_w * 0.44)

    # Active weft thread trail behind the flying shuttle
    trail_x0 = cloth_x0 if shuttle_dir == 1 else (cloth_x0 + cloth_w)
    active_row_colors = BROCADE_MATRIX[pick_int]
    if np.any(active_row_colors == 1):
        weft_col = FIL_DOR_HIGH
    elif np.any(active_row_colors == 2):
        weft_col = CRAMOISI_HIGH
    else:
        weft_col = CELADON_HIGH

    py5.stroke(weft_col[0], weft_col[1], weft_col[2], 235)
    py5.stroke_weight(2.6)
    py5.line(trail_x0, y_shed_mid, shuttle_x, y_shed_mid)

    # Polished Boxwood Flying Shuttle (Navette) boat silhouette + Pirn (Canette)
    sh_w, sh_h = 84.0, 20.0
    py5.stroke(248, 208, 118)
    py5.stroke_weight(1.6)
    py5.fill(176, 98, 42)
    py5.begin_shape()
    py5.vertex(shuttle_x - sh_w * 0.5, y_shed_mid)
    py5.vertex(shuttle_x - sh_w * 0.28, y_shed_mid - sh_h * 0.5)
    py5.vertex(shuttle_x + sh_w * 0.28, y_shed_mid - sh_h * 0.5)
    py5.vertex(shuttle_x + sh_w * 0.5, y_shed_mid)
    py5.vertex(shuttle_x + sh_w * 0.28, y_shed_mid + sh_h * 0.5)
    py5.vertex(shuttle_x - sh_w * 0.28, y_shed_mid + sh_h * 0.5)
    py5.end_shape(py5.CLOSE)

    py5.no_stroke()
    py5.fill(*weft_col)
    py5.rect(shuttle_x - 18.0, y_shed_mid - 4.5, 36.0, 9.0, 3)

    # -----------------------------------------------------------------------
    # ZONE D: Woven Lyon Grand Faconne Lampas Silk & Gold Brocade Cloth
    # -----------------------------------------------------------------------
    y_cloth_top = CY - 210.0
    n_cloth_rows = 38
    row_h = 19.5
    y_cloth_bot = y_cloth_top + n_cloth_rows * row_h

    # Recessed dark indigo silk foundation under the brocade weave
    py5.no_stroke()
    py5.fill(10, 18, 36)
    py5.rect(cloth_x0 - 8.0, y_cloth_top - 4.0, cloth_w + 16.0, n_cloth_rows * row_h + 8.0, 4)

    # Golden decorative selvedge borders (Lisieres) on left and right edges of the silk cloth
    py5.fill(*FIL_DOR_GOLD)
    py5.rect(cloth_x0 - 12.0, y_cloth_top - 4.0, 8.0, n_cloth_rows * row_h + 8.0)
    py5.rect(cloth_x0 + cloth_w + 4.0, y_cloth_top - 4.0, 8.0, n_cloth_rows * row_h + 8.0)

    # Batch-render all 38 x 32 = 1,216 woven Lampas thread floats & 8-end satin bindings!
    q_satin_base, q_satin_high = [], []
    q_gold_base, q_gold_high = [], []
    q_crim_base, q_crim_high = [], []
    q_cel_base, q_cel_high = [], []

    pad_x = 1.6
    pad_y = 1.5

    for r_vis in range(n_cloth_rows):
        r_pat = (pick_int - r_vis) % PATTERN_ROWS
        yy0 = y_cloth_top + (r_vis + pick_frac) * row_h
        yy1 = yy0 + row_h
        if yy1 > y_cloth_bot + row_h * 0.5:
            continue

        for col in range(PATTERN_COLS):
            xx0 = cloth_x0 + col * warp_step
            xx1 = xx0 + warp_step
            cell_val = BROCADE_MATRIX[r_pat, col]

            if cell_val == 0:
                # 8-End Satin Ground Warp Float (Vertical warp orientation)
                q_b = [
                    [xx0 + pad_x, yy0 + 0.6],
                    [xx1 - pad_x, yy0 + 0.6],
                    [xx1 - pad_x, yy1 - 0.6],
                    [xx0 + pad_x, yy1 - 0.6],
                ]
                q_satin_base.append(q_b)
                # Satin specular spine or binding tie point
                if (r_pat * 3 + col) % 8 == 0:
                    # Gold/Teal binding tie point (Point de Liage)
                    q_h = [
                        [xx0 + 5.0, yy0 + 5.0],
                        [xx1 - 5.0, yy0 + 5.0],
                        [xx1 - 5.0, yy1 - 5.0],
                        [xx0 + 5.0, yy1 - 5.0],
                    ]
                    q_gold_base.append(q_h)
                else:
                    q_h = [
                        [xx0 + 7.5, yy0 + 2.0],
                        [xx1 - 7.5, yy0 + 2.0],
                        [xx1 - 7.5, yy1 - 2.0],
                        [xx0 + 7.5, yy1 - 2.0],
                    ]
                    q_satin_high.append(q_h)
            else:
                # Polychrome Weft Brocade Float (Horizontal convex silk/gold float across warp)
                q_b = [
                    [xx0 + 0.5, yy0 + pad_y],
                    [xx1 - 0.5, yy0 + pad_y],
                    [xx1 - 0.5, yy1 - pad_y],
                    [xx0 + 0.5, yy1 - pad_y],
                ]
                q_h = [
                    [xx0 + 2.5, yy0 + 4.8],
                    [xx1 - 2.5, yy0 + 4.8],
                    [xx1 - 2.5, yy1 - 6.8],
                    [xx0 + 2.5, yy1 - 6.8],
                ]
                if cell_val == 1:
                    q_gold_base.append(q_b)
                    q_gold_high.append(q_h)
                elif cell_val == 2:
                    q_crim_base.append(q_b)
                    q_crim_high.append(q_h)
                else:
                    q_cel_base.append(q_b)
                    q_cel_high.append(q_h)

    def flush_quads(q_list, rgb):
        if not q_list:
            return
        py5.fill(*rgb)
        py5.begin_shape(py5.QUADS)
        py5.vertices(np.array(q_list, dtype=np.float32).reshape(-1, 2))
        py5.end_shape()

    py5.no_stroke()
    flush_quads(q_satin_base, BLEU_ROI_SATIN)
    flush_quads(q_satin_high, BLEU_ROI_HIGH)
    flush_quads(q_cel_base, CELADON_SILK)
    flush_quads(q_cel_high, CELADON_HIGH)
    flush_quads(q_crim_base, CRAMOISI_SILK)
    flush_quads(q_crim_high, CRAMOISI_HIGH)
    flush_quads(q_gold_base, FIL_DOR_GOLD)
    flush_quads(q_gold_high, FIL_DOR_HIGH)

    # -----------------------------------------------------------------------
    # ZONE E: Cloth Beam (Ensouple) & 32 Lead Lingoes (Plombs de Rappel)
    # -----------------------------------------------------------------------
    y_beam = y_cloth_bot + 12.0
    py5.stroke(244, 198, 108)
    py5.stroke_weight(2.0)
    py5.fill(142, 84, 38)
    py5.rect(cloth_x0 - 24.0, y_beam, cloth_w + 48.0, 22.0, 5)

    lingo_cords = []
    lingo_weights = []
    for col in range(PATTERN_COLS):
        lx = cloth_x0 + (col + 0.5) * warp_step
        dx_c = abs(lx - CX)
        max_y_circ = CY + np.sqrt(max(0.0, (r_inner - 18.0) ** 2 - dx_c * dx_c))
        bit = BINARY_PUNCH_MATRIX[pick_int, col]
        ly_bot = min(max_y_circ - 28.0, y_beam + 118.0 - (14.0 if bit == 1 else 0.0))
        if ly_bot > y_beam + 34.0:
            lingo_cords.append([lx, y_beam + 22.0, lx, ly_bot])
            lingo_weights.append((lx, ly_bot, bit == 1))

    if lingo_cords:
        py5.stroke(188, 168, 128, 185)
        py5.stroke_weight(1.4)
        py5.lines(np.array(lingo_cords, dtype=np.float32))

    py5.no_stroke()
    for lx, ly, is_up in lingo_weights:
        py5.fill(*(FIL_DOR_HIGH if is_up else (164, 176, 198)))
        py5.rect(lx - 4.0, ly, 8.0, 24.0, 3)

    # 6. Outer Graduated Brass Index Ring & Vernier Ticks
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
# Side Panels & 8 Jacquard Loom / Binary Weaving Apparatuses
# ---------------------------------------------------------------------------
def draw_card_shell(x, y, w, h, fig_top, title_top, sub_top, fig_bot, title_bot, sub_bot):
    py5.fill(*CARD_BG)
    py5.stroke(*CARD_BORDER)
    py5.stroke_weight(1.8)
    py5.rect(x, y, w, h, 8)

    mid_y = y + h * 0.49
    py5.stroke(186, 168, 138, 175)
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
        "FIG. 01", "JACQUARD NEEDLE (AIGUILLE) & HOOK (CROCHET) BINARY LOGIC",
        "BIT 1 (PERFORATION): HOOK ENGAGES RISING GRIFFE // BIT 0 (SOLID CARD): NEEDLE DEFLECTS HOOK",
        "FIG. 02", "MISE-EN-CARTE POINT-PAPER DRAFT & 8-END SATIN BINDING",
        "DECIMATED CARTE D'EMpoutage: 8-END REGULAR SATIN (STEP S = 3) + POLYCHROME BROCADE FLOATS",
    )

    # FIG. 01 Diagram: Mechanical Binary Gate (Aiguille + Crochet + Griffe)
    bx, by, bw, bh = LEFT_X + 28, CARD_Y_TOP + 86, 235.0, 245.0
    py5.fill(*LOOM_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(bx, by, bw, bh, 4)

    # Two vertical hooks: Left (Bit 1 = Lifted by Griffe), Right (Bit 0 = Tilted away)
    lift_anim = 18.0 * (0.5 + 0.5 * np.sin(tau * 2.0))
    # Left hook (Bit 1)
    py5.stroke(*FIL_DOR_HIGH)
    py5.stroke_weight(3.0)
    py5.line(bx + 78, by + 195 - lift_anim, bx + 78, by + 52 - lift_anim)
    py5.line(bx + 78, by + 52 - lift_anim, bx + 94, by + 64 - lift_anim)
    # Right hook (Bit 0 deflected)
    py5.stroke(148, 164, 194)
    py5.line(bx + 158, by + 195, bx + 176, by + 62)
    py5.line(bx + 176, by + 62, bx + 190, by + 74)
    # Horizontal needles & card face at left
    py5.stroke(*CRAMOISI_HIGH)
    py5.stroke_weight(2.2)
    py5.line(bx + 24, by + 115, bx + 115, by + 115)
    py5.line(bx + 42, by + 150, bx + 185, by + 150)
    py5.no_stroke()
    py5.fill(*MANILA_CARD)
    py5.rect(bx + 16, by + 92, 14, 86, 2)
    py5.fill(*LOOM_DARK)
    py5.rect(bx + 15, by + 109, 16, 12)  # Hole for Bit 1 needle!

    draw_kv_rows(LEFT_X + 285, CARD_Y_TOP + 98, [
        ("INVENTION PATENT", "Brevet 245 (J.-M. Jacquard, 1804)"),
        ("BINARY ENCODING", "1 = Perforation / 0 = Solid Card"),
        ("ACTUATOR NEEDLE", "Horizontal Spring-Return Aiguille"),
        ("LIFTING ELEMENT", "Vertical Hook (Crochet) + Griffe"),
        ("RESTORING FORCE", "Spiral Spring Box (Etui a Elastique)"),
        ("HARNESS COUPLING", "Linen Arcade Cords + Comber Board"),
        ("COUNTERWEIGHT", "Lead Lingo (Plomb de Rappel, 28 g)"),
    ])

    # FIG. 02 Diagram: 8x8 Mise-en-Carte Point-Paper Matrix
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    mx, my, mw, mh = LEFT_X + 28, mid_y + 82, 235.0, 245.0
    py5.fill(*LOOM_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(mx, my, mw, mh, 4)

    cell_s = 24.0
    ox_m, oy_m = mx + 21.5, my + 26.5
    for r in range(8):
        for c in range(8):
            cx_m = ox_m + c * cell_s
            cy_m = oy_m + r * cell_s
            is_satin = ((r * 3 + c) % 8 == 0)
            is_brocade = ((r - 3.5) ** 2 + (c - 3.5) ** 2) < 5.2
            py5.stroke(42, 58, 92)
            py5.stroke_weight(1.0)
            if is_brocade:
                py5.fill(*CRAMOISI_SILK)
            elif is_satin:
                py5.fill(*FIL_DOR_GOLD)
            else:
                py5.fill(18, 30, 56)
            py5.rect(cx_m, cy_m, cell_s - 2.0, cell_s - 2.0, 2)

    draw_kv_rows(LEFT_X + 285, mid_y + 92, [
        ("DRAFT NOTATION", "Mise-en-Carte Squared Point Paper"),
        ("GROUND WEAVE", "Satin de 8 (Decochement Step s = 3)"),
        ("MAIN WARP DENSITY", "120 Ends/cm Organzine Bombyx Mori"),
        ("BINDING WARP", "Chaine de Liage (1:4 Taffeta/Twill)"),
        ("BROCADE WEFTS", "3 Lats: Cramoisi, Fil d'Or, Celadon"),
        ("CARD TRANSLATION", "Liseur Reading & Piano Punching"),
        ("PATTERN SYMMETRY", "Pointed Draw (Empoutage a Pointe)"),
    ])

    # --- BOTTOM-LEFT CARD: FIG. 03 & FIG. 04 ---
    draw_card_shell(
        LEFT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 03", "WARP SHEDDING KINEMATICS (FOULE) & FLYING SHUTTLE",
        "ASYMMETRIC OPEN SHED GEOMETRY: UPPER LIFTED WARP SHEET VS. LOWER STAYED WARP SHEET",
        "FIG. 04", "LYON CANUT SILK, FIL D'OR & MANILA PASTEBOARD PALETTE",
        "COCHINEAL CRAMOISI, 24K GOLD-WRAPPED THREAD, BLEU DE ROI SATIN & CELADON BOTANICALS",
    )

    sx, sy, sw, sh = LEFT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0
    py5.fill(*LOOM_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(sx, sy, sw, sh, 4)

    # Shedding diamond cross-section (Cloth fell -> Heald/Arcade -> Warp Beam)
    shed_h = 58.0 * (0.35 + 0.65 * abs(np.sin(tau)))
    mid_sy = sy + sh * 0.52
    py5.stroke(*FIL_DOR_HIGH)
    py5.stroke_weight(2.2)
    py5.line(sx + 22, mid_sy, sx + 125, mid_sy - shed_h)
    py5.line(sx + 125, mid_sy - shed_h, sx + sw - 22, mid_sy)
    py5.stroke(*BLEU_ROI_HIGH)
    py5.line(sx + 22, mid_sy, sx + 125, mid_sy + shed_h)
    py5.line(sx + 125, mid_sy + shed_h, sx + sw - 22, mid_sy)

    # Cross-section of shuttle inside the shed diamond
    py5.no_stroke()
    py5.fill(*CRAMOISI_SILK)
    py5.ellipse(sx + 125, mid_sy, 38.0, 18.0)
    py5.fill(*FIL_DOR_HIGH)
    py5.circle(sx + 125, mid_sy, 9.0)

    draw_kv_rows(LEFT_X + 285, CARD_Y_BOT + 96, [
        ("SHEDDING ANGLE", "24.5 DEG Open Warp Shed (Foule)"),
        ("DWELL FRACTION", "120 DEG Crank Dwell for Shuttle"),
        ("SHUTTLE VELOCITY", "v_navette = 11.5 m/s Boxwood Pirn"),
        ("REED BEAT-UP", "Battant Sley Drive at 0 DEG TDC"),
        ("WARP TENSION", "Ensouple Weight Lever Equilibrium"),
        ("HARNESS CAPACITY", "400 / 600 / 1200 Hooks (Crochets)"),
        ("WEAVING RATE", "95 Picks/Min (~12x Drawloom Speed)"),
    ])

    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    swatches = [
        (CRAMOISI_SILK, "CRAMOISI DE LYON // COCHINEAL CARMINIC ACID DYED SILK WEFT (#D82C4A)"),
        (FIL_DOR_GOLD, "FIL D'OR DE LYON // 24K GOLD-GILT SILVER LAME WRAPPED ON SILK (#E6A21C)"),
        (BLEU_ROI_SATIN, "BLEU DE ROI SATIN // 8-END INDIGO-PRUSSIAN ORGANZINE GROUND WARP (#225CB2)"),
        (CELADON_SILK, "VERT CELADON // MALACHITE & WELD BOTANICAL FOLIAGE SILK WEFT (#149E7E)"),
        (MANILA_CARD, "CARTON PERFORE //OILED MANILA PASTEBOARD BINARY PUNCHED CARD (#EAD4A4)"),
        (LOOM_DARK, "EBENE & NOYER CANUT // RECESSED LYON LOOM FRAME & SHADOW GROUND (#0D1526)"),
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
        "FIG. 05", "LAMPAS DUAL-WARP & TRIPLE-WEFT FLOAT CROSS-SECTION",
        "CHAINE DE FOND (SATIN GROUND) + CHAINE DE LIAGE (TAFFETA BINDING) + 3 BROCADE WEFTS",
        "FIG. 06", "HISTORICAL PROGRAMMABLE LOOM & BINARY COMPUTATION LEDGER",
        "FROM BOUCHON (1725) & FALCON (1728) TO JACQUARD (1804) & BABBAGE/LOVELACE (1843)",
    )

    # FIG. 05 Diagram: Cross-sectional Weave Float Topology
    wx, wy, ww, wh = RIGHT_X + 28, CARD_Y_TOP + 88, 235.0, 245.0
    py5.fill(*LOOM_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(wx, wy, ww, wh, 4)

    # 6 Warp End Cross-Sections (circles) + Sinusoidal Weft Floats weaving over/under
    xs_w = np.linspace(0.0, 1.0, 48)
    weft_specs = [
        (wy + 62.0, FIL_DOR_HIGH, 1.0, 0.0),
        (wy + 124.0, CRAMOISI_HIGH, -1.0, 1.4),
        (wy + 186.0, CELADON_HIGH, 1.0, 2.8),
    ]
    for y_w, col_w, sgn, p_sh in weft_specs:
        segs = []
        ys_w = y_w + sgn * 16.0 * np.sin(xs_w * 3.0 * np.pi + tau + p_sh)
        for j in range(len(xs_w) - 1):
            segs.append([
                wx + 18 + xs_w[j] * (ww - 36), ys_w[j],
                wx + 18 + xs_w[j + 1] * (ww - 36), ys_w[j + 1],
            ])
        py5.stroke(*col_w)
        py5.stroke_weight(3.0)
        py5.lines(np.array(segs, dtype=np.float32))

        for k in range(6):
            kx = wx + 28 + k * 35.5
            py5.no_stroke()
            py5.fill(*(BLEU_ROI_HIGH if k % 2 == 0 else MANILA_CARD))
            py5.circle(kx, y_w, 11.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_TOP + 98, [
        ("TEXTILE CLASS", "Grand Faconne Lampas Brocade"),
        ("WARP SYSTEM I", "Chaine de Fond (8-End Satin Ground)"),
        ("WARP SYSTEM II", "Chaine de Liage (Binding Warp)"),
        ("WEFT PASSES", "1 Ground Pick + 3 Brocading Lats"),
        ("GOLD THREAD", "Fil d'Or: Gilt Silver Strip on Silk"),
        ("RELIEF EFFECT", " contrasting Matte Weft on Satin"),
        ("ATELIER STANDARD", "Mobilier National / Garde-Meuble"),
    ])

    # FIG. 06 Historical Ledger
    mid_y = CARD_Y_TOP + CARD_H_TOP * 0.49
    ledger = [
        ("PAPER ROLL (1725)", "Basile Bouchon", "Perforated Tape", "First Binary Needle Control"),
        ("CARD CHAIN (1728)", "Jean-Baptiste Falcon", "Laced Pasteboard", "Rectangular Punched Cards"),
        ("CYLINDER LOOM (1745)", "Jacques de Vaucanson", "Ratchet Drum", "Automated Shed Selection"),
        ("METIER JACQUARD (1804)", "Joseph-Marie Jacquard", "Square Prism + Griffe", "Full Single-Weaver Autonomy"),
        ("NOTE G (1843)", "Babbage & Lovelace", "Operation Cards", "Algebraic Analytical Engine"),
        ("VERDOL INDEX (1884)", "Jules Verdol", "896-Hook Continuous", "FINE PITCH PAPER TAPE LIVE"),
    ]
    for i, (era, author, metric, desc) in enumerate(ledger):
        ry = mid_y + 78 + i * 52
        is_active = i == 5
        py5.fill(*(LOOM_DARK if is_active else (240, 234, 220)))
        py5.stroke(*(TEXT_ACCENT if is_active else CARD_BORDER))
        py5.stroke_weight(1.6 if is_active else 1.0)
        py5.rect(RIGHT_X + 28, ry, CARD_W - 56, 42, 4)

        py5.no_stroke()
        py5.fill(*(FIL_DOR_HIGH if is_active else TEXT_PRIMARY))
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text_size(12)
        py5.text(era, RIGHT_X + 44, ry + 21)
        py5.fill(*(MANILA_CARD if is_active else TEXT_SECONDARY))
        py5.text(author, RIGHT_X + 245, ry + 21)
        py5.fill(*(CELADON_HIGH if is_active else TEXT_ACCENT))
        py5.text(metric, RIGHT_X + 440, ry + 21)
        py5.fill(*(MANILA_CARD if is_active else TEXT_PRIMARY))
        py5.text(desc, RIGHT_X + 615, ry + 21)

    # --- BOTTOM-RIGHT CARD: FIG. 07 & FIG. 08 ---
    draw_card_shell(
        RIGHT_X, CARD_Y_BOT, CARD_W, CARD_H_BOT,
        "FIG. 07", "FOUR-SIDED LANTERN CYLINDER (CYLINDRE CARRE) INDEXING",
        "90-DEGREE GENEVA MALTESE-CROSS ROTATION & BATTEN PRESS STROKE PER WEFT PICK",
        "FIG. 08", "32-CHANNEL BINARY PUNCH BITSTREAM & HARNESS LOAD OSCILLOGRAM",
        "SYNCHRONOUS HOOK ACTUATION RATIO H(t), SHUTTLE KINEMATICS & GRIFFE TENSION WAVE",
    )

    # FIG. 07 Diagram: Rotating 4-Sided Jacquard Cylinder (Cylindre Carre)
    cx_d, cy_d = RIGHT_X + 145, CARD_Y_BOT + 212
    py5.fill(*LOOM_DARK)
    py5.stroke(*CARD_BORDER)
    py5.rect(RIGHT_X + 28, CARD_Y_BOT + 86, 235.0, 255.0, 4)

    rot_ang = (tau / (2.0 * np.pi)) * (np.pi * 2.0)
    r_cyl = 62.0
    cyl_pts = [
        [cx_d + r_cyl * np.cos(rot_ang + k * np.pi * 0.5), cy_d + r_cyl * np.sin(rot_ang + k * np.pi * 0.5)]
        for k in range(4)
    ]
    py5.stroke(*FIL_DOR_HIGH)
    py5.stroke_weight(2.4)
    py5.fill(44, 62, 98)
    py5.begin_shape()
    for pt in cyl_pts:
        py5.vertex(pt[0], pt[1])
    py5.end_shape(py5.CLOSE)

    # Corner lantern pegs
    py5.no_stroke()
    py5.fill(*CRAMOISI_HIGH)
    for pt in cyl_pts:
        py5.circle(pt[0], pt[1], 11.0)
    py5.fill(*FIL_DOR_HIGH)
    py5.circle(cx_d, cy_d, 14.0)

    draw_kv_rows(RIGHT_X + 285, CARD_Y_BOT + 96, [
        ("LANTERN PRISM", "Square Oak & Brass Cylindre Carre"),
        ("INDEXING STEP", "90.0 DEG Quarter-Turn per Pick"),
        ("PRESS STROKE", "Swinging Batten Frame (Presse)"),
        ("REGISTRATION PEGS", "2 Conical Brass Etoiles (Lanterns)"),
        ("REPEAT LENGTH", "48 Laced Cards = 1 Medallion Cycle"),
        ("ACTIVE PICK ROW", f"Card #{int(np.floor((tau / (2.0 * np.pi)) * PATTERN_ROWS)) % PATTERN_ROWS + 1:02d} / 48"),
        ("ADA LOVELACE LOOP", "Continuous Endless Card Chain"),
    ])

    # FIG. 08 Oscillogram: Binary Bitstream & Griffe Harness Load
    mid_y_bot = CARD_Y_BOT + CARD_H_BOT * 0.49
    ox, oy, ow, oh = RIGHT_X + 28, mid_y_bot + 78, CARD_W - 56, 265.0
    py5.fill(*LOOM_DARK)
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

    # Plot 32-column binary step waveform for active card + smooth Griffe tension wave
    pick_cur = int(np.floor((tau / (2.0 * np.pi)) * PATTERN_ROWS)) % PATTERN_ROWS
    bits = BINARY_PUNCH_MATRIX[pick_cur]
    step_w = (ow - 32.0) / PATTERN_COLS
    bit_segs = []
    for c in range(PATTERN_COLS):
        x0_b = ox + 16.0 + c * step_w
        x1_b = x0_b + step_w
        yb = oy + oh * (0.26 if bits[c] == 1 else 0.74)
        bit_segs.append([x0_b, yb, x1_b, yb])
        if c < PATTERN_COLS - 1:
            yb_next = oy + oh * (0.26 if bits[c + 1] == 1 else 0.74)
            bit_segs.append([x1_b, yb, x1_b, yb_next])

    py5.stroke(*FIL_DOR_HIGH)
    py5.stroke_weight(2.2)
    py5.lines(np.array(bit_segs, dtype=np.float32))

    # Continuous shuttle & griffe harmonic tension curves
    xs_osc = np.linspace(0.0, 1.0, 150)
    x_px = ox + 16.0 + xs_osc * (ow - 32.0)
    y_griffe_w = oy + oh * 0.50 - (oh * 0.30) * np.sin(xs_osc * 4.0 * np.pi - tau * 2.0) * (0.65 + 0.35 * np.cos(xs_osc * 2.0 * np.pi))
    segs_g = np.empty((len(xs_osc) - 1, 4), dtype=np.float32)
    segs_g[:, 0], segs_g[:, 1] = x_px[:-1], y_griffe_w[:-1]
    segs_g[:, 2], segs_g[:, 3] = x_px[1:], y_griffe_w[1:]
    py5.stroke(*CRAMOISI_HIGH)
    py5.stroke_weight(2.0)
    py5.lines(segs_g)

    py5.no_stroke()
    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(12)
    py5.text(
        "GOLD: 32-CHANNEL BINARY PUNCH BITSTREAM (1 = LIFT / 0 = STAY) // CRIMSON: GRIFFE HARNESS TENSION WAVE",
        ox + 4, oy + oh + 14,
    )


def draw_header_and_footer(tau):
    # Subtle Mise-en-Carte point-paper background ruling
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
        "JACQUARD-VERDOL PUNCHED CARD LOOM // LYON GRAND FACONNE LAMPAS BROCADE",
        CX, 64,
    )
    py5.fill(*TEXT_ACCENT)
    py5.text_size(14)
    py5.text(
        "FALCON-JACQUARD BINARY PASTEBOARD CHAIN (1728/1804), 8-END SATIN DE LYON & BABBAGE-LOVELACE ANALYTICAL WEAVING",
        CX, 100,
    )

    py5.fill(*TEXT_SECONDARY)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(13)
    py5.text(
        "32-HOOK BINARY ARCADES HARNESS // CHAINE DE FOND + CHAINE DE LIAGE // CRAMOISI, FIL D'OR 24K & CELADON WEFT LATS",
        104, HEIGHT - 60,
    )
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text(
        f"4K PROCEDURAL TEXTILE MECHANICS // HARMONIC PHASE TAU = {tau / (2.0 * np.pi):.3f} (12.0s @ 60FPS)",
        WIDTH - 104, HEIGHT - 60,
    )


def draw():
    frame_idx = py5.frame_count - 1
    tau = (frame_idx / TOTAL_FRAMES) * 2.0 * np.pi

    py5.background(*BG_VELLUM)

    draw_header_and_footer(tau)
    draw_jacquard_loom_medallion(tau)
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


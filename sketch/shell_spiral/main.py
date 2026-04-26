from pathlib import Path
import numpy as np
import py5

SKETCH_DIR = Path(__file__).parent
PREVIEW_FRAME = 60

PREVIEW_SIZE = (1920, 1080)
OUTPUT_SIZE  = (3840, 2160)
SIZE = PREVIEW_SIZE

# Theme: "Growth spiral" — logarithmic nautilus shell cross-section
# The shell grows so that each whorl is a scaled copy of the previous one
# Parameters define the shell geometry

# Shell parameters (nautilus-like)
WHORLS       = 4.5       # number of complete whorls
GROWTH_RATE  = 0.18      # b: r = r0 * exp(b * θ) — how fast the shell expands
N_CHAMBERS   = 32        # number of chambers (septa)
TUBE_RATIO   = 0.85      # inner radius as fraction of outer radius (tube thickness)

# Palette: ivory shell, warm ochre septa, dark maroon inner shadow
BG_COL       = (16,  12,   8)    # near-black warm
OUTER_COL    = (232, 222, 196)   # #e8dec4 ivory-cream outer whorl
INNER_COL    = (180, 150, 100)   # #b49664 warm ochre inner
SEPTUM_COL   = (80,   54,  30)   # #50361e dark brown septa (chamber walls)
SHADOW_COL   = (40,   24,  12)   # #28180c very dark for center shadow
UMBO_COL     = (55,   35,  18)   # #372312 for the tight center whorl


def setup():
    py5.size(*SIZE)
    py5.background(*BG_COL)

    CX = SIZE[0] * 0.50
    CY = SIZE[1] * 0.50
    MAX_R = SIZE[1] * 0.44   # maximum outer radius

    # Compute the scale factor: at θ = 2π*WHORLS, r should be MAX_R
    r0 = MAX_R * np.exp(-GROWTH_RATE * 2 * np.pi * WHORLS)

    # Draw from outside inward (so inner whorls overlap correctly)
    # Outer boundary: r = r0 * exp(b * θ)
    # Inner boundary: r_inner = r * TUBE_RATIO

    py5.no_stroke()

    # Fill complete outer shell area first (ivory)
    n_pts = 800
    theta_full = np.linspace(0, 2 * np.pi * WHORLS, n_pts)
    r_out = r0 * np.exp(GROWTH_RATE * theta_full)
    r_in  = r_out * TUBE_RATIO

    # Draw outer spiral region (ivory)
    py5.fill(*OUTER_COL, 255)
    py5.begin_shape()
    # Outer boundary (counter-clockwise)
    for i in range(n_pts):
        x = CX + r_out[i] * np.cos(theta_full[i] - np.pi / 2)
        y = CY + r_out[i] * np.sin(theta_full[i] - np.pi / 2)
        py5.vertex(x, y)
    # Inner boundary (clockwise, reversed)
    for i in range(n_pts - 1, -1, -1):
        x = CX + r_in[i] * np.cos(theta_full[i] - np.pi / 2)
        y = CY + r_in[i] * np.sin(theta_full[i] - np.pi / 2)
        py5.vertex(x, y)
    py5.end_shape(py5.CLOSE)

    # Chamber coloring — each chamber alternates slightly in tone
    chamber_angles = np.linspace(0, 2 * np.pi * WHORLS, N_CHAMBERS + 1)
    for ci in range(N_CHAMBERS):
        a0 = chamber_angles[ci]
        a1 = chamber_angles[ci + 1]
        n_seg = 30
        thetas = np.linspace(a0, a1, n_seg)
        r_o = r0 * np.exp(GROWTH_RATE * thetas)
        r_i = r_o * TUBE_RATIO

        # Shade: outer whorls lighter, inner darker
        age = 1.0 - ci / N_CHAMBERS   # 1 = innermost, 0 = outermost
        r_c = int(OUTER_COL[0] * (1 - age * 0.35) + INNER_COL[0] * age * 0.35 + SHADOW_COL[0] * age * 0.2)
        g_c = int(OUTER_COL[1] * (1 - age * 0.35) + INNER_COL[1] * age * 0.35 + SHADOW_COL[1] * age * 0.2)
        b_c = int(OUTER_COL[2] * (1 - age * 0.35) + INNER_COL[2] * age * 0.35 + SHADOW_COL[2] * age * 0.2)

        py5.fill(r_c, g_c, b_c, 200)
        py5.begin_shape()
        for i in range(n_seg):
            x = CX + r_o[i] * np.cos(thetas[i] - np.pi / 2)
            y = CY + r_o[i] * np.sin(thetas[i] - np.pi / 2)
            py5.vertex(x, y)
        for i in range(n_seg - 1, -1, -1):
            x = CX + r_i[i] * np.cos(thetas[i] - np.pi / 2)
            y = CY + r_i[i] * np.sin(thetas[i] - np.pi / 2)
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

    # Draw septa (chamber walls) as thin radial lines at each chamber boundary
    py5.stroke(*SEPTUM_COL)
    py5.stroke_weight(1.8)
    for ci in range(N_CHAMBERS + 1):
        a = chamber_angles[ci]
        r_o_pt = r0 * np.exp(GROWTH_RATE * a)
        r_i_pt = r_o_pt * TUBE_RATIO
        x_o = CX + r_o_pt * np.cos(a - np.pi / 2)
        y_o = CY + r_o_pt * np.sin(a - np.pi / 2)
        x_i = CX + r_i_pt * np.cos(a - np.pi / 2)
        y_i = CY + r_i_pt * np.sin(a - np.pi / 2)
        py5.line(x_i, y_i, x_o, y_o)

    # Dark center (columella) — the tight inner spiral
    py5.no_stroke()
    py5.fill(*SHADOW_COL)
    inner_r = r0 * TUBE_RATIO * 1.1
    py5.ellipse(CX, CY, inner_r * 2, inner_r * 2)

    # Outer outline of the shell
    py5.no_fill()
    py5.stroke(*SEPTUM_COL, 180)
    py5.stroke_weight(1.2)
    py5.begin_shape()
    for i in range(n_pts):
        x = CX + r_out[i] * np.cos(theta_full[i] - np.pi / 2)
        y = CY + r_out[i] * np.sin(theta_full[i] - np.pi / 2)
        py5.vertex(x, y)
    py5.end_shape()


def draw():
    if py5.frame_count == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / "preview.png"))
        py5.exit_sketch()


py5.run_sketch()

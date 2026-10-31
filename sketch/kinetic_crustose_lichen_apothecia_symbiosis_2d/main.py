"""
kinetic_crustose_lichen_apothecia_symbiosis_2d
Autonomous Generative py5 Media Art Animation
Genre: Organic / Morphogenesis
Theme: Crustose & Foliose Lichen Symbiosis and Apothecia Morphogenesis on Alpine Basalt
12.0s Seamless Loop (720 frames @ 60 FPS, 4K Master)
Strictly Anonymous: Zero signatures, seals (落款), monograms, initials, or personal marks.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import py5

# Master 4K Resolution
WIDTH, HEIGHT = 3840, 2160
TOTAL_FRAMES = 720
FPS = 60

WORK_DIR = Path(__file__).resolve().parent
WORK_NAME = WORK_DIR.name
FRAMES_DIR = WORK_DIR / "frames"
PREVIEW_PATH = WORK_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_VIDEO = WORK_DIR / f"{WORK_NAME}.mp4"

# Static Basalt Rock Geologic Substrate (Stable across frames)
SEED = int(np.random.randint(1, 1000000))
RNG = np.random.RandomState(SEED)

# Geological foliation cracks and fractures
N_CRACKS = 320
CX1 = RNG.uniform(60, WIDTH - 60, N_CRACKS)
CY1 = RNG.uniform(60, HEIGHT - 60, N_CRACKS)
C_LEN = RNG.uniform(70, 360, N_CRACKS)
C_ANG = RNG.uniform(-0.25, 0.35, N_CRACKS) + np.pi * 0.22
CX2 = CX1 + C_LEN * np.cos(C_ANG)
CY2 = CY1 + C_LEN * np.sin(C_ANG)
CRACK_LINES = np.column_stack([CX1, CY1, CX2, CY2])

# Quartz crystalline mineral veins
N_VEINS = 75
VX1 = RNG.uniform(80, WIDTH - 80, N_VEINS)
VY1 = RNG.uniform(80, HEIGHT - 80, N_VEINS)
V_LEN = RNG.uniform(120, 520, N_VEINS)
V_ANG = RNG.uniform(-0.15, 0.25, N_VEINS) + np.pi * 0.22
VX2 = VX1 + V_LEN * np.cos(V_ANG)
VY2 = VY1 + V_LEN * np.sin(V_ANG)
VEIN_LINES = np.column_stack([VX1, VY1, VX2, VY2])

# Quartz and pyroxene mineral flecks
N_QUARTZ = 650
QX = RNG.uniform(30, WIDTH - 30, N_QUARTZ)
QY = RNG.uniform(30, HEIGHT - 30, N_QUARTZ)
QR = RNG.uniform(1.8, 5.0, N_QUARTZ)
QA = RNG.randint(40, 145, N_QUARTZ)

# Colony Definitions
COLONIES = [
    {"xc": WIDTH * 0.46, "yc": HEIGHT * 0.48, "r": 720.0, "type": "parmelia", "seed": 101, "n_apoth": 42},
    {"xc": WIDTH * 0.77, "yc": HEIGHT * 0.34, "r": 500.0, "type": "xanthoria", "seed": 202, "n_apoth": 32},
    {"xc": WIDTH * 0.23, "yc": HEIGHT * 0.68, "r": 540.0, "type": "parmelia", "seed": 303, "n_apoth": 36},
    {"xc": WIDTH * 0.17, "yc": HEIGHT * 0.25, "r": 340.0, "type": "xanthoria", "seed": 404, "n_apoth": 20},
    {"xc": WIDTH * 0.83, "yc": HEIGHT * 0.76, "r": 380.0, "type": "parmelia", "seed": 505, "n_apoth": 22},
]

# Pre-generate colony parameters
N_PTS = 540
THETA = np.linspace(0, 2.0 * np.pi, N_PTS, endpoint=False)
M_MODES = np.array([3, 4, 5, 7, 9, 11, 14])

COLONY_DATA = []
for col in COLONIES:
    c_rng = np.random.RandomState(col["seed"])
    amps = c_rng.uniform(0.04, 0.13, len(M_MODES))
    phases = c_rng.uniform(0, 2.0 * np.pi, len(M_MODES))
    freq_mult = np.array([1, -1, 1, 2, -1, 1, -2])

    n_ap = col["n_apoth"]
    ap_r_dist = c_rng.uniform(0.18, 0.70, n_ap)
    ap_theta = c_rng.uniform(0, 2.0 * np.pi, n_ap)
    ap_sizes = c_rng.uniform(16.0, 52.0, n_ap)
    ap_phase = c_rng.uniform(0, 2.0 * np.pi, n_ap)

    # Rhizine filament angles and reaches
    n_rhiz = 110
    rhiz_indices = (np.linspace(0, N_PTS - 1, n_rhiz)).astype(int)
    rhiz_reach = c_rng.uniform(14.0, 42.0, n_rhiz)
    rhiz_dtheta = c_rng.uniform(-0.35, 0.35, n_rhiz)

    # Lobal radial veins
    n_lobes = 28
    lobe_angles = (np.linspace(0, 2.0 * np.pi, n_lobes, endpoint=False) + c_rng.uniform(-0.04, 0.04, n_lobes))

    COLONY_DATA.append({
        "col": col,
        "amps": amps,
        "phases": phases,
        "freq_mult": freq_mult,
        "ap_r": ap_r_dist,
        "ap_theta": ap_theta,
        "ap_sizes": ap_sizes,
        "ap_phase": ap_phase,
        "rhiz_idx": rhiz_indices,
        "rhiz_reach": rhiz_reach,
        "rhiz_dth": rhiz_dtheta,
        "lobe_angles": lobe_angles,
    })


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized 4K render session (720 frames, Seed: {SEED})")


def draw():
    frame = py5.frame_count
    # Harmonic phase tau in [0, 2pi] for exact seamless loop
    tau = 2.0 * np.pi * ((frame - 1) % TOTAL_FRAMES) / TOTAL_FRAMES

    # 1. Deep Weathered Basalt Rock Ground Plane
    py5.background(22, 25, 29)

    # Geological foliation fractures
    py5.stroke(36, 44, 52, 95)
    py5.stroke_weight(2.4)
    py5.lines(CRACK_LINES)

    # Quartz crystalline cleavage veins
    py5.stroke(165, 145, 110, 70)
    py5.stroke_weight(1.6)
    py5.lines(VEIN_LINES)

    # Mineral flecks
    py5.no_stroke()
    for qx, qy, qr, qa in zip(QX, QY, QR, QA):
        py5.fill(195, 205, 215, qa)
        py5.circle(qx, qy, qr)

    # 2. Lichen Colonies Morphogenesis
    for cd in COLONY_DATA:
        col = cd["col"]
        xc, yc = col["xc"], col["yc"]
        is_xanthoria = (col["type"] == "xanthoria")

        # Dynamic breathing radius
        breathe = 1.0 + 0.038 * np.sin(tau + col["seed"] * 0.1)
        R_base = col["r"] * breathe

        # Compute dynamic crenulated boundary
        r_mod = np.ones(N_PTS)
        for m, amp, ph, fm in zip(M_MODES, cd["amps"], cd["phases"], cd["freq_mult"]):
            r_mod += amp * np.cos(m * THETA + ph + fm * tau)

        bx = xc + R_base * r_mod * np.cos(THETA)
        by = yc + R_base * r_mod * np.sin(THETA) * 0.92

        # Soft Colony Drop Shadow onto Basalt Substrate
        sh_dx, sh_dy = 28.0, 36.0
        py5.fill(10, 12, 14, 130)
        py5.no_stroke()
        py5.begin_shape()
        for x, y in zip(bx + sh_dx, by + sh_dy):
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

        # Marginal Rhizines (fine rooting fungal filaments extending onto stone)
        py5.stroke(18, 22, 26, 185)
        py5.stroke_weight(1.8)
        rh_lines = []
        for idx, reach, dth in zip(cd["rhiz_idx"], cd["rhiz_reach"], cd["rhiz_dth"]):
            rx1 = bx[idx]
            ry1 = by[idx]
            ang = THETA[idx] + dth
            rx2 = rx1 + reach * np.cos(ang)
            ry2 = ry1 + reach * np.sin(ang)
            rh_lines.append([rx1, ry1, rx2, ry2])
        py5.lines(np.array(rh_lines))

        # Concentric Zonation Rings (Morphological Growth Fronts)
        if is_xanthoria:
            # Sunburst Lichen (Golden Saffron, Amber & Terracotta)
            zones = [
                (1.00, (235, 170, 58), (255, 238, 178)),  # Saffron margin with golden-white edge
                (0.85, (210, 128, 34), None),              # Rich amber-gold
                (0.68, (180, 88, 24), None),               # Deep burnt orange
                (0.50, (144, 62, 20), None),               # Terracotta core
                (0.32, (116, 54, 18), None),               # Senescent dark sienna
            ]
            ap_disc_col = (196, 66, 26)
            ap_disc_hi = (248, 128, 48)
            ap_rim_col = (255, 228, 148)
        else:
            # Shield Lichen (Pale Celadon, Sage Green & Olivaceous Slate)
            zones = [
                (1.00, (148, 184, 154), (238, 246, 238)),  # Celadon with chalk mineral white rim
                (0.85, (108, 150, 118), None),              # Sage green
                (0.68, (82, 126, 96), None),                # Deep forest lichen green
                (0.50, (68, 100, 80), None),                # Olivaceous slate
                (0.32, (86, 110, 84), None),                # Senescent olive
            ]
            ap_disc_col = (184, 90, 54)
            ap_disc_hi = (240, 140, 80)
            ap_rim_col = (236, 246, 236)

        for frac, fill_col, rim_col in zones:
            zx = xc + R_base * frac * r_mod * np.cos(THETA)
            zy = yc + R_base * frac * r_mod * np.sin(THETA) * 0.92

            py5.fill(*fill_col)
            if rim_col:
                py5.stroke(*rim_col)
                py5.stroke_weight(4.2)
            else:
                py5.no_stroke()

            py5.begin_shape()
            for x, y in zip(zx, zy):
                py5.vertex(x, y)
            py5.end_shape(py5.CLOSE)

        # Radial Hyphae Segmentation Lobes
        if is_xanthoria:
            py5.stroke(112, 50, 18, 120)
        else:
            py5.stroke(50, 80, 62, 115)
        py5.stroke_weight(2.6)

        for ang in cd["lobe_angles"]:
            idx = int((ang % (2.0 * np.pi)) / (2.0 * np.pi) * N_PTS)
            x_end = bx[idx]
            y_end = by[idx]
            t_rib = np.linspace(0.2, 1.0, 24)
            rx = xc * (1.0 - t_rib) + x_end * t_rib + 14.0 * np.sin(t_rib * np.pi * 3.0 + tau)
            ry = yc * (1.0 - t_rib) + y_end * t_rib + 14.0 * np.cos(t_rib * np.pi * 3.0 + tau)
            py5.lines(np.column_stack([rx[:-1], ry[:-1], rx[1:], ry[1:]]))

        # 3. Raised Apothecia Spore Cups (Chalice Morphology)
        for ar, ath, asz_base, aph in zip(cd["ap_r"], cd["ap_theta"], cd["ap_sizes"], cd["ap_phase"]):
            # Locate position on undulating thallus
            idx = int((ath % (2.0 * np.pi)) / (2.0 * np.pi) * N_PTS)
            ax = xc + ar * R_base * r_mod[idx] * np.cos(ath)
            ay = yc + ar * R_base * r_mod[idx] * np.sin(ath) * 0.92

            # Dynamic breathing cup size
            asz = asz_base * (1.0 + 0.065 * np.sin(tau + aph))

            # Drop shadow onto underlying thallus
            py5.fill(16, 22, 18, 120)
            py5.no_stroke()
            py5.circle(ax + 7.0, ay + 10.0, asz * 2.2)

            # Raised outer rim polygon (mineral white & chalk bevel)
            py5.fill(*ap_rim_col)
            py5.stroke(130, 110, 85)
            py5.stroke_weight(2.8)
            py5.circle(ax, ay, asz * 2.0)

            # Concave inner spore disc (terracotta / burnt sienna hymenium)
            py5.fill(*ap_disc_col)
            py5.stroke(100, 40, 20)
            py5.stroke_weight(2.0)
            py5.circle(ax, ay, asz * 1.5)

            # Inner disc shadow on top-left (concave 3D relief)
            py5.fill(85, 30, 15, 145)
            py5.no_stroke()
            py5.arc(ax, ay, asz * 1.4, asz * 1.4, np.pi * 0.8, np.pi * 1.8)

            # Inner disc specular sheen on bottom-right
            py5.fill(ap_disc_hi[0], ap_disc_hi[1], ap_disc_hi[2], 125)
            py5.no_stroke()
            py5.arc(ax + 1.0, ay + 1.5, asz * 1.1, asz * 1.1, 0.0, np.pi * 0.7)

            # Central microscopic spore pore
            py5.fill(50, 20, 10)
            py5.circle(ax, ay, asz * 0.28)

    # Save initial preview on frame 1
    if frame == 1:
        py5.save(str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Initial preview image saved to {PREVIEW_PATH.name}")

    # Fail-safe blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame}. Aborting.")
            import os
            os._exit(1)

    # Save frame for video
    frame_filename = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save(str(frame_filename))

    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[{WORK_NAME}] Rendered frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    if frame >= TOTAL_FRAMES:
        finish_render()


def finish_render():
    py5.no_loop()
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered. Compiling 4K video with FFmpeg...")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        str(OUTPUT_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[{WORK_NAME}] Master MP4 video compiled successfully: {OUTPUT_VIDEO.name}")

    # Save representative middle frame as definitive preview
    mid_frame = FRAMES_DIR / f"frame_{TOTAL_FRAMES // 2:04d}.png"
    if mid_frame.exists():
        shutil.copy(str(mid_frame), str(PREVIEW_PATH))
        print(f"[{WORK_NAME}] Updated preview snapshot from frame {TOTAL_FRAMES // 2}")

    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Temporary frames directory cleaned up.")

    import os
    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

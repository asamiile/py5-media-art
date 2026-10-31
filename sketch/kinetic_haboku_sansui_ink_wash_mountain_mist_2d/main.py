"""
Kinetic Haboku Sansui — Broken Ink Mountain Mist Dispersion 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art exploring Classical Japanese Haboku Sansui (破墨山水,
"broken ink landscape") and atmospheric valley mist dispersion across warm mulberry
torinoko washi paper (#f6f0e4).

Seven depth tiers of monumental craggy granite mountain ridges emerge out of dense,
volumetric billowing sea-of-clouds mist banks (雲海 unkai), punctuated by plunging
mountain cataracts, cantilevered bonsai-style pine boughs (松 matsu), solitary mountain
pavilions (東屋 azumaya), and a flight of soaring cranes (孤鶴 kōkaku) wheeling across
the gorge in 12.0s contemplative harmonic resonance.
"""

import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import py5

# --- Artwork Constants ---
WORK_NAME = "kinetic_haboku_sansui_ink_wash_mountain_mist_2d"
WIDTH = 3840
HEIGHT = 2160
FPS = 60
TOTAL_FRAMES = 720
DURATION_SEC = 12.0

SKETCH_DIR = Path(__file__).resolve().parent
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_FILE = SKETCH_DIR / f"{WORK_NAME}_p1.png"
OUTPUT_MP4 = SKETCH_DIR / "output.mp4"

START_TIME = 0.0

# Dynamic non-fixed runtime seed offsets
RND_OFFSET = float(np.random.uniform(10.0, 5000.0))
SUN_X = float(np.random.uniform(2700.0, 3100.0))
SUN_Y = float(np.random.uniform(360.0, 440.0))

NUM_PTS = 800
XS = np.linspace(80, WIDTH - 80, NUM_PTS)

# 6 Mountain Tiers configuration (scaled to 4K: 3840 x 2160)
TIERS_CFG = [
    # Tier 0: Deepest distant ethereal mountain summits (Kōen - High Distance)
    {
        "peaks": [(720, 420, 520), (1560, 320, 640), (2440, 440, 560), (3360, 360, 620)],
        "base_y": 880,
        "col_body": (205, 212, 224), "alpha_body": 95,
        "col_wash": (222, 228, 238),
        "col_edge": (175, 185, 202), "edge_w": 2.4,
        "crag_amp": 70,
        "mist_y": 840, "mist_thick": 240, "mist_dens": 230
    },
    # Tier 1: Far mountain massifs with sheer vertical bluffs
    {
        "peaks": [(360, 580, 480), (1120, 500, 680), (2040, 540, 600), (2960, 480, 640), (3640, 600, 440)],
        "base_y": 1100,
        "col_body": (168, 178, 194), "alpha_body": 135,
        "col_wash": (190, 200, 215),
        "col_edge": (138, 148, 168), "edge_w": 3.0,
        "crag_amp": 110,
        "mist_y": 1040, "mist_thick": 260, "mist_dens": 240
    },
    # Tier 2: Mid-distance crags with Azurite Gunjō glaze
    {
        "peaks": [(640, 760, 560), (1480, 660, 760), (2480, 700, 640), (3280, 740, 580)],
        "base_y": 1320,
        "col_body": (118, 134, 156), "alpha_body": 175,
        "col_wash": (90, 115, 142), # Gunjō indigo mineral wash
        "col_edge": (82, 96, 120), "edge_w": 3.6,
        "crag_amp": 150,
        "mist_y": 1260, "mist_thick": 280, "mist_dens": 245
    },
    # Tier 3: Central Great Mountain Massif with Raw Umber Taisha sunlit face
    {
        "peaks": [(320, 980, 520), (1160, 860, 840), (2120, 920, 720), (3040, 960, 680)],
        "base_y": 1540,
        "col_body": (82, 94, 110), "alpha_body": 210,
        "col_wash": (132, 102, 74), # Raw umber taisha glaze
        "col_edge": (52, 62, 78), "edge_w": 4.4,
        "crag_amp": 180,
        "mist_y": 1480, "mist_thick": 300, "mist_dens": 250,
        "waterfalls": [
            {"x": 1560, "drop": 300, "w": 9.0}
        ]
    },
    # Tier 4: Fore-middle forested ridge with Celadon Rokushō glaze & waterfall
    {
        "peaks": [(760, 1240, 720), (1680, 1160, 880), (2680, 1200, 800), (3520, 1280, 600)],
        "base_y": 1760,
        "col_body": (50, 62, 70), "alpha_body": 240,
        "col_wash": (42, 85, 70), # Celadon rokushō glaze
        "col_edge": (30, 40, 48), "edge_w": 5.2,
        "crag_amp": 170,
        "mist_y": 1700, "mist_thick": 300, "mist_dens": 255,
        "waterfalls": [
            {"x": 2280, "drop": 280, "w": 8.0}
        ]
    },
    # Tier 5: Foreground Promontory Crags & Pine Cliffs (Rich Pitch Sumi Nōboku)
    {
        "peaks": [(280, 1580, 680), (1080, 1500, 880), (2200, 1520, 920), (3280, 1560, 760)],
        "base_y": 1980,
        "col_body": (16, 20, 26), "alpha_body": 255,
        "col_wash": (28, 34, 42),
        "col_edge": (6, 8, 12), "edge_w": 6.8,
        "crag_amp": 140,
        "mist_y": 1920, "mist_thick": 260, "mist_dens": 255
    }
]

# Solitary Mountain Pavilions (東屋 Azumaya) perched on spurs
PAVILIONS = [
    {"tier": 3, "x": 2120, "scl": 1.7},
    {"tier": 4, "x": 760, "scl": 2.2}
]

# Cantilevered Bonsai Pines (松 Matsu)
PINE_SITES = [
    (4, 680, 2.6, -1),
    (4, 1760, 2.7, 1),
    (4, 3120, 2.5, -1),
    (5, 480, 3.1, 1),
    (5, 1360, 3.2, -1),
    (5, 2360, 3.0, 1),
    (5, 3320, 2.9, -1)
]

# Cranes (孤鶴 Kōkaku)
CRANES = [
    {"cx": 2620, "cy": 310, "scl": 2.2, "off": 0.0},
    {"cx": 2730, "cy": 356, "scl": 1.8, "off": 0.4},
    {"cx": 2520, "cy": 276, "scl": 1.6, "off": 0.7},
    {"cx": 2830, "cy": 330, "scl": 1.5, "off": 1.1},
    {"cx": 2670, "cy": 416, "scl": 1.7, "off": 1.5}
]

def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)

def setup():
    global START_TIME
    START_TIME = time.time()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K 60fps render: {TOTAL_FRAMES} frames...")

def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES)
    omega = 2.0 * math.pi

    # 1. Warm Mulberry Washi Paper Ground (#f6f0e4)
    py5.background(246, 240, 228)

    # 2. Subtle Washi Laid Sieve Lines (簀の目 su-no-me)
    py5.stroke(232, 224, 210, 110)
    py5.stroke_weight(1.5)
    for x in range(120, WIDTH - 120, 96):
        py5.line(x, 80, x, HEIGHT - 80)
    py5.stroke(236, 228, 214, 80)
    for y in range(120, HEIGHT - 120, 48):
        py5.line(80, y, WIDTH - 80, y)

    # 3. Celestial Sky Atmosphere & Sunlit Wash
    py5.no_stroke()
    for sy in range(80, 960, 12):
        interp = (sy - 80) / 880.0
        r = int(246 * (1 - interp) + 236 * interp)
        g = int(240 * (1 - interp) + 228 * interp)
        b = int(228 * (1 - interp) + 216 * interp)
        a = int(85 * (1.0 - interp))
        py5.fill(r, g, b, a)
        py5.rect(80, sy, WIDTH - 160, 12)

    # Distant Pale Sun in Golden Haze
    for r_ring in range(190, 0, -6):
        alpha_ring = int(24 * (1.0 - r_ring / 190.0))
        py5.fill(235, 208, 170, alpha_ring)
        py5.circle(SUN_X, SUN_Y, r_ring * 2)

    # Soaring Cranes (Kōkaku) wheeling across the gorge
    for cr in CRANES:
        t_cr = omega * tau + cr["off"]
        bx = cr["cx"] + 80.0 * math.sin(t_cr * 0.8)
        by = cr["cy"] + 28.0 * math.cos(t_cr * 0.8)
        scl = cr["scl"]
        flap = math.sin(t_cr * 4.0) * 0.35
        # White wings
        py5.stroke(252, 250, 245, 240)
        py5.stroke_weight(2.2 * scl)
        py5.line(bx, by, bx - 14 * scl, by - (8 + flap * 10) * scl)
        py5.line(bx, by, bx + 14 * scl, by - (8 - flap * 10) * scl)
        # Black sumi wingtips
        py5.stroke(24, 28, 34, 240)
        py5.stroke_weight(1.8 * scl)
        py5.line(bx - 14 * scl, by - (8 + flap * 10) * scl, bx - 22 * scl, by - (12 + flap * 14) * scl)
        py5.line(bx + 14 * scl, by - (8 - flap * 10) * scl, bx + 22 * scl, by - (12 - flap * 14) * scl)

    # 4. Mountain Tiers & Volumetric Cloud Seas
    ridge_profiles = []

    for t_idx, t in enumerate(TIERS_CFG):
        # 1. Calculate height profile
        ys = np.full(NUM_PTS, float(t["base_y"]))
        for px, py_val, pw in t["peaks"]:
            dist_sq = ((XS - px) / pw) ** 2
            bell = np.exp(-dist_sq * 2.8)
            bell = np.power(bell, 0.85)
            ys -= (t["base_y"] - py_val) * bell

        crag_amp = t["crag_amp"]
        for k in range(1, 5):
            freq = k * 0.0024 * (1.0 + t_idx * 0.15)
            phase = RND_OFFSET + t_idx * 2.3 + k * 1.7
            # Cyclic harmonic breathing
            ys += (crag_amp / (k ** 0.9)) * np.sin(XS * freq + phase + 0.04 * math.sin(omega * tau + t_idx))
            # Axe-cut sharp vertical clefts
            ys += (crag_amp * 0.22 / k) * np.abs(np.cos(XS * freq * 2.1 + phase))

        ys = np.clip(ys, 160, HEIGHT - 80)
        ridge_profiles.append((XS, ys))

        # 2. Draw Solid Mountain Polygon down to bottom datum HEIGHT - 80
        py5.fill(t["col_body"][0], t["col_body"][1], t["col_body"][2], t["alpha_body"])
        py5.no_stroke()
        py5.begin_shape()
        py5.vertex(80, HEIGHT - 80)
        for x_val, y_val in zip(XS, ys):
            py5.vertex(x_val, y_val)
        py5.vertex(WIDTH - 80, HEIGHT - 80)
        py5.end_shape(py5.CLOSE)

        # 3. Mineral Wash Glaze on Upper Slopes
        wash = t["col_wash"]
        py5.begin_shape(py5.QUAD_STRIP)
        for x_val, y_val in zip(XS, ys):
            py5.fill(wash[0], wash[1], wash[2], int(t["alpha_body"] * 0.42))
            py5.no_stroke()
            py5.vertex(x_val, y_val)
            py5.fill(wash[0], wash[1], wash[2], 0)
            py5.vertex(x_val, min(HEIGHT - 80, y_val + 340))
        py5.end_shape()

        # 4. Axe-cut Texture Strokes (斧劈皴)
        py5.stroke(t["col_edge"][0], t["col_edge"][1], t["col_edge"][2], int(t["alpha_body"] * 0.65))
        py5.stroke_weight(t["edge_w"] * 0.75)
        for i in range(15, NUM_PTS - 15, 6):
            slope = (ys[i+2] - ys[i-2]) / (XS[i+2] - XS[i-2] + 1e-5)
            if abs(slope) > 0.38:
                cx = XS[i]
                cy = ys[i]
                length = min(170.0, 36.0 + abs(slope) * 64.0)
                angle = math.pi * 0.44 if slope > 0 else math.pi * 0.56
                py5.line(cx, cy, cx + math.cos(angle) * length, cy + math.sin(angle) * length)

        # 5. Bold Silhouette Calligraphic Edge
        py5.stroke(t["col_edge"][0], t["col_edge"][1], t["col_edge"][2], 245)
        py5.stroke_weight(t["edge_w"])
        for i in range(NUM_PTS - 1):
            py5.line(XS[i], ys[i], XS[i+1], ys[i+1])

        # 6. Waterfalls nestled in mountain clefts
        if "waterfalls" in t:
            for wf in t["waterfalls"]:
                w_x = wf["x"]
                idx = int((w_x - 80) / (WIDTH - 160) * (NUM_PTS - 1))
                w_start = ys[idx] + 4
                w_end = w_start + wf["drop"]
                w_w = wf["w"]
                # Dark rock fissure
                py5.stroke(14, 18, 24, 230)
                py5.stroke_weight(w_w * 3.0)
                py5.line(w_x, w_start, w_x + 8, w_end)
                # Cascading white torrent
                py5.stroke(255, 255, 255, 250)
                py5.stroke_weight(w_w)
                for cy in range(int(w_start), int(w_end), 10):
                    drift_w = math.sin((cy - w_start) * 0.045 + omega * tau * 3.0) * 4.4
                    py5.line(w_x + drift_w, cy, w_x + drift_w, cy + 10)
                # Billowing spray mist cloud at pool
                for sr in range(90, 0, -8):
                    py5.fill(248, 244, 234, int(90 * (1.0 - sr / 90.0)))
                    py5.no_stroke()
                    py5.circle(w_x + 8, w_end + 12, sr * 2)

        # 7. Dense Volumetric Billowing Cloud Sea / Valley Mist (雲海)
        # 2-stage ribbon: Top to Mid (0 -> max_alpha), Mid to Bot (max_alpha -> 0)
        drift_x = math.sin(omega * tau + t_idx * 0.85) * 180.0
        mist_y = t["mist_y"]
        mist_thick = t["mist_thick"]
        mist_dens = t["mist_dens"]

        for layer in range(3):
            l_off = (layer - 1) * 44
            peak_alpha = int(mist_dens * (0.65 + 0.3 * (1.0 - abs(layer - 1) / 1.0)))

            w1 = np.sin(XS * 0.0025 + drift_x * 0.018 + layer * 1.6) * (52.0 + layer * 12.0)
            w2 = np.cos(XS * 0.0055 + drift_x * 0.012 + layer * 0.8) * 32.0
            
            top_m = mist_y + l_off - mist_thick * 0.5 + w1
            mid_m = mist_y + l_off + w1 * 0.5 + w2 * 0.5
            bot_m = mist_y + l_off + mist_thick * 0.5 + w2

            # Upper fade (top -> mid)
            py5.begin_shape(py5.QUAD_STRIP)
            for x_val, ym_top, ym_mid in zip(XS, top_m, mid_m):
                py5.fill(248, 244, 234, 0)
                py5.no_stroke()
                py5.vertex(x_val, ym_top)
                py5.fill(248, 244, 234, peak_alpha)
                py5.vertex(x_val, ym_mid)
            py5.end_shape()

            # Lower fade (mid -> bot)
            py5.begin_shape(py5.QUAD_STRIP)
            for x_val, ym_mid, ym_bot in zip(XS, mid_m, bot_m):
                py5.fill(248, 244, 234, peak_alpha)
                py5.no_stroke()
                py5.vertex(x_val, ym_mid)
                py5.fill(248, 244, 234, 0)
                py5.vertex(x_val, ym_bot)
            py5.end_shape()

    # 5. Architectural Feature: Mountain Pavilions (東屋 Azumaya)
    for pav in PAVILIONS:
        xs_r, ys_r = ridge_profiles[pav["tier"]]
        idx = int((pav["x"] - 80) / (WIDTH - 160) * (NUM_PTS - 1))
        idx = np.clip(idx, 0, NUM_PTS - 1)
        px = pav["x"]
        py_val = ys_r[idx]
        scl = pav["scl"]

        py5.stroke(14, 18, 24, 255)
        py5.stroke_weight(2.0 * scl)
        py5.line(px - 14 * scl, py_val, px - 14 * scl, py_val - 12 * scl)
        py5.line(px + 14 * scl, py_val, px + 14 * scl, py_val - 12 * scl)
        py5.line(px, py_val, px, py_val - 12 * scl)
        py5.stroke_weight(3.0 * scl)
        py5.line(px - 18 * scl, py_val - 12 * scl, px + 18 * scl, py_val - 12 * scl)
        py5.stroke_weight(1.8 * scl)
        py5.line(px - 12 * scl, py_val - 12 * scl, px - 12 * scl, py_val - 26 * scl)
        py5.line(px + 12 * scl, py_val - 12 * scl, px + 12 * scl, py_val - 26 * scl)
        py5.stroke_weight(2.5 * scl)
        py5.line(px - 26 * scl, py_val - 24 * scl, px, py_val - 34 * scl)
        py5.line(px, py_val - 34 * scl, px + 26 * scl, py_val - 24 * scl)
        py5.stroke_weight(1.8 * scl)
        py5.line(px - 26 * scl, py_val - 24 * scl, px - 30 * scl, py_val - 27 * scl)
        py5.line(px + 26 * scl, py_val - 24 * scl, px + 30 * scl, py_val - 27 * scl)
        py5.stroke_weight(2.0 * scl)
        py5.line(px, py_val - 34 * scl, px, py_val - 40 * scl)

    # 6. Gnarled Cantilevered Pines (松 Matsu) rooted on Promontory Crags
    for t_idx, px, scl, ldir in PINE_SITES:
        xs_r, ys_r = ridge_profiles[t_idx]
        idx = int((px - 80) / (WIDTH - 160) * (NUM_PTS - 1))
        idx = np.clip(idx, 0, NUM_PTS - 1)
        py_val = ys_r[idx]

        py5.stroke(10, 14, 18, 255)
        py5.stroke_weight(5.5 * scl)
        py5.line(px - 8 * scl, py_val + 5 * scl, px, py_val)
        py5.line(px + 8 * scl, py_val + 6 * scl, px, py_val)
        
        x1 = px + ldir * 8 * scl
        y1 = py_val - 28 * scl
        py5.line(px, py_val, x1, y1)
        
        x2 = x1 + ldir * 26 * scl
        y2 = y1 - 22 * scl
        py5.stroke_weight(4.0 * scl)
        py5.line(x1, y1, x2, y2)
        
        b1_x = x2 + ldir * 32 * scl
        b1_y = y2 - 8 * scl
        py5.stroke_weight(2.6 * scl)
        py5.line(x2, y2, b1_x, b1_y)
        
        b2_x = x2 - ldir * 18 * scl
        b2_y = y2 - 20 * scl
        py5.line(x2, y2, b2_x, b2_y)

        origins = [(x2, y2), (b1_x, b1_y), (b2_x, b2_y), (x1, y1)]
        for ox, oy in origins:
            for cluster_dx, cluster_dy in [(-8, -4), (8, -6), (0, -10)]:
                cx = ox + cluster_dx * scl
                cy = oy + cluster_dy * scl
                for a_deg in range(-75, 85, 16):
                    a_rad = math.radians(a_deg) + (0.12 * ldir)
                    py5.stroke(18, 48, 38, 235)
                    py5.stroke_weight(1.4 * scl)
                    len_n = (22.0 + 5.0 * math.cos(a_deg * 2.0)) * scl
                    py5.line(cx, cy, cx + math.cos(a_rad) * len_n, cy + math.sin(a_rad) * len_n)

    # 7. Tranquil Foreground River Basin & Sumi Ripple Lines (Hei'en - Level Distance)
    py5.stroke(22, 28, 36, 140)
    py5.stroke_weight(2.0)
    for ry in range(HEIGHT - 200, HEIGHT - 90, 24):
        interp = (ry - (HEIGHT - 200)) / 110.0
        for rx in range(120, WIDTH - 120, 48):
            r_len = 32.0 + 16.0 * math.sin(rx * 0.01 + ry * 0.025 + omega * tau * 2.0)
            py5.line(rx, ry, rx + r_len, ry)

    # 8. Traditional Archival Mounting Borders and Latin Calligraphic Title (Kakejiku Scroll)
    py5.no_fill()
    py5.stroke(48, 52, 60)
    py5.stroke_weight(4.0)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke(148, 134, 116, 180) # Antique silk ribbon border
    py5.stroke_weight(2.0)
    py5.rect(70, 70, WIDTH - 140, HEIGHT - 140)
    py5.stroke(48, 52, 60, 130)
    py5.rect(76, 76, WIDTH - 152, HEIGHT - 152)

    # Header Telemetry
    py5.fill(36, 42, 50)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(24)
    py5.text("SANSUI JUNI-KEI — TRADITIONAL AERIAL PERSPECTIVE (SAN'EN)", WIDTH / 2.0, 96)
    py5.text_size(38)
    py5.text("HABOKU SANSUI — BROKEN INK MOUNTAIN MIST DISPERSION", WIDTH / 2.0, 136)
    py5.text_size(22)
    py5.fill(138, 88, 52)
    py5.text("SEVEN-TIER AERIAL RIDGES • VALLEY FOG ADVECTION • AZURITE & RAW UMBER GLAZES", WIDTH / 2.0, 186)

    # Bottom Telemetry
    py5.fill(45, 52, 62)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(22)
    py5.text("KOEN (HIGH DISTANCE) • SHIN'EN (DEEP DISTANCE) • HEI'EN (LEVEL DISTANCE)", 108, HEIGHT - 92)
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text("4K GENERATIVE MEDIA ART • 12.0s CONTEMPLATIVE HARMONIC CYCLE", WIDTH - 108, HEIGHT - 92)

    # Save frame
    frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at frame 0
    if frame == 0:
        py5.save_frame(str(PREVIEW_FILE))
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_FILE}")

    if (frame + 1) % 60 == 0 or frame + 1 == TOTAL_FRAMES:
        elapsed = time.time() - START_TIME
        fps_calc = (frame + 1) / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - (frame + 1)) / max(0.01, fps_calc)
        print(f"[{WORK_NAME}] Frame {frame+1:03d}/{TOTAL_FRAMES} ({(frame+1)/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")

def finish_and_encode():
    global START_TIME
    total_elapsed = time.time() - START_TIME
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        str(OUTPUT_MP4)
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
            
    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()

"""
kinetic_pelagic_medusa_bioluminescence_morphogenesis_2d
Autonomous Generative py5 Media Art Animation (720 frames @ 60 FPS, 12.0s seamless loop, 4K Master)

Genre: Organic / Morphogenesis / Biological Systems
Theme: Deep-sea pelagic scyphozoan jellyfish (Medusa) bioluminescent morphogenesis.
       Rhythmic coronal umbrella pulsation, undulating silken oral arms, and flowing
       tentacular zooids with bioluminescent nematocyst batteries floating through
       the hadal midnight zone.

Anti-Clustering & Diversity Compliance:
- Genre: Organic / Morphogenesis / Biological Systems (Rotates away from Signal/Glitch, Atmospheric/Painterly, Textile/Craft)
- Background: Hadal midnight pelagic abyss (#04070f, L ≈ 3%) with subtle soft light cones
- Primitives: Multi-tiered translucent nectophore umbrella bell with scalloped lappets,
  radial gastrovascular canals, fluted undulating oral arm ribbons, trailing tentacular
  filaments, and apical statocyst organ. Zero particles or point clouds.
- Strict Anonymity: Zero signatures, zero seals/hanko, zero monograms, zero author marks.
- Palette: Hadal abyss (#04070f), bioluminescent cyan (#06b6d4), emerald green (#10b981),
  topaz amber (#f59e0b), and core bio-white (#fef08a).
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_pelagic_medusa_bioluminescence_morphogenesis_2d"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")
PREVIEW_PATH = os.path.join(SCRIPT_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SCRIPT_DIR, f"{WORK_NAME}.mp4")

TOTAL_FRAMES = 720
FPS = 60
PREVIEW_FRAME = 180

# Canvas dimensions (4K UHD)
WIDTH = 3840
HEIGHT = 2160
CX = WIDTH // 2
CY = HEIGHT // 2

# Medusa morphological configuration
N_BELL_TIERS = 22
N_BELL_SAMPLES = 320
THETAS_BELL = np.linspace(-np.pi * 0.5, np.pi * 0.5, N_BELL_SAMPLES)
COS_TB, SIN_TB = np.cos(THETAS_BELL), np.sin(THETAS_BELL)

N_RIBS = 16
N_ARMS = 8
N_ARM_PTS = 220
ST_ARM = np.linspace(0.0, 1.0, N_ARM_PTS)

N_TENTS = 44
N_TENT_PTS = 220
ST_TENT = np.linspace(0.0, 1.0, N_TENT_PTS)


def setup():
    py5.size(WIDTH, HEIGHT)
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Starting render of {TOTAL_FRAMES} frames @ 60 FPS (4K Master)...")


def draw():
    frame = py5.frame_count
    if frame > TOTAL_FRAMES:
        return

    # Normalized time parameter for seamless 12.0s loop
    t_norm = (frame - 1) / TOTAL_FRAMES
    tau = 2.0 * np.pi * t_norm

    # 1. Hadal Midnight Pelagic Abyss Ground
    py5.background(4, 7, 15)

    # Ambient deep-sea pelagic light glow
    py5.no_stroke()
    for r_glow in range(400, 1600, 180):
        py5.fill(6, 32, 54, 9)
        py5.ellipse(CX, CY - 150, r_glow * 1.8, r_glow * 1.3)

    # Rhythmic coronal contraction / swimming stroke (periodic in tau)
    # Bell expands horizontally on recovery, contracts and pulses down on power stroke
    pulse_contraction = np.sin(tau)
    bell_w = 880.0 * (1.0 + 0.15 * np.cos(tau))
    bell_h = 580.0 * (1.0 - 0.18 * pulse_contraction)
    apex_y = CY - 580 + 45.0 * pulse_contraction
    margin_y = apex_y + bell_h

    # 2. Multi-tiered Translucent Nectophore Umbrella (Haeckel geometric bell)
    py5.no_fill()
    for tier in range(N_BELL_TIERS, 0, -1):
        frac = tier / N_BELL_TIERS
        rw = bell_w * (0.28 + 0.72 * frac)
        rh = bell_h * (0.28 + 0.72 * frac)

        # Scalloped rim lappets
        n_lappets = 16
        scallop = 1.0 + 0.024 * np.cos(THETAS_BELL * n_lappets + tau)
        dome_x = CX + rw * SIN_TB * scallop
        dome_y = apex_y + rh * (1.0 - COS_TB)
        dome_pts = np.column_stack([dome_x, dome_y])

        # Alternating bioluminescent cyan and bio-emerald bands
        if tier % 2 == 0:
            py5.stroke(6, 182, 212, int(28 + frac * 90))
        else:
            py5.stroke(16, 185, 129, int(22 + frac * 80))
        py5.stroke_weight(2.4 + frac * 2.2)

        py5.begin_shape()
        py5.vertices(dome_pts)
        py5.end_shape()

    # 3. Radial Gastrovascular Canal Ribs & Marginal Rhopalia
    for i in range(N_RIBS + 1):
        th = -np.pi * 0.48 + (i / N_RIBS) * (np.pi * 0.96)
        mx = CX + bell_w * np.sin(th)
        my = apex_y + bell_h * (1.0 - np.cos(th))
        cx_rib = CX + (bell_w * 0.55) * np.sin(th)
        cy_rib = apex_y + (bell_h * 0.45) * (1.0 - np.cos(th))

        py5.stroke(254, 240, 138, 140)
        py5.stroke_weight(2.4)
        py5.begin_shape()
        py5.vertex(CX, apex_y)
        py5.quadratic_vertex(cx_rib, cy_rib, mx, my)
        py5.end_shape()

        # Marginal rhopalium sense organ (bioluminescent bead at rim)
        py5.no_stroke()
        py5.fill(245, 158, 11, 230)
        py5.ellipse(mx, my, 12, 12)
        py5.fill(255, 255, 255, 255)
        py5.ellipse(mx, my, 5, 5)
        py5.no_fill()

    # 4. Fluted Undulating Oral Arms (silken manubrium frills)
    for arm in range(N_ARMS):
        frac_arm = arm / N_ARMS
        arm_ang = -np.pi * 0.42 + frac_arm * np.pi * 0.84
        ax0 = CX + 120.0 * np.sin(arm_ang)
        ay0 = margin_y - 80.0
        arm_len = 1180.0 + 150.0 * np.cos(arm * 1.5)

        cur_y = ay0 + ST_ARM * arm_len
        wave1 = np.sin(tau + ST_ARM * 12.0 + arm * 0.8) * (36.0 + ST_ARM * 88.0)
        wave2 = np.cos(tau * 2.0 - ST_ARM * 7.0 + arm * 0.5) * (18.0 + ST_ARM * 42.0)
        cur_x = ax0 + np.sin(arm_ang) * ST_ARM * 260.0 + wave1 + wave2
        arm_pts = np.column_stack([cur_x, cur_y])

        # Golden amber frill glow
        py5.stroke(245, 158, 11, 42)
        py5.stroke_weight(13.0)
        py5.begin_shape()
        py5.vertices(arm_pts)
        py5.end_shape()

        # Core translucent frill ribbon
        py5.stroke(254, 240, 138, 205)
        py5.stroke_weight(2.8)
        py5.begin_shape()
        py5.vertices(arm_pts)
        py5.end_shape()

    # 5. Trailing Bioluminescent Tentacular Zooids (44 slender filaments)
    for t_idx in range(N_TENTS):
        frac_t = t_idx / (N_TENTS - 1)
        th = -np.pi * 0.46 + frac_t * np.pi * 0.92
        tx0 = CX + bell_w * np.sin(th)
        ty0 = apex_y + bell_h * (1.0 - np.cos(th))
        t_len = 1420.0 + 320.0 * np.sin(frac_t * np.pi * 3.0 + 0.8)

        cur_y = ty0 + ST_TENT * t_len
        delay = ST_TENT * 11.0
        wave_x = np.sin(tau * 2.0 - delay + frac_t * 5.0) * (20.0 + ST_TENT * 120.0)
        wave_sub = np.cos(tau - delay * 0.6) * (12.0 + ST_TENT * 45.0)
        cur_x = tx0 + wave_x + wave_sub
        tent_pts = np.column_stack([cur_x, cur_y])

        # Chromatic bio-filament color cycling
        c_mode = t_idx % 3
        if c_mode == 0:
            py5.stroke(6, 182, 212, 125)
        elif c_mode == 1:
            py5.stroke(16, 185, 129, 115)
        else:
            py5.stroke(245, 158, 11, 120)

        py5.stroke_weight(2.0)
        py5.begin_shape()
        py5.vertices(tent_pts)
        py5.end_shape()

        # Pulsating nematocyst batteries along tentacle
        py5.no_stroke()
        for b_idx in range(6, N_TENT_PTS - 4, 18):
            bx, by = tent_pts[b_idx]
            pulse_b = np.sin(tau * 3.0 + b_idx * 0.35 + t_idx)
            nr = 4.2 * (1.0 + 0.35 * pulse_b)
            py5.fill(254, 240, 138, 220)
            py5.ellipse(bx, by, nr * 2.2, nr * 2.2)
            py5.fill(255, 255, 255, 255)
            py5.ellipse(bx, by, nr * 1.0, nr * 1.0)
        py5.no_fill()

    # 6. Apical Statocyst & Sensory Organ Crown
    py5.no_stroke()
    py5.fill(6, 182, 212, 70)
    py5.ellipse(CX, apex_y, 90, 90)
    py5.fill(245, 158, 11, 180)
    py5.ellipse(CX, apex_y, 44, 44)
    py5.fill(255, 255, 245, 255)
    py5.ellipse(CX, apex_y, 18, 18)

    # 7. Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at frame 180 (peak contraction power stroke)
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Medusa preview captured: {PREVIEW_PATH}")

    # Progress reporting
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 8. Finalize animation on reaching total frame count
    if frame == TOTAL_FRAMES:
        print("[Rendering Complete] Encoding master 4K MP4 via ffmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "17",
            "-preset", "slow",
            OUTPUT_MP4
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[Video Compiled] Master MP4 saved: {OUTPUT_MP4}")
            shutil.rmtree(FRAMES_DIR, ignore_errors=True)
            print("[Render Cleanup] Temporary frames directory removed.")
        else:
            print(f"[FFmpeg Error] {res.stderr}")

        os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

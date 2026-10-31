"""
Kinetic Hamilton Conical Refraction & Diabolical Point Singularity 2D
4K 60fps 720 frames (12.0s seamless loop)

Physical wave optics simulation of Hamilton's 1832 discovery of conical refraction
and diabolical points in biaxial anisotropic crystals (Aragonite CaCO3).
A single incident laser pencil splits into a hollow cone of light, resolving into
concentric Poggendorff dual rings, rotating orthogonal polarization vectors (Berry phase),
sweeping analyzer extinction crescent lobes, and 3D intersecting Fresnel wave sheets.
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
WORK_NAME = "kinetic_hamilton_conical_refraction_diabolical_points_2d"
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

# Precompute static angle arrays for fast vectorized 4K rendering
NUM_RAYS = 720
THETA_RAYS = np.linspace(0.0, 2.0 * np.pi, NUM_RAYS, endpoint=False)
COS_RAYS = np.cos(THETA_RAYS)
SIN_RAYS = np.sin(THETA_RAYS)
ALPHA_RAYS = THETA_RAYS * 0.5 # Berry geometric phase half-angle

NUM_NEEDLES = 72
THETA_NEEDLES = np.linspace(0.0, 2.0 * np.pi, NUM_NEEDLES, endpoint=False)
COS_NEEDLES = np.cos(THETA_NEEDLES)
SIN_NEEDLES = np.sin(THETA_NEEDLES)
ALPHA_NEEDLES = THETA_NEEDLES * 0.5
DX_NEEDLES = np.cos(ALPHA_NEEDLES)
DY_NEEDLES = np.sin(ALPHA_NEEDLES)

# 3D Fresnel Double Cone Mesh (32 spokes, 40 points per spoke)
NUM_SPOKES = 32
SPOKE_ANGLES = np.linspace(0.0, 2.0 * np.pi, NUM_SPOKES, endpoint=False)
SPOKE_S = np.linspace(-320.0, 320.0, 40)
# (NUM_SPOKES, 40, 3) 3D coordinate array
CONE_3D = np.zeros((NUM_SPOKES, 40, 3), dtype=np.float64)
for k, phi in enumerate(SPOKE_ANGLES):
    for j, s in enumerate(SPOKE_S):
        CONE_3D[k, j, 0] = s * math.cos(phi) * 0.58
        CONE_3D[k, j, 1] = s * math.sin(phi) * 0.58
        CONE_3D[k, j, 2] = abs(s) * 0.95 - 140.0

def settings():
    py5.size(WIDTH, HEIGHT)
    py5.smooth(8)

def setup():
    global START_TIME
    START_TIME = time.time()
    py5.frame_rate(FPS)
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{WORK_NAME}] Starting 4K render: {TOTAL_FRAMES} frames @ {FPS} fps...")

def draw():
    frame = py5.frame_count - 1
    if frame >= TOTAL_FRAMES:
        finish_and_encode()
        return

    tau = frame / float(TOTAL_FRAMES)
    omega = 2.0 * math.pi

    # Center coordinates
    cx, cy = WIDTH / 2.0, HEIGHT / 2.0

    # 1. Background & Precision Optical Graticule
    py5.background(7, 8, 14) # Optical bench deep obsidian

    # Optical alignment grid
    py5.stroke(24, 34, 48, 90)
    py5.stroke_weight(1.0)
    for x in range(160, WIDTH, 120):
        py5.line(x, 80, x, HEIGHT - 80)
    for y in range(160, HEIGHT, 120):
        py5.line(80, y, WIDTH - 80, y)

    # Concentric distance reticles
    py5.no_fill()
    for r in [240, 480, 720, 960]:
        py5.stroke(28, 42, 60, 75)
        py5.circle(cx, cy, r * 2.0)

    # Diagonal reticle crosshairs
    py5.stroke(28, 42, 60, 85)
    py5.line(cx - 1000, cy - 1000, cx + 1000, cy + 1000)
    py5.line(cx - 1000, cy + 1000, cx + 1000, cy - 1000)

    # 2. 3D Fresnel Double Cone Sheets (Diabolical point singularity)
    rot_y = 0.35 * math.sin(omega * tau)
    rot_x = 0.22 * math.cos(omega * tau)
    cos_ry, sin_ry = math.cos(rot_y), math.sin(rot_y)
    cos_rx, sin_rx = math.cos(rot_x), math.sin(rot_x)

    # Vectorized 3D rotation and projection
    X = CONE_3D[:, :, 0]
    Y = CONE_3D[:, :, 1]
    Z = CONE_3D[:, :, 2]

    XX = X * cos_ry + Z * sin_ry
    ZZ = -X * sin_ry + Z * cos_ry
    YY = Y * cos_rx - ZZ * sin_rx

    cam_dist = 3200.0
    denom = np.maximum(100.0, cam_dist - ZZ)
    scale = cam_dist / denom

    U = cx + XX * scale
    V = cy + YY * scale

    # Create line segments for py5.lines batching
    cone_segments = []
    for k in range(NUM_SPOKES):
        for j in range(39):
            cone_segments.append([U[k, j], V[k, j], U[k, j+1], V[k, j+1]])

    if cone_segments:
        py5.stroke(16, 185, 129, 45)
        py5.stroke_weight(1.5)
        py5.lines(np.array(cone_segments, dtype=np.float32))

    # Center diabolical singular apex
    py5.no_stroke()
    py5.fill(244, 63, 94, 230)
    py5.circle(cx, cy, 16)
    py5.fill(255, 255, 255, 255)
    py5.circle(cx, cy, 6)

    # 3. Poggendorff Dual Rings & Intensity Caustic Field
    # R0 = central Poggendorff dark ring radius
    R0 = 540.0
    dR = 76.0 * (1.0 + 0.18 * math.sin(omega * tau))
    R_inner = R0 - dR
    R_outer = R0 + dR

    gamma = omega * tau # Analyzer rotation angle

    # Malus modulation around the ring: cos^2(alpha - gamma)
    malus = np.cos(ALPHA_RAYS - gamma) ** 2

    # Inner ring lines
    len_in = 52.0 * (0.4 + 0.6 * malus)
    rA = R_inner - len_in * 0.5
    rB = R_inner + len_in * 0.5
    uA = cx + COS_RAYS * rA
    vA = cy + SIN_RAYS * rA
    uB = cx + COS_RAYS * rB
    vB = cy + SIN_RAYS * rB
    inner_lines = np.column_stack([uA, vA, uB, vB]).astype(np.float32)

    # Outer ring lines
    len_out = 56.0 * (0.4 + 0.6 * (1.0 - malus * 0.75))
    rC = R_outer - len_out * 0.5
    rD = R_outer + len_out * 0.5
    uC = cx + COS_RAYS * rC
    vC = cy + SIN_RAYS * rC
    uD = cx + COS_RAYS * rD
    vD = cy + SIN_RAYS * rD
    outer_lines = np.column_stack([uC, vC, uD, vD]).astype(np.float32)

    # Diffraction ripples
    ripple_indices = np.arange(0, NUM_RAYS, 4)
    r_rip1 = R_inner - 56.0 - 16.0 * np.sin(6.0 * THETA_RAYS[ripple_indices] + omega * tau)
    r_rip2 = R_outer + 60.0 + 20.0 * np.cos(6.0 * THETA_RAYS[ripple_indices] - omega * tau)

    cos_rip = COS_RAYS[ripple_indices]
    sin_rip = SIN_RAYS[ripple_indices]

    rip1_lines = np.column_stack([
        cx + cos_rip * (r_rip1 - 8), cy + sin_rip * (r_rip1 - 8),
        cx + cos_rip * (r_rip1 + 8), cy + sin_rip * (r_rip1 + 8)
    ]).astype(np.float32)

    rip2_lines = np.column_stack([
        cx + cos_rip * (r_rip2 - 10), cy + sin_rip * (r_rip2 - 10),
        cx + cos_rip * (r_rip2 + 10), cy + sin_rip * (r_rip2 + 10)
    ]).astype(np.float32)

    # Draw Inner Ring (Emerald Nd:YAG)
    py5.stroke(16, 185, 129, 220)
    py5.stroke_weight(3.6)
    py5.lines(inner_lines)
    py5.stroke(110, 231, 183, 140)
    py5.stroke_weight(1.4)
    py5.lines(inner_lines)

    # Draw Outer Ring (Cyan Coherent Field)
    py5.stroke(6, 182, 212, 220)
    py5.stroke_weight(3.6)
    py5.lines(outer_lines)
    py5.stroke(165, 243, 252, 140)
    py5.stroke_weight(1.4)
    py5.lines(outer_lines)

    # Draw Diffraction Fringes
    py5.stroke(52, 211, 153, 95)
    py5.stroke_weight(1.8)
    py5.lines(rip1_lines)
    py5.lines(rip2_lines)

    # Sharp Poggendorff Dark Ring (Analytical dark singularity)
    py5.no_fill()
    py5.stroke(7, 8, 14) # Pure dark background cut
    py5.stroke_weight(20.0)
    py5.circle(cx, cy, R0 * 2.0)
    py5.stroke(20, 30, 48, 230)
    py5.stroke_weight(3.0)
    py5.circle(cx, cy, R0 * 2.0)

    # 4. Polarization Vector Needles (Berry Geometric Phase Half-Angle Rotation)
    needle_len = 52.0
    needle_mid_x = cx + COS_NEEDLES * R0
    needle_mid_y = cy + SIN_NEEDLES * R0

    dx = DX_NEEDLES * needle_len * 0.5
    dy = DY_NEEDLES * needle_len * 0.5

    pos_lines = np.column_stack([needle_mid_x, needle_mid_y, needle_mid_x + dx, needle_mid_y + dy]).astype(np.float32)
    neg_lines = np.column_stack([needle_mid_x, needle_mid_y, needle_mid_x - dx, needle_mid_y - dy]).astype(np.float32)

    # Positive arm (Crimson He-Ne)
    py5.stroke(244, 63, 94, 245)
    py5.stroke_weight(3.5)
    py5.lines(pos_lines)

    # Negative arm (Amber Caustic)
    py5.stroke(251, 191, 36, 245)
    py5.stroke_weight(3.5)
    py5.lines(neg_lines)

    # Center beads on needles
    py5.no_stroke()
    for mx, my in zip(needle_mid_x, needle_mid_y):
        py5.fill(255, 255, 255, 255)
        py5.circle(mx, my, 7.5)

    # 5. Caustic Cusps and Radial Spikes
    for k in range(4):
        cusp_angle = gamma * 2.0 + k * math.pi / 2.0
        u_cusp = cx + math.cos(cusp_angle) * (R_outer + 72.0)
        v_cusp = cy + math.sin(cusp_angle) * (R_outer + 72.0)
        py5.no_stroke()
        py5.fill(52, 211, 153, 230)
        py5.circle(u_cusp, v_cusp, 18.0)
        py5.fill(255, 255, 255, 255)
        py5.circle(u_cusp, v_cusp, 7.0)

    # 6. Four Corner Sleek Dark Optical Apparatuses
    def draw_telemetry_box(x, y, w, h, title, subtitle):
        py5.fill(12, 16, 24, 230)
        py5.stroke(30, 41, 59, 220)
        py5.stroke_weight(2.0)
        py5.rect(x, y, w, h, 10)
        
        py5.fill(241, 245, 249)
        py5.text_size(20)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.text(title, x + 24, y + 20)
        
        py5.fill(148, 163, 184)
        py5.text_size(16)
        py5.text(subtitle, x + 24, y + 48)

    # Top-Left: Biaxial Indicatrix
    draw_telemetry_box(100, 100, 440, 400, "BIAXIAL INDICATRIX", "nx=1.530 ny=1.681 nz=1.686 (ARAGONITE)")
    tl_cx, tl_cy = 320, 330
    py5.no_fill()
    py5.stroke(16, 185, 129, 200)
    py5.stroke_weight(2.5)
    py5.ellipse(tl_cx, tl_cy, 240, 150)
    py5.stroke(6, 182, 212, 200)
    py5.ellipse(tl_cx, tl_cy, 150, 240)
    # Optic axes intersection
    py5.stroke(244, 63, 94, 230)
    py5.stroke_weight(2.0)
    py5.line(tl_cx - 90, tl_cy - 90, tl_cx + 90, tl_cy + 90)
    py5.line(tl_cx - 90, tl_cy + 90, tl_cx + 90, tl_cy - 90)

    # Top-Right: Poincaré Polarization Sphere
    draw_telemetry_box(WIDTH - 540, 100, 440, 400, "POINCARÉ SPHERE", "BERRY GEOMETRIC PHASE: 2*PI")
    tr_cx, tr_cy = WIDTH - 320, 330
    py5.no_fill()
    py5.stroke(51, 65, 85)
    py5.stroke_weight(2.0)
    py5.circle(tr_cx, tr_cy, 220)
    py5.stroke(244, 63, 94, 200)
    py5.line(tr_cx - 110, tr_cy, tr_cx + 110, tr_cy)
    py5.line(tr_cx, tr_cy - 110, tr_cx, tr_cy + 110)
    s_ang = gamma * 2.0
    py5.fill(251, 191, 36)
    py5.no_stroke()
    py5.circle(tr_cx + math.cos(s_ang) * 96, tr_cy + math.sin(s_ang) * 96, 14)

    # Bottom-Left: Conical Beam Axial Profile
    draw_telemetry_box(100, HEIGHT - 500, 440, 400, "AXIAL BEAM PROFILE", "APEX DIABOLICAL CONE (Z = 0)")
    bl_cx, bl_cy = 320, HEIGHT - 290
    py5.no_fill()
    py5.stroke(16, 185, 129, 230)
    py5.stroke_weight(3.0)
    py5.line(bl_cx - 140, bl_cy - 90, bl_cx, bl_cy)
    py5.line(bl_cx + 140, bl_cy - 90, bl_cx, bl_cy)
    py5.line(bl_cx, bl_cy, bl_cx - 140, bl_cy + 90)
    py5.line(bl_cx, bl_cy, bl_cx + 140, bl_cy + 90)
    py5.fill(255, 255, 255)
    py5.no_stroke()
    py5.circle(bl_cx, bl_cy, 12)

    # Bottom-Right: Wollaston Analyzer Compass
    draw_telemetry_box(WIDTH - 540, HEIGHT - 500, 440, 400, "ANALYZER EXTINCTION", f"EXTINCTION ANGLE GAMMA = {math.degrees(gamma)%360:.1f}°")
    br_cx, br_cy = WIDTH - 320, HEIGHT - 290
    py5.no_fill()
    py5.stroke(51, 65, 85)
    py5.stroke_weight(2.0)
    py5.circle(br_cx, br_cy, 220)
    # Analyzer needle
    an_dx = math.cos(gamma) * 100
    an_dy = math.sin(gamma) * 100
    py5.stroke(251, 191, 36)
    py5.stroke_weight(4.5)
    py5.line(br_cx - an_dx, br_cy - an_dy, br_cx + an_dx, br_cy + an_dy)
    py5.fill(255, 255, 255)
    py5.no_stroke()
    py5.circle(br_cx, br_cy, 10)

    # 7. Monograph Archival Borders and Technical Typography
    py5.no_fill()
    py5.stroke(30, 41, 59)
    py5.stroke_weight(4.0)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke_weight(2.0)
    py5.rect(72, 72, WIDTH - 144, HEIGHT - 144)

    # Header
    py5.fill(148, 163, 184)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(24)
    py5.text("ROYAL IRISH ACADEMY — TRANSACTIONS VOL. XVII (1832)", WIDTH / 2.0, 96)
    py5.text_size(36)
    py5.fill(241, 245, 249)
    py5.text("HAMILTON CONICAL REFRACTION & DIABOLICAL POINT SINGULARITY", WIDTH / 2.0, 134)
    py5.text_size(22)
    py5.fill(16, 185, 129)
    py5.text("DUAL POGGENDORFF RINGS • BERRY GEOMETRIC PHASE • BIAXIAL ARAGONITE", WIDTH / 2.0, 182)

    # Footer
    py5.fill(148, 163, 184)
    py5.text_align(py5.CENTER, py5.BOTTOM)
    py5.text_size(20)
    py5.text("WAVE OPTICS CALIBRATION • COHERENT Nd:YAG (532 nm) & He-Ne (632.8 nm) • 4K GENERATIVE MICROSCOPY", WIDTH / 2.0, HEIGHT - 92)

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

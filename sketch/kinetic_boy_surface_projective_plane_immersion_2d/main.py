"""
Kinetic Werner Boy Surface Projective Plane Immersion 2D
4K 60fps 720 frames (12.0s seamless loop)

Autonomous Generative Media Art exploring Abstract Differential Topology,
the Real Projective Plane RP^2 immersion into R^3 without singularities,
formulated by Werner Boy (1901) under David Hilbert, via Robert Bryant and
Rob Kusner's conformal inversion parametrization, executed on warm ivory
mathematical drafting vellum (#f8f6f0).

The non-orientable surface features 3-fold rotational symmetry (C3), three
intersecting sheets crossing orthogonally at a central triple point (mu = 3),
two-tone Möbius winding coloration (Prussian blue #1a4473 and Venetian crimson #a82a3e),
amber asymptotic meridian loops, dynamic Gaussian curvature meters, and four
differential geometry apparatus cards in 12.0s topological harmonic resonance.
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
WORK_NAME = "kinetic_boy_surface_projective_plane_immersion_2d"
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
RND_ROT_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RND_PHASE_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))

# Projection Center and Scale (4K)
CX = WIDTH / 2.0
CY = HEIGHT / 2.0 + 70.0
SCALE_3D = 570.0
DIST_CAM = 4.2

# Precalculate Base Complex Mesh on Unit Disk
NUM_R = 38
NUM_TH = 114
R_ARR = np.linspace(0.02, 0.98, NUM_R)
TH_ARR = np.linspace(0.0, 2.0 * np.pi, NUM_TH, endpoint=False)
R_MESH, TH_MESH = np.meshgrid(R_ARR, TH_ARR)
Z_COMPLEX = R_MESH * np.exp(1j * TH_MESH)

# Bryant-Kusner Algebraic Inversion Formulation
DENOM = Z_COMPLEX**6 + np.sqrt(5.0) * Z_COMPLEX**3 - 1.0
F1 = -1.5 * np.imag(Z_COMPLEX * (1.0 - Z_COMPLEX**4) / DENOM)
F2 = -1.5 * np.real(Z_COMPLEX * (1.0 + Z_COMPLEX**4) / DENOM)
F3 = np.imag((1.0 + Z_COMPLEX**6) / DENOM) - 0.5
NORM_SQ = F1**2 + F2**2 + F3**2

# Static 3D Surface Coordinates (Centered at Origin)
X_BASE = F1 / NORM_SQ
Y_BASE = F2 / NORM_SQ
Z_BASE = (F3 / NORM_SQ) + 0.85 # Vertical centering along C3 axis

# Side factor for non-orientable two-tone coloration
SIDE_FACTOR = np.sin(TH_MESH * 1.5 + R_MESH * 2.5)

# Meron Particles circulating along surface coordinate lines
NUM_PARTICLES = 60
PARTICLE_INDICES = []
np.random.seed(int(time.time() * 1000) % 100000)
for _ in range(NUM_PARTICLES):
    p_i = int(np.random.randint(0, NUM_TH))
    p_j = int(np.random.randint(2, NUM_R - 2))
    p_speed = float(np.random.uniform(0.6, 1.4))
    PARTICLE_INDICES.append((p_i, p_j, p_speed))

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

    # 1. Warm Ivory Mathematical Drafting Vellum (#f8f6f0)
    py5.background(248, 246, 240)

    # 2. Archival Drafting Grid & Polar Projection Graticule
    py5.stroke(228, 222, 210, 130)
    py5.stroke_weight(1.5)
    for x in range(120, WIDTH, 120):
        py5.line(x, 80, x, HEIGHT - 80)
    for y in range(120, HEIGHT, 120):
        py5.line(80, y, WIDTH - 80, y)

    # Polar Graticule Rings centered at Projection Center
    py5.stroke(215, 208, 195, 110)
    py5.stroke_weight(2.0)
    py5.no_fill()
    for r_ring in [320, 640, 960]:
        py5.circle(CX, CY, r_ring * 2)

    # Rotating Projective Coordinate Scan Line
    scan_angle = omega * tau + RND_ROT_OFFSET
    py5.stroke(217, 119, 6, 45)
    py5.stroke_weight(2.0)
    py5.line(CX, CY, CX + 1020 * math.cos(scan_angle), CY + 1020 * math.sin(scan_angle))

    # 3. 3D Rotation Angles (Harmonic 12.0s Loop with 3-Fold C3 Invariance)
    rot_y = omega * tau + RND_ROT_OFFSET
    rot_x = 0.44 + 0.14 * math.sin(omega * tau)
    rot_z = 0.10 * math.cos(omega * tau)

    # Rotation matrix components
    cy_a, sy_a = math.cos(rot_y), math.sin(rot_y)
    cx_a, sx_a = math.cos(rot_x), math.sin(rot_x)
    cz_a, sz_a = math.cos(rot_z), math.sin(rot_z)

    # 1. Rotate about Y
    x1 = X_BASE * cy_a + Z_BASE * sy_a
    y1 = Y_BASE
    z1 = -X_BASE * sy_a + Z_BASE * cy_a

    # 2. Rotate about X
    x2 = x1
    y2 = y1 * cx_a - z1 * sx_a
    z2 = y1 * sx_a + z1 * cx_a

    # 3. Rotate about Z
    x3 = x2 * cz_a - y2 * sz_a
    y3 = x2 * sz_a + y2 * cz_a
    z3 = z2

    # Perspective factor
    fov_factor = DIST_CAM / (DIST_CAM + z3)
    proj_x = CX + x3 * SCALE_3D * fov_factor
    proj_y = CY + y3 * SCALE_3D * fov_factor

    # 4. Render Translucent Surface Mesh (Depth-Sorted Painter's Algorithm)
    quads = []
    for i in range(NUM_TH):
        i_next = (i + 1) % NUM_TH
        for j in range(NUM_R - 1):
            j_next = j + 1
            # Average depth of 4 vertices
            z_avg = (z3[i, j] + z3[i_next, j] + z3[i_next, j_next] + z3[i, j_next]) * 0.25
            quads.append((z_avg, i, j, i_next, j_next))

    # Sort descending: largest z3 (farthest from camera) rendered first
    quads.sort(key=lambda q: q[0], reverse=True)

    for z_avg, i, j, i_next, j_next in quads:
        # Two-tone non-orientable coloring: outside Prussian blue, inside Venetian crimson
        side = SIDE_FACTOR[i, j]
        if side > 0:
            base_r, base_g, base_b = 26, 68, 115 # Prussian blue
        else:
            base_r, base_g, base_b = 168, 42, 62 # Venetian crimson

        light_val = 0.52 + 0.42 * math.sin(x3[i, j] * 1.1 + y3[i, j] * 1.4)
        r_c = int(base_r * light_val)
        g_c = int(base_g * light_val)
        b_c = int(base_b * light_val)
        alpha_c = int(195 + 50 * (z_avg + 1.2) / 2.8)
        alpha_c = max(135, min(245, alpha_c))

        py5.fill(r_c, g_c, b_c, alpha_c)
        py5.stroke(18, 32, 50, 95)
        py5.stroke_weight(1.2)
        py5.begin_shape()
        py5.vertex(proj_x[i, j], proj_y[i, j])
        py5.vertex(proj_x[i_next, j], proj_y[i_next, j])
        py5.vertex(proj_x[i_next, j_next], proj_y[i_next, j_next])
        py5.vertex(proj_x[i, j_next], proj_y[i, j_next])
        py5.end_shape(py5.CLOSE)

    # 5. Coordinate Curve Filaments (Asymptotic Curves & Meron Fibers)
    py5.no_fill()
    # Circumferential rings (constant r)
    for j in range(0, NUM_R, 4):
        py5.stroke(217, 119, 6, 175) # Amber meridian
        py5.stroke_weight(2.4)
        py5.begin_shape()
        for i in range(NUM_TH):
            py5.vertex(proj_x[i, j], proj_y[i, j])
        py5.vertex(proj_x[0, j], proj_y[0, j])
        py5.end_shape()

    # Radial fibers (constant theta)
    for i in range(0, NUM_TH, 6):
        py5.stroke(20, 50, 85, 185) # Prussian blue fiber
        py5.stroke_weight(2.0)
        py5.begin_shape()
        for j in range(NUM_R):
            py5.vertex(proj_x[i, j], proj_y[i, j])
        py5.end_shape()

    # 6. Circulating Meron Coordinate Particles along Surface
    py5.no_stroke()
    for p_idx, (p_i, p_j, p_speed) in enumerate(PARTICLE_INDICES):
        t_phase = (tau * p_speed + p_idx / float(NUM_PARTICLES)) % 1.0
        cur_th_idx = int((p_i + t_phase * NUM_TH) % NUM_TH)
        cur_x = proj_x[cur_th_idx, p_j]
        cur_y = proj_y[cur_th_idx, p_j]
        cur_z = z3[cur_th_idx, p_j]

        # Draw particle if facing toward camera (depth attenuation)
        p_alpha = int(220 * max(0.2, (cur_z + 1.8) / 3.6))
        if p_idx % 2 == 0:
            py5.fill(217, 119, 6, p_alpha) # Amber spark
        else:
            py5.fill(234, 179, 8, p_alpha) # Gold spark
        py5.circle(cur_x, cur_y, 7.0)

    # 7. Central Triple Point Marker & Tangent Plane Triad
    tp_x = CX
    tp_y = CY + 48.0
    py5.stroke(190, 18, 60, 240)
    py5.stroke_weight(4.0)
    py5.line(tp_x - 56, tp_y, tp_x + 56, tp_y)
    py5.line(tp_x, tp_y - 48, tp_x, tp_y + 48)
    py5.fill(217, 119, 6, 230)
    py5.circle(tp_x, tp_y, 18.0)
    py5.fill(248, 246, 240)
    py5.circle(tp_x, tp_y, 6.0)

    # 8. Four-Corner Mathematical Apparatus Cards (Scaled for 4K)
    CARD_W = 460
    CARD_H = 430

    # Corner 1 (Top-Left): Weierstrass-Enneper Conformal Representation
    c1_x, c1_y = 350, 350
    py5.fill(242, 238, 228, 235)
    py5.stroke(70, 80, 95)
    py5.stroke_weight(2.5)
    py5.rect(c1_x - CARD_W/2, c1_y - CARD_H/2, CARD_W, CARD_H)

    py5.fill(160, 45, 65)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(20)
    py5.text("BRYANT-KUSNER CONVENTIONS", c1_x - CARD_W/2 + 28, c1_y - CARD_H/2 + 26)
    py5.fill(50, 60, 75)
    py5.text_size(17)
    py5.text("g(z) = z(1 - z^4) / (z^6 + sqrt(5) z^3 - 1)", c1_x - CARD_W/2 + 28, c1_y - CARD_H/2 + 64)
    py5.text("DEGREE: 6 (MEROMORPHIC GAUSS MAP)", c1_x - CARD_W/2 + 28, c1_y - CARD_H/2 + 98)
    py5.text("INVERSION: (f1, f2, f3) / ||f||^2", c1_x - CARD_W/2 + 28, c1_y - CARD_H/2 + 132)
    py5.text("ENERGY: WILLMORE MINIMAL W = 12 * PI", c1_x - CARD_W/2 + 28, c1_y - CARD_H/2 + 166)

    # Riemann Sphere Projection Diagram
    py5.stroke(30, 65, 105, 180)
    py5.stroke_weight(2.5)
    py5.no_fill()
    py5.circle(c1_x, c1_y + 80, 150)
    py5.stroke(217, 119, 6)
    py5.line(c1_x - 75, c1_y + 80, c1_x + 75, c1_y + 80)
    py5.line(c1_x, c1_y + 5, c1_x, c1_y + 155)
    # Orbiting polar marker
    orb_a = omega * tau * 2.0
    py5.fill(160, 45, 65)
    py5.circle(c1_x + 75 * math.cos(orb_a), c1_y + 80 + 75 * math.sin(orb_a), 12.0)

    # Corner 2 (Top-Right): Gauss-Bonnet Topological Invariant Card
    c2_x, c2_y = WIDTH - 350, 350
    py5.fill(242, 238, 228, 235)
    py5.stroke(70, 80, 95)
    py5.stroke_weight(2.5)
    py5.rect(c2_x - CARD_W/2, c2_y - CARD_H/2, CARD_W, CARD_H)

    py5.fill(160, 45, 65)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(20)
    py5.text("TOPOLOGICAL INVARIANTS", c2_x - CARD_W/2 + 28, c2_y - CARD_H/2 + 26)
    py5.fill(50, 60, 75)
    py5.text_size(17)
    py5.text("EULER CHAR: CHI(RP^2) = 1", c2_x - CARD_W/2 + 28, c2_y - CARD_H/2 + 64)
    py5.text("NON-ORIENTABLE: CROSS-CAP MODEL", c2_x - CARD_W/2 + 28, c2_y - CARD_H/2 + 98)
    py5.text("SYMMETRY: C3 (3-FOLD ROTATIONAL)", c2_x - CARD_W/2 + 28, c2_y - CARD_H/2 + 132)
    py5.text("SELF-INTERSECTION: 3 SEAMS", c2_x - CARD_W/2 + 28, c2_y - CARD_H/2 + 166)

    # Cross-Cap Self-Intersection Diagram
    py5.stroke(160, 45, 65, 200)
    py5.stroke_weight(3.0)
    py5.no_fill()
    py5.ellipse(c2_x, c2_y + 90, 150, 85)
    py5.line(c2_x - 45, c2_y + 70, c2_x + 45, c2_y + 110)
    py5.line(c2_x - 45, c2_y + 110, c2_x + 45, c2_y + 70)
    # Pulsing flux node
    flux_r = 10.0 + 4.0 * math.sin(omega * tau * 3.0)
    py5.fill(217, 119, 6)
    py5.circle(c2_x, c2_y + 90, flux_r)

    # Corner 3 (Bottom-Left): Triple Point Tangent Plane Triad
    c3_x, c3_y = 350, HEIGHT - 350
    py5.fill(242, 238, 228, 235)
    py5.stroke(70, 80, 95)
    py5.stroke_weight(2.5)
    py5.rect(c3_x - CARD_W/2, c3_y - CARD_H/2, CARD_W, CARD_H)

    py5.fill(160, 45, 65)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(20)
    py5.text("TRIPLE POINT TANGENT TRIAD", c3_x - CARD_W/2 + 28, c3_y - CARD_H/2 + 26)
    py5.fill(50, 60, 75)
    py5.text_size(17)
    py5.text("SHEETS CROSS AT 90 DEG (ORTHOGONAL)", c3_x - CARD_W/2 + 28, c3_y - CARD_H/2 + 64)
    py5.text("LOCAL MULTIPLICITY: mu = 3", c3_x - CARD_W/2 + 28, c3_y - CARD_H/2 + 98)
    py5.text("NO BRANCH POINT / SMOOTH IMMERSION", c3_x - CARD_W/2 + 28, c3_y - CARD_H/2 + 132)
    py5.text("TANGENT VECTORS: T1 perp T2 perp T3", c3_x - CARD_W/2 + 28, c3_y - CARD_H/2 + 166)

    # 3D Orthogonal Triad Axes (Rotating with Surface Frame)
    triad_rot = rot_y
    tx1, ty1 = 70.0 * math.cos(triad_rot), 35.0 * math.sin(triad_rot)
    tx2, ty2 = 70.0 * math.cos(triad_rot + 2.094), 35.0 * math.sin(triad_rot + 2.094)
    tx3, ty3 = 70.0 * math.cos(triad_rot + 4.188), 35.0 * math.sin(triad_rot + 4.188)

    py5.stroke(30, 65, 105, 240)
    py5.stroke_weight(3.5)
    py5.line(c3_x, c3_y + 85, c3_x + tx1, c3_y + 85 + ty1)
    py5.stroke(160, 45, 65, 240)
    py5.line(c3_x, c3_y + 85, c3_x + tx2, c3_y + 85 + ty2)
    py5.stroke(217, 119, 6, 240)
    py5.line(c3_x, c3_y + 85, c3_x + tx3, c3_y + 85 + ty3)
    py5.fill(50, 60, 75)
    py5.circle(c3_x, c3_y + 85, 10.0)

    # Corner 4 (Bottom-Right): Principal Curvature Tensor Spectrum
    c4_x, c4_y = WIDTH - 350, HEIGHT - 350
    py5.fill(242, 238, 228, 235)
    py5.stroke(70, 80, 95)
    py5.stroke_weight(2.5)
    py5.rect(c4_x - CARD_W/2, c4_y - CARD_H/2, CARD_W, CARD_H)

    py5.fill(160, 45, 65)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text_size(20)
    py5.text("GAUSSIAN CURVATURE K", c4_x - CARD_W/2 + 28, c4_y - CARD_H/2 + 26)
    py5.fill(50, 60, 75)
    py5.text_size(17)
    py5.text("TOTAL CURVATURE: 2 * PI", c4_x - CARD_W/2 + 28, c4_y - CARD_H/2 + 64)
    k_max_val = 3.84 + 0.52 * math.sin(omega * tau)
    k_min_val = -2.12 - 0.35 * math.cos(omega * tau)
    py5.text(f"K_MAX: {k_max_val:.2f}", c4_x - CARD_W/2 + 28, c4_y - CARD_H/2 + 98)
    py5.text(f"K_MIN: {k_min_val:.2f}", c4_x - CARD_W/2 + 28, c4_y - CARD_H/2 + 132)
    py5.text("PARABOLIC CURVES: K = 0 (INFLECTION)", c4_x - CARD_W/2 + 28, c4_y - CARD_H/2 + 166)

    # Curvature Spectrum Gradient Bar & Needle
    py5.no_stroke()
    spec_w = 260
    spec_h = 36
    spec_ox = c4_x - spec_w / 2
    spec_oy = c4_y + 70
    for bx in range(spec_w):
        t_b = bx / float(spec_w)
        py5.fill(int(26 * (1 - t_b) + 168 * t_b), int(68 * (1 - t_b) + 42 * t_b), int(115 * (1 - t_b) + 62 * t_b))
        py5.rect(spec_ox + bx, spec_oy, 2, spec_h)

    # Dynamic needle indicator
    needle_x = spec_ox + spec_w * (0.5 + 0.38 * math.sin(omega * tau))
    py5.stroke(217, 119, 6)
    py5.stroke_weight(3.5)
    py5.line(needle_x, spec_oy - 8, needle_x, spec_oy + spec_h + 8)

    # 9. Archival Mathematical Vellum Outer Borders & Title
    py5.no_fill()
    py5.stroke(65, 75, 90)
    py5.stroke_weight(3.5)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120)
    py5.stroke(180, 140, 85, 170) # Antique gold inner border
    py5.stroke_weight(1.8)
    py5.rect(72, 72, WIDTH - 144, HEIGHT - 144)

    # Header Title
    py5.fill(35, 45, 60)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text_size(24)
    py5.text("DIFFERENTIAL TOPOLOGY - NON-ORIENTABLE IMMERSION OF REAL PROJECTIVE PLANE", WIDTH / 2.0, 96)
    py5.text_size(38)
    py5.text("WERNER BOY - BOY'S SURFACE (RP^2) TOPOLOGICAL IMMERSION", WIDTH / 2.0, 136)
    py5.text_size(22)
    py5.fill(160, 45, 65)
    py5.text("BRYANT-KUSNER PARAMETRIZATION - 3-FOLD ROTATIONAL SYMMETRY - TRIPLE POINT SINGULARITY", WIDTH / 2.0, 186)

    # Bottom Telemetry
    py5.fill(70, 80, 95)
    py5.text_align(py5.LEFT, py5.BOTTOM)
    py5.text_size(22)
    py5.text("WERNER BOY (1901) - DAVID HILBERT - OBERWOLFACH MATHEMATICAL EMBLEM - EULER CHAR CHI = 1", 108, HEIGHT - 92)
    py5.text_align(py5.RIGHT, py5.BOTTOM)
    py5.text("4K GENERATIVE MEDIA ART - 12.0s TOPOLOGICAL HARMONIC CYCLE", WIDTH - 108, HEIGHT - 92)

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

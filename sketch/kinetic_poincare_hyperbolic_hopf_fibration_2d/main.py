"""
kinetic_poincare_hyperbolic_hopf_fibration_2d
Autonomous Generative py5 Media Art Animation (720 frames @ 60 FPS, 12.0s seamless loop, 4K Master)

Genre: Mathematical / Abstract Topology
Theme: Non-Euclidean Poincaré disk hyperbolic geometry, conformal Möbius transformations,
       and 4D Clifford-Hopf fibration Villarceau circle bundles projected onto
       tactile antique mathematician drafting vellum.

Anti-Clustering & Diversity Compliance:
- Genre: Mathematical / Abstract Topology (Rotates away from Organic/Morphogenesis, Signal/Glitch, Atmospheric/Painterly)
- Background: Warm antique drafting vellum (#f6f2e8, high-luminance ground L ≈ 94%), inverting recent dark backgrounds
- Primitives: Non-Euclidean circular geodesics, horocycle families, Villarceau torus circle bundles,
  Apollonian coordinate pencil nets, and technical compass calibration ticks. Zero particles or point clouds.
- Strict Anonymity: Zero signatures, zero seals/hanko, zero monograms, zero initials, zero author marks.
- Palette: Drafting vellum ground (#f6f2e8), Prussian slate blue (#1c3e66), copper sepia (#944c2a),
  sage drafting ink (#3d5a45), deep boundary ink (#1e2530), and chalk ivory (#ffffff).
"""

import os
import shutil
import subprocess
import numpy as np
import py5

# Work identification
WORK_NAME = "kinetic_poincare_hyperbolic_hopf_fibration_2d"
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
R_DISK = 940.0

# Pre-computed angular arrays for vectorized curve rendering
N_CIRCLE_PTS = 720
THETAS = np.linspace(0.0, 2.0 * np.pi, N_CIRCLE_PTS, endpoint=False)
COS_T, SIN_T = np.cos(THETAS), np.sin(THETAS)

# Hopf fibration Villarceau fibers
N_FIBERS = 84
N_FIBER_PTS = 360
TH_FIBER = np.linspace(0.0, 2.0 * np.pi, N_FIBER_PTS, endpoint=False)
COS_F, SIN_F = np.cos(TH_FIBER), np.sin(TH_FIBER)


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

    # 1. Warm Antique Mathematician Drafting Vellum Ground (#f6f2e8)
    py5.background(246, 242, 232)

    # 2. Fine Geometric Drafting Coordinate Grid
    py5.stroke(222, 216, 202, 60)
    py5.stroke_weight(1.0)
    for gx in range(0, WIDTH, 120):
        py5.line(gx, 0, gx, HEIGHT)
    for gy in range(0, HEIGHT, 120):
        py5.line(0, gy, WIDTH, gy)

    # Diagonal drafting isometric guide lines
    py5.stroke(226, 220, 206, 45)
    for d_off in range(-HEIGHT, WIDTH + HEIGHT, 240):
        py5.line(d_off, 0, d_off + HEIGHT, HEIGHT)

    # 3. Dynamic Apollonian Pencil of Coaxial Circles (Orthogonal Net)
    # Pole positions precessing harmonically
    pole_dist = 680.0 * (1.0 + 0.12 * np.cos(tau))
    p1_x = CX + pole_dist * np.cos(tau * 0.5)
    p1_y = CY + pole_dist * np.sin(tau * 0.5)
    p2_x = CX - pole_dist * np.cos(tau * 0.5)
    p2_y = CY - pole_dist * np.sin(tau * 0.5)

    py5.no_fill()
    n_apollonian = 36
    for k in range(1, n_apollonian + 1):
        frac_k = k / n_apollonian
        # Coaxial circle radius and center offset
        lambda_val = np.tan(frac_k * np.pi * 0.48)
        r_apol = pole_dist / (2.0 * max(0.01, np.abs(np.sinh(lambda_val * 0.5))))
        if r_apol < 2800.0:
            c_apol_x = CX + pole_dist * 0.5 * (1.0 / np.tanh(lambda_val * 0.5)) * np.cos(tau * 0.5)
            c_apol_y = CY + pole_dist * 0.5 * (1.0 / np.tanh(lambda_val * 0.5)) * np.sin(tau * 0.5)

            py5.stroke(61, 90, 69, int(15 + 45 * np.sin(frac_k * np.pi)))
            py5.stroke_weight(1.2)
            py5.ellipse(c_apol_x, c_apol_y, r_apol * 2.0, r_apol * 2.0)

    # 4. Family of Conformal Hyperbolic Geodesics (Orthogonal to Poincaré Boundary Circle)
    n_geodesics = 72
    for a in range(n_geodesics):
        frac_a = a / n_geodesics
        ang = frac_a * 2.0 * np.pi + tau * 0.25
        # Orthogonal circle parameters via Pythagorean theorem d^2 = R^2 + r^2
        d = R_DISK * (1.18 + 0.82 * np.cos(tau + frac_a * np.pi * 2.0))
        r_arc = np.sqrt(max(10.0, d * d - R_DISK * R_DISK))
        c_arc_x = CX + d * np.cos(ang)
        c_arc_y = CY + d * np.sin(ang)

        # Alternating Prussian blue and Copper sepia inks
        if a % 2 == 0:
            py5.stroke(28, 62, 102, int(45 + 95 * (1.0 - (d - R_DISK) / (1.5 * R_DISK))))
            py5.stroke_weight(1.8)
        else:
            py5.stroke(148, 76, 42, int(40 + 85 * (1.0 - (d - R_DISK) / (1.5 * R_DISK))))
            py5.stroke_weight(1.6)

        py5.ellipse(c_arc_x, c_arc_y, r_arc * 2.0, r_arc * 2.0)

    # 5. Concentric Poincaré Horocycles (Hyperbolic Circles tangent to boundary)
    n_horo = 18
    for h in range(1, n_horo + 1):
        frac_h = h / n_horo
        r_horo = R_DISK * (0.15 + 0.80 * np.power(frac_h, 1.4))
        # Breathing horocycle centers along precessing axis
        h_ang = tau + frac_h * np.pi * 0.5
        h_cx = CX + (R_DISK - r_horo) * np.cos(h_ang) * 0.45
        h_cy = CY + (R_DISK - r_horo) * np.sin(h_ang) * 0.45

        py5.stroke(28, 62, 102, int(25 + 55 * frac_h))
        py5.stroke_weight(1.3)
        py5.ellipse(h_cx, h_cy, r_horo * 2.0, r_horo * 2.0)

    # 6. Stereographic 4D Clifford-Hopf Fibration Villarceau Circles
    # S^3 -> S^2 Hopf fiber bundle projection onto Clifford torus
    for f in range(N_FIBERS):
        frac_f = f / N_FIBERS
        phi = frac_f * 2.0 * np.pi + tau

        # Breathing major and minor radii of the projected Clifford Torus
        r_torus = 590.0 * (1.0 + 0.16 * np.sin(tau * 2.0 + frac_f * 4.0))
        h_torus = 350.0 * (1.0 + 0.16 * np.cos(tau * 2.0 + frac_f * 4.0))

        # Villarceau diagonal cut trajectory
        v_x = CX + r_torus * COS_F * np.cos(phi) - h_torus * SIN_F * np.sin(phi)
        v_y = CY + r_torus * COS_F * np.sin(phi) + h_torus * SIN_F * np.cos(phi)
        v_pts = np.column_stack([v_x, v_y])

        # Dual-layer stroke for copper/prussian ink wash
        py5.stroke(28, 62, 102, int(40 + 130 * np.sin(frac_f * np.pi)))
        py5.stroke_weight(1.8)
        py5.begin_shape()
        py5.vertices(v_pts)
        py5.end_shape(py5.CLOSE)

        # Counter-chiral Villarceau fiber
        v2_x = CX + r_torus * COS_F * np.cos(-phi) + h_torus * SIN_F * np.sin(-phi)
        v2_y = CY + r_torus * COS_F * np.sin(-phi) - h_torus * SIN_F * np.cos(-phi)
        v2_pts = np.column_stack([v2_x, v2_y])

        py5.stroke(148, 76, 42, int(35 + 115 * np.sin(frac_f * np.pi)))
        py5.stroke_weight(1.4)
        py5.begin_shape()
        py5.vertices(v2_pts)
        py5.end_shape(py5.CLOSE)

    # 7. Non-Euclidean Poincaré Disk Conformal Boundary Circle (S^1 at Infinity)
    py5.no_fill()
    py5.stroke(30, 37, 48, 240)
    py5.stroke_weight(5.5)
    py5.ellipse(CX, CY, R_DISK * 2.0, R_DISK * 2.0)

    # Inner boundary parchment bevel
    py5.stroke(148, 76, 42, 120)
    py5.stroke_weight(1.8)
    py5.ellipse(CX, CY, (R_DISK - 8.0) * 2.0, (R_DISK - 8.0) * 2.0)

    # Outer compass boundary track
    py5.stroke(28, 62, 102, 110)
    py5.stroke_weight(1.5)
    py5.ellipse(CX, CY, (R_DISK + 18.0) * 2.0, (R_DISK + 18.0) * 2.0)

    # 8. Compass Calibration Radian Ticks along Disk Perimeter
    py5.stroke(30, 37, 48, 160)
    py5.stroke_weight(1.6)
    n_ticks = 360
    for tick in range(n_ticks):
        t_ang = tick * (2.0 * np.pi / n_ticks)
        tick_len = 16.0 if tick % 30 == 0 else (10.0 if tick % 10 == 0 else 5.0)
        cos_a, sin_a = np.cos(t_ang), np.sin(t_ang)
        x_in = CX + (R_DISK + 18.0) * cos_a
        y_in = CY + (R_DISK + 18.0) * sin_a
        x_out = CX + (R_DISK + 18.0 + tick_len) * cos_a
        y_out = CY + (R_DISK + 18.0 + tick_len) * sin_a
        py5.line(x_in, y_in, x_out, y_out)

    # Radial cardinal crosshairs
    py5.stroke(30, 37, 48, 190)
    py5.stroke_weight(1.8)
    for ang in [0, np.pi * 0.5, np.pi, np.pi * 1.5]:
        ca, sa = np.cos(ang), np.sin(ang)
        py5.line(CX + (R_DISK + 18.0) * ca, CY + (R_DISK + 18.0) * sa, CX + (R_DISK + 55.0) * ca, CY + (R_DISK + 55.0) * sa)

    # 9. Frame output & progress tracking
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Capture preview image at frame 180 (quarter-cycle peak phase)
    if frame == PREVIEW_FRAME:
        shutil.copy(frame_path, PREVIEW_PATH)
        print(f"[Preview Saved] Poincaré topology preview captured: {PREVIEW_PATH}")

    # Progress reporting
    if frame % 60 == 0 or frame == TOTAL_FRAMES:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")

    # 10. Finalize animation on reaching total frame count
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

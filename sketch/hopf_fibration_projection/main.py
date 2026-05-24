"""
hopf_fibration_projection
=========================
Parametric 4D generation of Hopf circles projected via Stereographic 
projection from S3 to R3, and then to 2D. Rendered as luminous, silken threads.

Uses pure numpy arrays for the mathematical projection and py5 for rendering
with additive blending to create an iridescent 3D optical illusion.
"""

from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

# ── constants ───────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS           # 900
PREVIEW_FRAME = 450                         # Mid-point where the torus is inside out
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Fiber structure parameters
N_RINGS = 400
N_POINTS = 600

# Base parameters on S3
_x1 = None
_x2 = None
_x3 = None
_x4 = None
_theta_sph = None
_phi_sph = None


def setup_geometry():
    global _x1, _x2, _x3, _x4, _theta_sph, _phi_sph
    
    golden_ratio = (1 + 5**0.5) / 2
    indices = np.arange(N_RINGS, dtype=np.float32)
    z = 1 - (indices / float(N_RINGS - 1)) * 2
    
    _theta_sph = np.arccos(z)
    _phi_sph = (2 * np.pi * indices / golden_ratio) % (2 * np.pi)

    psi = np.linspace(0, 2 * np.pi, N_POINTS, dtype=np.float32)

    THETA = _theta_sph[:, None]
    PHI = _phi_sph[:, None]
    PSI = psi[None, :]

    _x1 = np.cos(PSI) * np.sin(THETA / 2)
    _x2 = np.sin(PSI) * np.sin(THETA / 2)
    _x3 = np.cos(PSI + PHI) * np.cos(THETA / 2)
    _x4 = np.sin(PSI + PHI) * np.cos(THETA / 2)


def setup():
    # Use default 2D renderer for absolute reliability, since we manually project 3D->2D
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    setup_geometry()
    print(f"[{WORK_NAME}] Setup OK  canvas={SIZE[0]}x{SIZE[1]}")


def draw():
    fc = py5.frame_count
    t = (fc / TOTAL_FRAMES) * 2 * np.pi
    
    # Very dark void
    py5.background(2, 0, 5)
    
    # 4D Rotations (Isoclinic-like rotation to turn the fibration inside out)
    alpha = t
    x1_r = np.cos(alpha) * _x1 - np.sin(alpha) * _x4
    x4_r = np.sin(alpha) * _x1 + np.cos(alpha) * _x4
    x2_r = _x2
    x3_r = _x3
    
    beta = t * 2.0
    x2_rr = np.cos(beta) * x2_r - np.sin(beta) * x3_r
    x3_rr = np.sin(beta) * x2_r + np.cos(beta) * x3_r
    x1_rr = x1_r
    x4_rr = x4_r
    
    # Stereographic projection from S3 to R3
    denom = 1.0 - x4_rr
    # Prevent singularities (infinity lines)
    denom = np.where(np.abs(denom) < 0.001, 0.001 * np.sign(denom), denom)
    r = 1.0 / denom
    
    X = x1_rr * r
    Y = x2_rr * r
    Z = x3_rr * r
    
    # 3D Camera Orbit
    cam_angle = t * 1.5
    X_rot = np.cos(cam_angle) * X - np.sin(cam_angle) * Z
    Z_rot = np.sin(cam_angle) * X + np.cos(cam_angle) * Z
    Y_rot = Y
    
    # Camera Tilt
    tilt = 0.6
    Y_tilt = np.cos(tilt) * Y_rot - np.sin(tilt) * Z_rot
    Z_tilt = np.sin(tilt) * Y_rot + np.cos(tilt) * Z_rot
    
    # 2D projection
    Z_cam = Z_tilt + 4.5
    # Avoid objects clipping behind the camera
    Z_cam = np.where(Z_cam < 0.1, 0.1, Z_cam)
    scale = SIZE[1] * 0.9  # Scale relative to height
    
    X_2D = (X_rot / Z_cam) * scale + SIZE[0] / 2
    Y_2D = (Y_tilt / Z_cam) * scale + SIZE[1] / 2
    
    # Clip coordinates to prevent Java2D huge line rendering crashes
    X_2D = np.clip(X_2D, -20000, 20000)
    Y_2D = np.clip(Y_2D, -20000, 20000)
    
    # ── Rendering ──────────────────────────────────────────────────────────
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 255)
    py5.no_fill()
    py5.stroke_weight(1.0)
    
    for i in range(N_RINGS):
        # Base hue on S2 phi and animate over time
        hue = ((_phi_sph[i] / (2 * np.pi)) * 255 + (t / (2 * np.pi)) * 255) % 255
        sat = 200 + 55 * np.sin(_theta_sph[i])
        bri = 255
        alpha_val = 35
        
        py5.stroke(hue, sat, bri, alpha_val)
        
        pts = np.column_stack((X_2D[i], Y_2D[i]))
        py5.begin_shape()
        py5.vertices(pts)
        py5.end_shape(py5.CLOSE)

    # ── Lifecycle ──────────────────────────────────────────────────────────
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % FPS == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc == PREVIEW_FRAME:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))
        print(f"[Preview] Saved {PREVIEW_FILENAME}")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a backup snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()

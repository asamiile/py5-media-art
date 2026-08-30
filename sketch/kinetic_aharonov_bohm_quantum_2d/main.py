"""
kinetic_aharonov_bohm_quantum_2d

A 4K kinetic visualization of the Aharonov-Bohm effect: solving the 2D Time-Dependent
Schrödinger Equation (TDSE) using a covariant lattice gauge formulation.
Visualizes phase shifts and topological wave scattering around a shielded magnetic flux tube.
"""
import struct
from pathlib import Path
import shutil
import subprocess
import sys
import math
import numpy as np

import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840x2160

# --- Grid Configuration ---
SIM_W, SIM_H = 320, 180  # Grid size

# --- Physical Parameters ---
DT = 0.15             # Staggered leapfrog time step (stable for DT < 0.5)
FLUX_STRENGTH = 12.0  # Topological vector potential scaling (Aharonov-Bohm flux)

# --- State Fields ---
R = np.zeros((SIM_H, SIM_W), dtype=np.float32)  # Real part of Wave Function
I = np.zeros((SIM_H, SIM_W), dtype=np.float32)  # Imaginary part of Wave Function

# Coordinate grids
Y_idx, X_idx = np.indices((SIM_H, SIM_W), dtype=np.float32)
CX = SIM_W // 2
CY = SIM_H // 2

# --- Vector Potential A (Aharonov-Bohm Field on Yee-like link coordinates) ---
Ax = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Ay = np.zeros((SIM_H, SIM_W), dtype=np.float32)

SHIELD_R = 15.0

# Ax defined on link (x -> x+1)
dx_x = X_idx + 0.5 - CX
dy_x = Y_idx - CY
r2_x = dx_x**2 + dy_x**2
r2_x[r2_x < 1.0] = 1.0
mask_x = r2_x > SHIELD_R**2
Ax[mask_x] = -FLUX_STRENGTH * dy_x[mask_x] / r2_x[mask_x]

# Ay defined on link (y -> y+1)
dx_y = X_idx - CX
dy_y = Y_idx + 0.5 - CY
r2_y = dx_y**2 + dy_y**2
r2_y[r2_y < 1.0] = 1.0
mask_y = r2_y > SHIELD_R**2
Ay[mask_y] = FLUX_STRENGTH * dx_y[mask_y] / r2_y[mask_y]

# --- Impenetrable Shield Mask (PEC-like cylinder where psi = 0) ---
dx_c = X_idx - CX
dy_c = Y_idx - CY
r2_c = dx_c**2 + dy_c**2
barrier_mask = r2_c <= SHIELD_R**2

# --- Wave Packet Initialization ---
# Spawn a Gaussian wave packet on the left moving right
X0 = 60.0
Y0 = CY
SIGMA = 18.0
K_X = 0.7  # Wave number

dist_init = (X_idx - X0)**2 + (Y_idx - Y0)**2
envelope = np.exp(-dist_init / (2.0 * SIGMA**2))
R[:] = envelope * np.cos(K_X * X_idx)
I[:] = envelope * np.sin(K_X * X_idx)

# Zero out wave function inside the tube initially
R[barrier_mask] = 0.0
I[barrier_mask] = 0.0

# --- Boundary Absorber (Sponge layer to prevent boundary reflections) ---
absorber = np.ones((SIM_H, SIM_W), dtype=np.float32)
BORDER = 25
for b in range(BORDER):
    factor = 0.88 + 0.12 * (b / BORDER) ** 2  # Damping curve
    absorber[b, :] = np.minimum(absorber[b, :], factor)
    absorber[-1 - b, :] = np.minimum(absorber[-1 - b, :], factor)
    absorber[:, b] = np.minimum(absorber[:, b], factor)
    absorber[:, -1 - b] = np.minimum(absorber[:, -1 - b], factor)

# Trail Buffer (float32)
trail_buf = None
pimg = None


def setup():
    global trail_buf, pimg

    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    # Base trail buffer (Obsidian Void)
    trail_buf = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    trail_buf[:, :, :] = np.array([2, 3, 6], dtype=np.float32)

    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)


def step_quantum():
    """Leapfrog integration of 2D TDSE using covariant gauge link variables."""
    global R, I

    # Perform 3 physics steps per frame for smooth wave animation
    for _ in range(3):
        # 1. Compute lap_I (Covariant Laplacian of Imaginary part I)
        cos_Ax = np.cos(Ax[1:-1, 1:-1])
        sin_Ax = np.sin(Ax[1:-1, 1:-1])
        cos_Ax_l = np.cos(Ax[1:-1, :-2])
        sin_Ax_l = np.sin(Ax[1:-1, :-2])
        
        cos_Ay = np.cos(Ay[1:-1, 1:-1])
        sin_Ay = np.sin(Ay[1:-1, 1:-1])
        cos_Ay_b = np.cos(Ay[:-2, 1:-1])
        sin_Ay_b = np.sin(Ay[:-2, 1:-1])
        
        lap_I = (
            (I[1:-1, 2:] * cos_Ax - R[1:-1, 2:] * sin_Ax) +
            (I[1:-1, :-2] * cos_Ax_l + R[1:-1, :-2] * sin_Ax_l) +
            (I[2:, 1:-1] * cos_Ay - R[2:, 1:-1] * sin_Ay) +
            (I[:-2, 1:-1] * cos_Ay_b + R[:-2, 1:-1] * sin_Ay_b) -
            4.0 * I[1:-1, 1:-1]
        )
        
        # Update R
        R[1:-1, 1:-1] += DT * (-0.5 * lap_I)
        R[barrier_mask] = 0.0
        R *= absorber

        # 2. Compute lap_R (Covariant Laplacian of Real part R)
        lap_R = (
            (R[1:-1, 2:] * cos_Ax + I[1:-1, 2:] * sin_Ax) +
            (R[1:-1, :-2] * cos_Ax_l - I[1:-1, :-2] * sin_Ax_l) +
            (R[2:, 1:-1] * cos_Ay + I[2:, 1:-1] * sin_Ay) +
            (R[:-2, 1:-1] * cos_Ay_b - I[:-2, 1:-1] * sin_Ay_b) -
            4.0 * R[1:-1, 1:-1]
        )
        
        # Update I
        I[1:-1, 1:-1] += DT * (0.5 * lap_R)
        I[barrier_mask] = 0.0
        I *= absorber


def phase_to_rgb(phase, amp):
    """Map quantum phase angle to HSL spectrum, modulated by amplitude."""
    # Convert phase from [-pi, pi] to [0, 1]
    t = (phase + np.pi) / (2.0 * np.pi)
    
    # Map to RGB spectral wheel
    r = 0.5 + 0.5 * np.cos(2.0 * np.pi * t)
    g = 0.5 + 0.5 * np.cos(2.0 * np.pi * (t - 0.333))
    b = 0.5 + 0.5 * np.cos(2.0 * np.pi * (t - 0.666))
    
    return r * amp, g * amp, b * amp


def draw():
    global trail_buf

    fc = py5.frame_count
    t = fc / TOTAL_FRAMES

    # --- Physics Step ---
    step_quantum()

    # --- Render Fields ---
    density = R**2 + I**2
    phase = np.arctan2(I, R)

    # Gamma-compressed amplitude for highlighting faint fringes
    amp = np.clip(np.sqrt(density) * 220.0, 0, 255)
    
    # Base trail decay
    trail_buf *= 0.82
    trail_buf[:, :, 0] = np.maximum(trail_buf[:, :, 0], 2)
    trail_buf[:, :, 1] = np.maximum(trail_buf[:, :, 1], 3)
    trail_buf[:, :, 2] = np.maximum(trail_buf[:, :, 2], 6)

    # Calculate RGB from phase and amplitude
    r_phase, g_phase, b_phase = phase_to_rgb(phase, amp)

    # Draw quantum field to trail buffer
    trail_buf[:, :, 0] += r_phase
    trail_buf[:, :, 1] += g_phase
    trail_buf[:, :, 2] += b_phase

    # Draw the vector potential field A lines (circular paths)
    for ring_r in [30, 50, 75, 105]:
        mask_ring = np.abs(np.sqrt(r2_c) - ring_r) < 0.8
        trail_buf[mask_ring, 0] = 0.85 * trail_buf[mask_ring, 0] + 0.15 * 50
        trail_buf[mask_ring, 1] = 0.85 * trail_buf[mask_ring, 1] + 0.15 * 90
        trail_buf[mask_ring, 2] = 0.85 * trail_buf[mask_ring, 2] + 0.15 * 180

    # Draw the impenetrable central core (shielded cylinder)
    trail_buf[barrier_mask, 0] = 0.9 * trail_buf[barrier_mask, 0] + 0.1 * 12
    trail_buf[barrier_mask, 1] = 0.9 * trail_buf[barrier_mask, 1] + 0.1 * 12
    trail_buf[barrier_mask, 2] = 0.9 * trail_buf[barrier_mask, 2] + 0.1 * 25

    # Central core outline glow
    core_outline = np.abs(np.sqrt(r2_c) - SHIELD_R) < 1.0
    trail_buf[core_outline, 0] = 0.8 * trail_buf[core_outline, 0] + 0.2 * 255
    trail_buf[core_outline, 1] = 0.8 * trail_buf[core_outline, 1] + 0.2 * 60
    trail_buf[core_outline, 2] = 0.8 * trail_buf[core_outline, 2] + 0.2 * 120

    # --- Convert trail buffer to ARGB pixels ---
    buf_clamped = np.clip(trail_buf, 0, 255).astype(np.uint8)
    argb = (
        (np.int32(255) << 24)
        | (buf_clamped[:, :, 0].astype(np.int32) << 16)
        | (buf_clamped[:, :, 1].astype(np.int32) << 8)
        | buf_clamped[:, :, 2].astype(np.int32)
    )
    argb_signed = argb.view(np.int32)

    pimg.load_pixels()
    pimg.pixels[:] = argb_signed.flatten()
    pimg.update_pixels()

    # --- Blit to 4K canvas ---
    py5.background(2, 3, 6)
    py5.image(pimg, 0, 0, py5.width, py5.height)

    # --- HUD Overlay ---
    scale_x = py5.width / SIM_W
    ts = int(10 * scale_x)
    py5.no_stroke()

    # Telemetry Panel
    panel_w = int(280 * scale_x)
    panel_h = int(105 * scale_x)
    py5.fill(1, 1, 4, 210)
    py5.rect(0, 0, panel_w, panel_h, 0, 0, 8, 0)

    # Title
    py5.fill(235, 120, 240)
    py5.text_size(ts)
    py5.text("AHARONOV-BOHM EFFECT // 2D TDSE", int(12 * scale_x), int(20 * scale_x))

    # Stats
    py5.text_size(int(7.5 * scale_x))
    py5.fill(160, 175, 200)
    py5.text(f"Grid size:     {SIM_W} x {SIM_H}", int(12 * scale_x), int(38 * scale_x))
    py5.text(f"Time (t):      {fc/FPS:.2f}s / {DURATION_SEC:.1f}s", int(12 * scale_x), int(53 * scale_x))
    py5.text(f"AB Flux (Φ):   {FLUX_STRENGTH:.1f} (Topological)", int(12 * scale_x), int(68 * scale_x))
    py5.text(f"Phase Angle:   Spectral Hue [-π, π]", int(12 * scale_x), int(83 * scale_x))

    # Probability density conservation bar
    prob_total = float(np.sum(density))
    bar_x = int(12 * scale_x)
    bar_y = int(92 * scale_x)
    bar_w = int(256 * scale_x)
    bar_h = int(5 * scale_x)
    py5.fill(10, 10, 20)
    py5.rect(bar_x, bar_y, bar_w, bar_h, 2)
    
    # Scale conservation relative to initial probability
    fill_ratio = np.clip(prob_total / 2470.0, 0.0, 1.0)
    py5.fill(220, 60, 240)
    py5.rect(bar_x, bar_y, int(bar_w * fill_ratio), bar_h, 2)

    # Progress bar at bottom
    py5.fill(5, 5, 12)
    py5.rect(0, py5.height - int(4 * scale_x), py5.width, int(4 * scale_x))
    py5.fill(210, 60, 235)
    py5.rect(0, py5.height - int(4 * scale_x), int(py5.width * t), int(4 * scale_x))

    # Watermark
    py5.fill(130, 120, 160, 80)
    py5.text_size(int(7 * scale_x))
    py5.text(WORK_NAME.upper(), int(12 * scale_x), py5.height - int(10 * scale_x))

    # Fail-safe: abort on blank screen
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | Probability Sum = {prob_total:.2f}")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "slow",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)

        # Save a preview snapshot at mid-point
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")

        import os
        os._exit(0)


py5.run_sketch()

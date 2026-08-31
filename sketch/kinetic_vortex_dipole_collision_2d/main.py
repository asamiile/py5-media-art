"""
kinetic_vortex_dipole_collision_2d

A 4K kinetic visualization of fluid dynamics: solving the 2D Navier-Stokes equations
in the Vorticity-Stream Function formulation to model the symmetric collision,
reconnection, and splitting of two counter-rotating vortex dipoles.
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
SIM_W, SIM_H = 320, 180  # Grid size (keep small for fast real-time Jacobi solver)

# --- Physical Parameters ---
DT = 1.0         # Time step for advection
VISCOSITY = 0.08 # Viscosity (diffusion coefficient for vorticity stabilization)

# --- State Fields ---
vorticity = np.zeros((SIM_H, SIM_W), dtype=np.float32)
psi = np.zeros((SIM_H, SIM_W), dtype=np.float32)
u = np.zeros((SIM_H, SIM_W), dtype=np.float32)
v = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Coordinate grids for semi-Lagrangian advection
Y_idx, X_idx = np.indices((SIM_H, SIM_W), dtype=np.float32)

# --- Initialize Vortex Dipoles ---
CX = SIM_W // 2
CY = SIM_H // 2


def add_vortex(x0, y0, strength, sigma=8.0):
    global vorticity
    dx = X_idx - x0
    dy = Y_idx - y0
    dist2 = dx**2 + dy**2
    vorticity += strength * np.exp(-dist2 / (2.0 * sigma**2))


# Dipole 1 (starts left, travels right)
# A positive and negative vortex pair self-propels forward
add_vortex(CX - 90, CY - 20, 4.0)   # Positive (counter-clockwise)
add_vortex(CX - 90, CY + 20, -4.0)  # Negative (clockwise)

# Dipole 2 (starts right, travels left)
add_vortex(CX + 90, CY + 20, 4.0)   # Positive
add_vortex(CX + 90, CY - 20, -4.0)  # Negative

# --- Particles ---
NUM_PARTICLES = 6000
particle_pos = None  # Shape (NUM_PARTICLES, 2)
particle_age = None  # Shape (NUM_PARTICLES,)

# Trail Buffer (float32)
trail_buf = None
pimg = None


def setup():
    global particle_pos, particle_age, trail_buf, pimg

    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng(None)

    # Spawn particles concentrated in the central collision corridor
    px = rng.uniform(CX - 120, CX + 120, NUM_PARTICLES)
    py = rng.uniform(CY - 50, CY + 50, NUM_PARTICLES)
    particle_pos = np.stack([px, py], axis=1)
    particle_age = rng.integers(0, 200, NUM_PARTICLES)

    # Base trail buffer (Deep Velvet/Space Black)
    trail_buf = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    trail_buf[:, :, :] = np.array([2, 2, 5], dtype=np.float32)

    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)


def step_physics():
    global vorticity, psi, u, v

    # 1. Solve Poisson equation for Stream Function: L(psi) = -vorticity
    # Using 40 Jacobi relaxation iterations for rapid convergence
    for _ in range(40):
        psi[1:-1, 1:-1] = 0.25 * (
            psi[2:, 1:-1] + psi[:-2, 1:-1] +
            psi[1:-1, 2:] + psi[1:-1, :-2] +
            vorticity[1:-1, 1:-1]
        )

    # 2. Compute Velocity Field from Stream Function (u = d(psi)/dy, v = -d(psi)/dx)
    u[1:-1, 1:-1] = 0.5 * (psi[2:, 1:-1] - psi[:-2, 1:-1])
    v[1:-1, 1:-1] = -0.5 * (psi[1:-1, 2:] - psi[1:-1, :-2])

    # 3. Advect Vorticity using Semi-Lagrangian scheme
    X_back = np.clip(X_idx - u * DT, 0, SIM_W - 1)
    Y_back = np.clip(Y_idx - v * DT, 0, SIM_H - 1)

    # Bilinear interpolation
    x0 = np.floor(X_back).astype(np.int32)
    x1 = np.minimum(x0 + 1, SIM_W - 1)
    y0 = np.floor(Y_back).astype(np.int32)
    y1 = np.minimum(y0 + 1, SIM_H - 1)

    wa = X_back - x0
    wb = Y_back - y0

    vorticity_next = (
        vorticity[y0, x0] * (1.0 - wa) * (1.0 - wb) +
        vorticity[y0, x1] * wa * (1.0 - wb) +
        vorticity[y1, x0] * (1.0 - wa) * wb +
        vorticity[y1, x1] * wa * wb
    )

    # Apply viscosity/diffusion to stabilize vortex cores
    laplacian = (
        vorticity[2:, 1:-1] + vorticity[:-2, 1:-1] +
        vorticity[1:-1, 2:] + vorticity[1:-1, :-2] - 4.0 * vorticity[1:-1, 1:-1]
    )
    vorticity_next[1:-1, 1:-1] += VISCOSITY * laplacian

    vorticity = vorticity_next


def update_particles():
    global particle_pos, particle_age

    rng = np.random.default_rng()

    # Interpolate velocities at particle positions
    px = np.clip(particle_pos[:, 0], 0, SIM_W - 1)
    py = np.clip(particle_pos[:, 1], 0, SIM_H - 1)

    ix0 = px.astype(np.int32)
    ix1 = np.minimum(ix0 + 1, SIM_W - 1)
    iy0 = py.astype(np.int32)
    iy1 = np.minimum(iy0 + 1, SIM_H - 1)

    wa = px - ix0
    wb = py - iy0

    # Bilinear interpolate velocity U and V
    p_u = (
        u[iy0, ix0] * (1.0 - wa) * (1.0 - wb) +
        u[iy0, ix1] * wa * (1.0 - wb) +
        u[iy1, ix0] * (1.0 - wa) * wb +
        u[iy1, ix1] * wa * wb
    )
    p_v = (
        v[iy0, ix0] * (1.0 - wa) * (1.0 - wb) +
        v[iy0, ix1] * wa * (1.0 - wb) +
        v[iy1, ix0] * (1.0 - wa) * wb +
        v[iy1, ix1] * wa * wb
    )

    # Update coordinates
    particle_pos[:, 0] += p_u * DT + rng.normal(0, 0.04, NUM_PARTICLES)
    particle_pos[:, 1] += p_v * DT + rng.normal(0, 0.04, NUM_PARTICLES)

    # Age and reset rules
    particle_age += 1
    oob = (
        (particle_pos[:, 0] < 5) | (particle_pos[:, 0] > SIM_W - 5) |
        (particle_pos[:, 1] < 5) | (particle_pos[:, 1] > SIM_H - 5) |
        (particle_age > 240)
    )

    if np.any(oob):
        num_reset = np.sum(oob)
        # Respawn in the central collision zone to maintain density
        particle_pos[oob, 0] = rng.uniform(CX - 120, CX + 120, num_reset)
        particle_pos[oob, 1] = rng.uniform(CY - 50, CY + 50, num_reset)
        particle_age[oob] = 0


def draw():
    global trail_buf

    fc = py5.frame_count
    t = fc / TOTAL_FRAMES

    # --- Physics Step ---
    step_physics()
    update_particles()

    # --- Render to Trail Buffer ---
    # Trail persistence
    trail_buf *= 0.88
    trail_buf[:, :, 0] = np.maximum(trail_buf[:, :, 0], 2)
    trail_buf[:, :, 1] = np.maximum(trail_buf[:, :, 1], 2)
    trail_buf[:, :, 2] = np.maximum(trail_buf[:, :, 2], 5)

    # 1. Render Vorticity cores as glowing regions
    # Positive vorticity (counter-clockwise) -> Glowing Orange/Amber
    pos_mask = vorticity > 0.01
    val_pos = vorticity[pos_mask] * 90.0
    trail_buf[pos_mask, 0] += val_pos * 1.0  # Red
    trail_buf[pos_mask, 1] += val_pos * 0.7  # Green
    trail_buf[pos_mask, 2] += val_pos * 0.1  # Blue

    # Negative vorticity (clockwise) -> Glowing Cyan/Teal
    neg_mask = vorticity < -0.01
    val_neg = -vorticity[neg_mask] * 90.0
    trail_buf[neg_mask, 0] += val_neg * 0.1  # Red
    trail_buf[neg_mask, 1] += val_neg * 0.8  # Green
    trail_buf[neg_mask, 2] += val_neg * 1.0  # Blue

    # 2. Render advected fluid tracer particles
    px = np.clip(particle_pos[:, 0].astype(np.int32), 0, SIM_W - 1)
    py = np.clip(particle_pos[:, 1].astype(np.int32), 0, SIM_H - 1)

    # Speed-based coloring
    p_speeds = np.hypot(u[py, px], v[py, px])
    intensities = np.clip(p_speeds * 180.0, 40.0, 240.0)

    for i in range(NUM_PARTICLES):
        x, y = px[i], py[i]
        val = intensities[i]
        # Map particle type based on position relative to CY (initial top vs bottom)
        # Top-emitted -> Amber-Pink, Bottom-emitted -> Bright Cyan/White
        if y < CY:
            trail_buf[y, x, 0] += val * 1.0
            trail_buf[y, x, 1] += val * 0.5
            trail_buf[y, x, 2] += val * 0.4
        else:
            trail_buf[y, x, 0] += val * 0.3
            trail_buf[y, x, 1] += val * 0.8
            trail_buf[y, x, 2] += val * 1.0

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
    py5.background(2, 2, 5)
    py5.image(pimg, 0, 0, py5.width, py5.height)

    # --- HUD Overlay ---
    scale_x = py5.width / SIM_W
    ts = int(10 * scale_x)
    py5.no_stroke()

    # Dark panel
    panel_w = int(280 * scale_x)
    panel_h = int(105 * scale_x)
    py5.fill(1, 1, 3, 210)
    py5.rect(0, 0, panel_w, panel_h, 0, 0, 8, 0)

    # Title
    py5.fill(250, 180, 80)
    py5.text_size(ts)
    py5.text("VORTEX DIPOLE COLLISION // 2D NS", int(12 * scale_x), int(20 * scale_x))

    # Stats
    py5.text_size(int(7.5 * scale_x))
    py5.fill(160, 175, 200)
    py5.text(f"Grid Size:     {SIM_W} x {SIM_H}", int(12 * scale_x), int(38 * scale_x))
    py5.text(f"Simulation t:  {fc/FPS:.2f}s / {DURATION_SEC:.1f}s", int(12 * scale_x), int(53 * scale_x))
    py5.text(f"Viscosity:     ν = {VISCOSITY:.3f}", int(12 * scale_x), int(68 * scale_x))
    py5.text(f"Particles:     N = {NUM_PARTICLES} Stream Tracers", int(12 * scale_x), int(83 * scale_x))

    # Kinetic Energy Bar (average speed magnitude)
    avg_ke = float(np.mean(u**2 + v**2))
    bar_x = int(12 * scale_x)
    bar_y = int(92 * scale_x)
    bar_w = int(256 * scale_x)
    bar_h = int(5 * scale_x)
    py5.fill(10, 10, 20)
    py5.rect(bar_x, bar_y, bar_w, bar_h, 2)
    
    fill_ratio = np.clip(avg_ke * 20.0, 0.0, 1.0)
    py5.fill(240, 140, 60)
    py5.rect(bar_x, bar_y, int(bar_w * fill_ratio), bar_h, 2)

    # Progress bar at bottom
    py5.fill(5, 5, 12)
    py5.rect(0, py5.height - int(4 * scale_x), py5.width, int(4 * scale_x))
    py5.fill(235, 160, 70)
    py5.rect(0, py5.height - int(4 * scale_x), int(py5.width * t), int(4 * scale_x))

    # Watermark
    py5.fill(120, 130, 160, 80)
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
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | Mean KE = {avg_ke:.5f}")

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

        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")

        import os
        os._exit(0)


py5.run_sketch()

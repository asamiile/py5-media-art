"""
kinetic_maxwell_poynting_flow_2d

A 4K kinetic visualization of electromagnetism: solving the 2D Maxwell's equations
via FDTD and mapping the Poynting vector (energy flux) to the flow of glowing
tracer particles around a dielectric split-ring resonator.
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
SIM_W, SIM_H = 480, 270  # Simulation grid size

# --- Physical Constants & FDTD Parameters ---
C = 0.5  # Courant number (stability requires C < 1/sqrt(2) ≈ 0.707)
ch = C
ce = C

# --- Permittivity Field (Obstacles) ---
epsilon = np.ones((SIM_H, SIM_W), dtype=np.float32)

# Create a central split-ring resonator (high dielectric)
CY = SIM_H // 2
CX = SIM_W // 2
R_OUTER = 50
R_INNER = 35
SLOT_W = 14

for y in range(SIM_H):
    for x in range(SIM_W):
        dx = x - CX
        dy = y - CY
        r = math.hypot(dx, dy)
        if R_INNER <= r <= R_OUTER:
            # Create a slot opening on the right (dx > 0)
            if not (dx > 0 and abs(dy) < SLOT_W):
                epsilon[y, x] = 12.0  # High relative permittivity (refraction/scattering)

# Add a lattice of smaller circular scatterers around the main ring
scatterer_centers = [
    (CX - 120, CY - 60), (CX - 120, CY + 60),
    (CX + 120, CY - 60), (CX + 120, CY + 60),
    (CX, CY - 90), (CX, CY + 90),
]
for scx, scy in scatterer_centers:
    for y in range(SIM_H):
        for x in range(SIM_W):
            if math.hypot(x - scx, y - scy) < 10:
                epsilon[y, x] = 8.0

# --- Boundary Absorber (Simple viscous damping to simulate open space) ---
absorber = np.ones((SIM_H, SIM_W), dtype=np.float32)
BORDER = 20
for b in range(BORDER):
    factor = 0.85 + 0.15 * (b / BORDER) ** 2  # Smooth damping curve
    absorber[b, :] = np.minimum(absorber[b, :], factor)
    absorber[-1 - b, :] = np.minimum(absorber[-1 - b, :], factor)
    absorber[:, b] = np.minimum(absorber[:, b], factor)
    absorber[:, -1 - b] = np.minimum(absorber[:, -1 - b], factor)

# --- State ---
Ez = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Hx = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Hy = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# Poynting Vector Field
Sx = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Sy = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Sx_smooth = np.zeros((SIM_H, SIM_W), dtype=np.float32)
Sy_smooth = np.zeros((SIM_H, SIM_W), dtype=np.float32)

# --- Particles ---
NUM_PARTICLES = 3000
particle_pos = None  # Shape (NUM_PARTICLES, 2)
particle_vel = None  # Shape (NUM_PARTICLES, 2)
particle_age = None  # Shape (NUM_PARTICLES,)

# Trail Buffer (float32)
trail_buf = None
pimg = None

def setup():
    global particle_pos, particle_vel, particle_age, trail_buf, pimg

    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

    rng = np.random.default_rng(None)

    # Initialize particle positions randomly
    particle_pos = rng.uniform([10, 10], [SIM_W - 10, SIM_H - 10], (NUM_PARTICLES, 2))
    particle_vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    particle_age = rng.integers(0, 150, NUM_PARTICLES)

    # Base trail buffer (Deep Navy/Black)
    trail_buf = np.zeros((SIM_H, SIM_W, 3), dtype=np.float32)
    trail_buf[:, :, :] = np.array([4, 6, 12], dtype=np.float32)

    pimg = py5.create_image(SIM_W, SIM_H, py5.ARGB)


def update_maxwell(frame_count):
    global Ez, Hx, Hy, Sx, Sy, Sx_smooth, Sy_smooth

    # 1. Update H field (Magnetic field updates use Ez differences)
    Hx[:, :-1] -= ch * (Ez[:, 1:] - Ez[:, :-1])
    Hy[:-1, :] += ch * (Ez[1:, :] - Ez[:-1, :])

    # Apply absorbing boundaries to H
    Hx *= absorber
    Hy *= absorber

    # 2. Update E field (Electric field update uses H differences)
    # Yee cell centered update
    Ez[1:, 1:] += (ce / epsilon[1:, 1:]) * (
        (Hy[1:, 1:] - Hy[:-1, 1:]) - (Hx[1:, 1:] - Hx[1:, :-1])
    )

    # Apply absorbing boundaries to E
    Ez *= absorber

    # 3. Inject Sources (Two point sources on the left emitting out-of-phase waves)
    omega = 2.0 * math.pi * 0.085  # wave frequency
    src_val1 = math.sin(omega * frame_count) * 1.5
    src_val2 = math.sin(omega * frame_count + math.pi * 0.5) * 1.5  # 90 deg phase shift

    Ez[CY - 40, 45] = src_val1
    Ez[CY + 40, 45] = src_val2

    # 4. Calculate Poynting Vector Field: S = E x H
    # Interpolate Hx and Hy to center grid where Ez is located
    Hx_c = 0.5 * (Hx[:, 1:] + Hx[:, :-1])  # (H, W-1)
    Hy_c = 0.5 * (Hy[1:, :] + Hy[:-1, :])  # (H-1, W)

    # Pad back to full size
    Hx_center = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    Hy_center = np.zeros((SIM_H, SIM_W), dtype=np.float32)
    Hx_center[:, 1:] = Hx_c
    Hy_center[1:, :] = Hy_c

    # S_x = -E_z * H_y, S_y = E_z * H_x
    Sx[:, :] = -Ez * Hy_center
    Sy[:, :] = Ez * Hx_center

    # Apply smoothing to Poynting vector for smooth particle drift
    Sx_smooth[:] = 0.95 * Sx_smooth + 0.05 * Sx
    Sy_smooth[:] = 0.95 * Sy_smooth + 0.05 * Sy


def update_particles():
    global particle_pos, particle_age

    rng = np.random.default_rng()

    # Get integer grid coordinates for particle lookup
    px = np.clip(particle_pos[:, 0].astype(np.int32), 0, SIM_W - 1)
    py = np.clip(particle_pos[:, 1].astype(np.int32), 0, SIM_H - 1)

    # Fetch Poynting velocity vectors
    vx = Sx_smooth[py, px]
    vy = Sy_smooth[py, px]

    # Add velocity with a limit, plus a tiny bit of random thermal motion
    # Also add the raw instantaneous Poynting vector for wave-like oscillations
    vx_raw = Sx[py, px]
    vy_raw = Sy[py, px]

    particle_vel[:, 0] = 0.85 * particle_vel[:, 0] + 0.15 * (vx * 12.0 + vx_raw * 6.0)
    particle_vel[:, 1] = 0.85 * particle_vel[:, 1] + 0.15 * (vy * 12.0 + vy_raw * 6.0)

    # Update position
    particle_pos += particle_vel + rng.normal(0, 0.05, particle_pos.shape)

    # Check boundaries and age, reset if out of bounds or dead
    particle_age += 1
    oob = (
        (particle_pos[:, 0] < 5) | (particle_pos[:, 0] > SIM_W - 5) |
        (particle_pos[:, 1] < 5) | (particle_pos[:, 1] > SIM_H - 5) |
        (particle_age > 180)
    )

    if np.any(oob):
        num_reset = np.sum(oob)
        # Reset to random positions with bias to the left source region
        particle_pos[oob] = rng.uniform([10, 20], [SIM_W // 2, SIM_H - 20], (num_reset, 2))
        particle_vel[oob] = 0.0
        particle_age[oob] = 0


def draw():
    global trail_buf

    fc = py5.frame_count
    t = fc / TOTAL_FRAMES

    # --- Update Physics ---
    update_maxwell(fc)
    update_particles()

    # --- Render to Trail Buffer ---
    # Decay trails (giving fluid motion persistence)
    trail_buf *= 0.90  # High persistence
    trail_buf[:, :, 0] = np.maximum(trail_buf[:, :, 0], 4)
    trail_buf[:, :, 1] = np.maximum(trail_buf[:, :, 1], 6)
    trail_buf[:, :, 2] = np.maximum(trail_buf[:, :, 2], 12)

    # 1. Draw Electric Field Ez as glowing waves
    # Normalize Ez for visual mapping
    ez_vis = np.clip(Ez * 90.0, -120.0, 120.0)

    # Map Ez to Teal/Cyan (positive) and Deep Indigo/Magenta (negative)
    # Positive Ez -> Add Cyan
    pos_mask = ez_vis > 0
    trail_buf[pos_mask, 0] += ez_vis[pos_mask] * 0.2    # Red
    trail_buf[pos_mask, 1] += ez_vis[pos_mask] * 0.95   # Green
    trail_buf[pos_mask, 2] += ez_vis[pos_mask] * 1.0    # Blue

    # Negative Ez -> Add Deep Violet
    neg_mask = ez_vis < 0
    val_neg = -ez_vis[neg_mask]
    trail_buf[neg_mask, 0] += val_neg * 0.8  # Red
    trail_buf[neg_mask, 1] += val_neg * 0.1  # Green
    trail_buf[neg_mask, 2] += val_neg * 0.95 # Blue

    # 2. Draw Dielectric Resonator Ring and Obstacles (Luminescent Purple Outline)
    obs_mask = epsilon > 1.0
    # Blend a static purple glow into the obstacles
    trail_buf[obs_mask, 0] = 0.8 * trail_buf[obs_mask, 0] + 0.2 * 110.0
    trail_buf[obs_mask, 1] = 0.8 * trail_buf[obs_mask, 1] + 0.2 * 30.0
    trail_buf[obs_mask, 2] = 0.8 * trail_buf[obs_mask, 2] + 0.2 * 150.0

    # 3. Draw Poynting Flow Particles as bright amber streamlines
    px = np.clip(particle_pos[:, 0].astype(np.int32), 0, SIM_W - 1)
    py = np.clip(particle_pos[:, 1].astype(np.int32), 0, SIM_H - 1)

    # Speeds determine intensity
    speeds = np.linalg.norm(particle_vel, axis=1)
    intensity = np.clip(speeds * 35.0, 50.0, 255.0)

    # Accumulate particle pixels on trail_buf
    for i in range(NUM_PARTICLES):
        x, y = px[i], py[i]
        val = intensity[i]
        # Draw a tiny 1x2 dot for streaks
        trail_buf[y, x, 0] += val * 1.0    # Amber Red
        trail_buf[y, x, 1] += val * 0.75   # Amber Green
        trail_buf[y, x, 2] += val * 0.1    # Amber Blue

        # Draw neighboring pixel to anti-alias / soften
        if x + 1 < SIM_W:
            trail_buf[y, x + 1, 0] += val * 0.4
            trail_buf[y, x + 1, 1] += val * 0.3
        if y + 1 < SIM_H:
            trail_buf[y + 1, x, 0] += val * 0.4
            trail_buf[y + 1, x, 1] += val * 0.3

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
    py5.background(4, 6, 12)
    py5.image(pimg, 0, 0, py5.width, py5.height)

    # --- HUD Overlay ---
    scale_x = py5.width / SIM_W
    ts = int(10 * scale_x)
    py5.no_stroke()

    # Dark telemetry panel
    panel_w = int(280 * scale_x)
    panel_h = int(105 * scale_x)
    py5.fill(2, 3, 7, 220)
    py5.rect(0, 0, panel_w, panel_h, 0, 0, 8, 0)

    # Title
    py5.fill(130, 240, 220)
    py5.text_size(ts)
    py5.text("MAXWELL POYNTING FLOW // 2D FDTD", int(12 * scale_x), int(20 * scale_x))

    # Stats
    py5.text_size(int(7.5 * scale_x))
    py5.fill(170, 180, 210)
    py5.text(f"Grid Size:     {SIM_W} x {SIM_H}", int(12 * scale_x), int(38 * scale_x))
    py5.text(f"Time (t):      {fc/FPS:.2f}s / {DURATION_SEC:.1f}s", int(12 * scale_x), int(53 * scale_x))
    py5.text(f"Permittivity:  ε_r = 12.0 (Resonator)", int(12 * scale_x), int(68 * scale_x))
    py5.text(f"Energy Flux:   S = E × H ({NUM_PARTICLES} Streamlines)", int(12 * scale_x), int(83 * scale_x))

    # Energy Bar (Root Mean Square of Ez)
    rms_ez = math.sqrt(float(np.mean(Ez**2)))
    bar_x = int(12 * scale_x)
    bar_y = int(92 * scale_x)
    bar_w = int(256 * scale_x)
    bar_h = int(5 * scale_x)
    py5.fill(15, 20, 35)
    py5.rect(bar_x, bar_y, bar_w, bar_h, 2)
    
    # Fill bar based on Ez amplitude
    fill_ratio = np.clip(rms_ez * 8.0, 0.0, 1.0)
    py5.fill(35, 220, 180)
    py5.rect(bar_x, bar_y, int(bar_w * fill_ratio), bar_h, 2)

    # Progress bar at bottom
    py5.fill(10, 15, 25)
    py5.rect(0, py5.height - int(4 * scale_x), py5.width, int(4 * scale_x))
    py5.fill(35, 180, 210)
    py5.rect(0, py5.height - int(4 * scale_x), int(py5.width * t), int(4 * scale_x))

    # Watermark
    py5.fill(120, 140, 180, 80)
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
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%) | RMS_Ez = {rms_ez:.4f}")

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

        # Save a preview snapshot at total_frames // 2
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory removed.")

        import os
        os._exit(0)


py5.run_sketch()

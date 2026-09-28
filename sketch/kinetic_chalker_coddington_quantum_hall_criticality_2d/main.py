"""
Kinetic Chalker-Coddington Quantum Hall Criticality 2D
Generative media art depicting multifractal electronic wavefunctions,
random magnetic disorder potential landscapes, chiral edge percolation channels,
and saddle-point quantum tunneling in the integer quantum Hall plateau transition.

Features:
- Smooth random disorder potential landscape V(x, y) with saddle-point QPCs
- Oscillating Fermi energy E_F(t) tuning through the critical Landau level center
- Chiral edge percolation channels flowing along equipotential contours
- Quantum phase winding along percolating paths with interference nodes
- Dual-light Blinn-Phong specular normal mapping for cryogenic 2DEG topography
- 4,000 chiral cyclotron electrons executing E x B guiding center drift and saddle tunneling
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_chalker_coddington_quantum_hall_criticality_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 900
FPS = 60
SIZE = (1920, 1080)

# Computational Grid
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-6.4, 6.4, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-3.6, 3.6, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32) # Cool cyan
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)  # Warm gold

# Pre-generate 24 random Fourier modes for reproducible smooth disorder landscape
np.random.seed(101)
MODES = []
for _ in range(24):
    kx = float(np.random.uniform(0.7, 3.2))
    ky = float(np.random.uniform(0.7, 3.2))
    phase = float(np.random.uniform(0.0, 2.0 * np.pi))
    amp = float(np.random.uniform(0.35, 1.0))
    MODES.append((kx, ky, phase, amp))

# Particle system: 4,000 chiral cyclotron electrons
NUM_PARTICLES = 4000
P_X = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_Y = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_LARMOR_PHASE = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_COLOR_TYPE = np.zeros(NUM_PARTICLES, dtype=np.int32)

def init_particles():
    global P_X, P_Y, P_LARMOR_PHASE, P_COLOR_TYPE
    np.random.seed(77)
    P_X = np.random.uniform(-6.3, 6.3, size=NUM_PARTICLES).astype(np.float32)
    P_Y = np.random.uniform(-3.5, 3.5, size=NUM_PARTICLES).astype(np.float32)
    P_LARMOR_PHASE = np.random.uniform(0.0, 2.0 * np.pi, size=NUM_PARTICLES).astype(np.float32)
    P_COLOR_TYPE = np.random.choice([0, 1, 2], size=NUM_PARTICLES, p=[0.5, 0.35, 0.15])

init_particles()


def compute_quantum_hall_field(t_norm):
    """
    Computes the disorder landscape, critical percolating wavefunctions,
    drift velocity field, and specular normal lighting.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. Random Disorder Potential V(x, y) with slow breathing
    V = np.zeros_like(x)
    for kx, ky, phase, amp in MODES:
        V += amp * np.sin(kx * x + ky * y + phase + 0.35 * np.sin(tau))

    V_max = np.max(np.abs(V))
    V = V / (V_max + 1e-5)

    # 2. Fermi energy sweep near the critical Landau level center (E = 0)
    E_F = 0.16 * np.sin(tau)
    delta_E = V - E_F

    # 3. Wavefunction probability density |psi|^2 along percolation channels
    channel_width = 0.13
    psi_sq = np.exp(-0.5 * (delta_E / channel_width)**2)

    # Gradients of potential: Ex = -dV/dx, Ey = -dV/dy
    gy, gx = np.gradient(V)
    grad_mag = np.sqrt(gx**2 + gy**2) + 0.04

    # Drift velocity field: v = (-gy, gx) / grad_mag (chiral equipotential flow)
    v_drift_x = -gy / grad_mag
    v_drift_y = gx / grad_mag

    # Quantum phase winding along the percolation channels
    chiral_phase = 12.0 * (x * v_drift_x + y * v_drift_y) + 3.0 * tau
    phase_fringe = np.cos(chiral_phase)**2

    # Saddle point tunneling nodes (Quantum Point Contacts: small grad_mag & delta_E ~ 0)
    saddle_metric = np.exp(-0.5 * (grad_mag / 0.14)**2) * np.exp(-0.5 * (delta_E / 0.14)**2)

    # 4. Normal mapping & specular topography
    nx = -gx * 3.2
    ny = -gy * 3.2
    nz = np.ones_like(nx)
    norm_len = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = dot1 ** 16.0

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = dot2 ** 22.0

    # 5. Color synthesis:
    # Potential Hills (V > 0): Luminescent Electric Coral & Solar Gold
    # Potential Valleys (V < 0): Deep Cryogenic Cobalt Azure & Midnight Obsidian
    # Critical Percolating Channels: Phosphorescent Electric Mint & Glacial Cyan
    # Saddle tunneling nodes: Liquid Incandescent White
    v_norm = np.clip(V * 0.5 + 0.5, 0.0, 1.0)

    r_hill, g_hill, b_hill = 45.0, 18.0, 78.0
    r_val, g_val, b_val = 8.0, 16.0, 42.0

    base_r = (1.0 - v_norm) * r_val + v_norm * r_hill
    base_g = (1.0 - v_norm) * g_val + v_norm * g_hill
    base_b = (1.0 - v_norm) * b_val + v_norm * b_hill

    # Percolating channel glow with phase modulation
    channel_glow = psi_sq * (0.7 + 0.3 * phase_fringe)

    r_out = base_r + channel_glow * 25.0 + saddle_metric * 255.0 + spec2 * 255.0
    g_out = base_g + channel_glow * 245.0 + saddle_metric * 255.0 + spec1 * 180.0 + spec2 * 180.0
    b_out = base_b + channel_glow * 255.0 + saddle_metric * 255.0 + spec1 * 255.0

    rgb = np.stack([
        np.clip(r_out, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_out, 0, 255).astype(np.uint8)
    ], axis=-1)

    return rgb, v_drift_x, v_drift_y, saddle_metric


def to_screen(x, y):
    sx = int((x + 6.4) / 12.8 * SIZE[0])
    sy = int((y + 3.6) / 7.2 * SIZE[1])
    return sx, sy


def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count

    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = ((frame - 1) % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    field_rgb, v_x, v_y, saddle = compute_quantum_hall_field(t_norm)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Advect and draw 4,000 chiral cyclotron electrons
    global P_X, P_Y, P_LARMOR_PHASE
    P_LARMOR_PHASE += 0.25 # Cyclotron gyration frequency

    grid_ix = np.clip(((P_X + 6.4) / 12.8 * (GRID_W - 1)).astype(np.int32), 0, GRID_W - 1)
    grid_iy = np.clip(((P_Y + 3.6) / 7.2 * (GRID_H - 1)).astype(np.int32), 0, GRID_H - 1)

    drift_u = v_x[grid_iy, grid_ix] * 0.038
    drift_v = v_y[grid_iy, grid_ix] * 0.038
    s_tunnel = saddle[grid_iy, grid_ix]

    # At saddle points, quantum tunneling introduces transverse branching
    tunnel_kick = np.where(s_tunnel > 0.4, np.sin(tau * 5.0 + P_LARMOR_PHASE) * 0.03, 0.0)

    P_X += drift_u + tunnel_kick
    P_Y += drift_v - tunnel_kick

    # Periodic boundary wrap
    P_X = np.where(P_X > 6.35, -6.35, P_X)
    P_X = np.where(P_X < -6.35, 6.35, P_X)
    P_Y = np.where(P_Y > 3.55, -3.55, P_Y)
    P_Y = np.where(P_Y < -3.55, 3.55, P_Y)

    # Draw electrons with cyclotron gyration
    r_cyclotron = 0.035
    for i in range(NUM_PARTICLES):
        larmor_x = P_X[i] + r_cyclotron * np.cos(P_LARMOR_PHASE[i])
        larmor_y = P_Y[i] + r_cyclotron * np.sin(P_LARMOR_PHASE[i])

        sx, sy = to_screen(larmor_x, larmor_y)
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            ctype = P_COLOR_TYPE[i]
            if ctype == 0:
                py5.stroke(0, 255, 170, 200) # Mint Flare
                py5.stroke_weight(1.5)
            elif ctype == 1:
                py5.stroke(0, 220, 255, 210) # Electric Cyan
                py5.stroke_weight(1.6)
            else:
                py5.stroke(255, 255, 255, 240) # Incandescent Tunneling Pearl
                py5.stroke_weight(2.0)
            py5.point(sx, sy)

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Chalker-Coddington preview captured: {PREVIEW_FILE}")

    if frame % 60 == 0:
        pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({pct:.1f}%)")


def finish_render():
    print("[Rendering Complete] Encoding master MP4 via ffmpeg...")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        OUTPUT_VIDEO
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[Video Compiled] Master MP4 saved: {OUTPUT_VIDEO}")
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
    else:
        print(f"[Video Encoding Failed] ffmpeg error:\n{res.stderr}")

    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

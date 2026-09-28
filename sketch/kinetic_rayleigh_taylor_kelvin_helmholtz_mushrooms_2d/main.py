"""
Kinetic Rayleigh-Taylor Kelvin-Helmholtz Mushrooms 2D
Generative media art depicting multi-mode Rayleigh-Taylor interfacial instability
with Atwood number density stratification (At ~ 0.6), baroclinic vorticity generation,
secondary Kelvin-Helmholtz mushroom rollups, and Lagrangian fluid tracer advection.

Features:
- Multi-mode interfacial perturbation growth and non-linear spike/bubble development
- Counter-rotating Kelvin-Helmholtz vortex spirals forming nested mushroom caps
- Baroclinic torque vorticity fringes and shear boundary layer highlights
- Dual-light Blinn-Phong specular normal mapping on the fluid meniscus interface
- 4,500 Lagrangian fluid tracer particles tracing swirling stream-function paths
- 900 frames @ 60 FPS (15 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_rayleigh_taylor_kelvin_helmholtz_mushrooms_2d"
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
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32) # Cool cyan specular
LIGHT2_DIR = np.array([0.485, 0.647, 0.589], dtype=np.float32)  # Warm gold specular

# Particle system: 4,500 fluid tracer particles
NUM_PARTICLES = 4500
P_X = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_Y = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_COLOR_TYPE = np.zeros(NUM_PARTICLES, dtype=np.int32)

SPIKE_CENTERS = [-4.0, -1.3, 1.4, 4.1]

def init_particles():
    global P_X, P_Y, P_COLOR_TYPE
    np.random.seed(42)
    P_X = np.random.uniform(-6.3, 6.3, size=NUM_PARTICLES).astype(np.float32)
    P_Y = np.random.uniform(-3.5, 3.5, size=NUM_PARTICLES).astype(np.float32)
    P_COLOR_TYPE = np.random.choice([0, 1, 2], size=NUM_PARTICLES, p=[0.45, 0.35, 0.20])

init_particles()


def compute_fluid_field(t_norm):
    """
    Computes fluid density field, Kelvin-Helmholtz rollups, and specular normal lighting.
    """
    tau = 2.0 * np.pi * t_norm
    # Seamless pulsation in growth parameter
    growth = 1.0 + 0.85 * np.sin(tau)
    phase_shift = 0.5 * np.cos(tau)

    x, y = GX, GY

    # Base multi-mode interface perturbation
    k1, k2, k3 = 1.5, 3.0, 4.5
    spike_depth = 1.8 * growth
    bubble_height = 1.2 * growth

    y_base = (
        0.45 * np.cos(k1 * x + phase_shift) * bubble_height -
        0.25 * np.cos(k2 * x + 0.6) * growth +
        0.12 * np.sin(k3 * x + tau)
    )

    # Falling heavy fluid spikes
    for sc in SPIKE_CENTERS:
        dist_x = np.abs(x - sc)
        y_base -= spike_depth * np.exp(-0.5 * (dist_x / 0.52)**2)

    # Kelvin-Helmholtz vortex sheet rollup (mushroom caps)
    vortex_dx = np.zeros_like(x)
    vortex_dy = np.zeros_like(x)

    gamma_vortex = 1.9 * growth
    core_rad = 0.42

    for sc in SPIKE_CENTERS:
        # Left flank vortex
        vx_l = sc - 0.52 * growth
        vy_l = -spike_depth * 0.72
        rx_l = x - vx_l
        ry_l = y - vy_l
        r2_l = rx_l**2 + ry_l**2 + core_rad**2
        vortex_dx -= gamma_vortex * ry_l / r2_l
        vortex_dy += gamma_vortex * rx_l / r2_l

        # Right flank vortex
        vx_r = sc + 0.52 * growth
        vy_r = -spike_depth * 0.72
        rx_r = x - vx_r
        ry_r = y - vy_r
        r2_r = rx_r**2 + ry_r**2 + core_rad**2
        vortex_dx += gamma_vortex * ry_r / r2_r
        vortex_dy -= gamma_vortex * rx_r / r2_r

    # Advected coordinates
    advect_x = x + 0.24 * vortex_dx
    advect_y = y + 0.24 * vortex_dy

    # Fluid density rho in [0, 1]
    interface_dist = advect_y - y_base
    thickness = 0.17
    rho = 0.5 * (1.0 + np.tanh(interface_dist / thickness))

    # Vorticity roll-up fringes
    vort_fringe = np.sin(7.5 * (vortex_dx + vortex_dy))**2 * np.exp(-0.5 * (interface_dist / 0.55)**2)

    # Normal mapping & specular sheen
    gy, gx = np.gradient(rho)
    nx = -gx * 3.4
    ny = -gy * 3.4
    nz = np.ones_like(nx)
    norm_len = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = dot1 ** 16.0

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = dot2 ** 22.0

    # Color synthesis:
    # Heavy Fluid (top, rho ~ 1): Deep Obsidian Indigo & Sapphire Abyss
    # Light Fluid (bottom, rho ~ 0): Molten Solar Amber & Radiant Gold
    # Mixing Layer: Phosphorescent Emerald Teal & Coral Violet
    r_heavy, g_heavy, b_heavy = 9.0, 22.0, 52.0
    r_light, g_light, b_light = 245.0, 145.0, 22.0

    base_r = (1.0 - rho) * r_light + rho * r_heavy
    base_g = (1.0 - rho) * g_light + rho * g_heavy
    base_b = (1.0 - rho) * b_light + rho * b_heavy

    grad_mag = np.sqrt(gx**2 + gy**2)
    grad_norm = np.clip(grad_mag * 4.2, 0.0, 1.0)

    r_out = base_r + grad_norm * 45.0 + vort_fringe * 125.0 + spec2 * 255.0
    g_out = base_g + grad_norm * 185.0 + vort_fringe * 225.0 + spec1 * 185.0 + spec2 * 185.0
    b_out = base_b + grad_norm * 245.0 + vort_fringe * 195.0 + spec1 * 255.0

    rgb = np.stack([
        np.clip(r_out, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_out, 0, 255).astype(np.uint8)
    ], axis=-1)
    return rgb, vortex_dx, vortex_dy


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

    field_rgb, v_dx, v_dy = compute_fluid_field(t_norm)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Advect and draw 4,500 Lagrangian tracer particles
    global P_X, P_Y
    # Sample velocity from grid coordinates
    grid_ix = np.clip(((P_X + 6.4) / 12.8 * (GRID_W - 1)).astype(np.int32), 0, GRID_W - 1)
    grid_iy = np.clip(((P_Y + 3.6) / 7.2 * (GRID_H - 1)).astype(np.int32), 0, GRID_H - 1)

    u_x = v_dx[grid_iy, grid_ix] * 0.04
    u_y = v_dy[grid_iy, grid_ix] * 0.04

    P_X += u_x
    P_Y += u_y

    # Wrap boundary
    P_X = np.where(P_X > 6.3, -6.3, P_X)
    P_X = np.where(P_X < -6.3, 6.3, P_X)
    P_Y = np.where(P_Y > 3.5, -3.5, P_Y)
    P_Y = np.where(P_Y < -3.5, 3.5, P_Y)

    for i in range(NUM_PARTICLES):
        sx, sy = to_screen(P_X[i], P_Y[i])
        if 0 <= sx < SIZE[0] and 0 <= sy < SIZE[1]:
            ctype = P_COLOR_TYPE[i]
            if ctype == 0:
                py5.stroke(0, 255, 180, 190) # Electric Emerald Teal
                py5.stroke_weight(1.5)
            elif ctype == 1:
                py5.stroke(255, 200, 60, 200) # Solar Gold
                py5.stroke_weight(1.6)
            else:
                py5.stroke(255, 255, 255, 240) # Incandescent White
                py5.stroke_weight(2.0)
            py5.point(sx, sy)

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 250:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Rayleigh-Taylor preview captured: {PREVIEW_FILE}")

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

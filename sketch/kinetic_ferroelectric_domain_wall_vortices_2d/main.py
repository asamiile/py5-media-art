"""
Kinetic Ferroelectric Domain Wall Vortices 2D (Revised)
Generative media art depicting spontaneous electric polarization,
chiral flux-closure polarization vortices, charged conductive domain walls,
and electromechanical switching dynamics under alternating electric stress.

Features:
- Razor-sharp non-linear saturated polarization fields tanh(P * 5) forming crisp 90° and 180° domain walls
- Incandescent conductive domain wall filaments running along high-energy phase seams
- Chiral flux-closure polarization vortices spinning at crystal vertex nodes
- Piezoelectric surface relief with dual-light Blinn-Phong specular normal mapping
- 2,800 Lagrangian screening carriers tracing conductive domain walls and vortex loops
- Fast vectorized batch rendering via py5.lines() and py5.points()
- 720 frames @ 60 FPS (12 seconds seamless loop)
"""

import os
import shutil
import subprocess
import numpy as np
import py5

WORK_NAME = "kinetic_ferroelectric_domain_wall_vortices_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
OUTPUT_VIDEO = os.path.join(SKETCH_DIR, "output.mp4")
WORK_VIDEO = os.path.join(SKETCH_DIR, f"{WORK_NAME}.mp4")
PREVIEW_FILE = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 720
FPS = 60
SIZE = (1920, 1080)

# Computational Grid for field synthesis
GRID_W, GRID_H = 480, 270
X_COORDS = np.linspace(-6.4, 6.4, GRID_W, dtype=np.float32)
Y_COORDS = np.linspace(-3.6, 3.6, GRID_H, dtype=np.float32)
GX, GY = np.meshgrid(X_COORDS, Y_COORDS)

# Normal mapping directional lights
LIGHT1_DIR = np.array([-0.577, -0.577, 0.577], dtype=np.float32)  # Cool azure cyan
LIGHT2_DIR = np.array([0.577, 0.577, 0.577], dtype=np.float32)    # Warm coral gold

# Vortex core centers in normalized crystal domain
VORTEX_CENTERS = [
    (-3.2, -1.8, 1.0),
    (-3.2, 1.8, -1.0),
    (0.0, -1.8, -1.0),
    (0.0, 1.8, 1.0),
    (3.2, -1.8, 1.0),
    (3.2, 1.8, -1.0),
]

# Particle system: 2,800 screening carriers with multi-segment history trails
NUM_PARTICLES = 2800
TRAIL_LEN = 6

P_X = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_Y = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_VX = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_VY = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_TYPE = np.zeros(NUM_PARTICLES, dtype=np.int32)     # 0: Wall Conduction (White/Gold), 1: Vortex Orbit (Cyan), 2: Switching Sparks (Coral)
P_VORTEX_IDX = np.zeros(NUM_PARTICLES, dtype=np.int32)
P_ANGLE = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_RADIUS = np.zeros(NUM_PARTICLES, dtype=np.float32)
P_AGE = np.zeros(NUM_PARTICLES, dtype=np.float32)

TRAIL_X = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)
TRAIL_Y = np.zeros((NUM_PARTICLES, TRAIL_LEN), dtype=np.float32)


def init_particles():
    global P_X, P_Y, P_VX, P_VY, P_TYPE, P_VORTEX_IDX, P_ANGLE, P_RADIUS, P_AGE, TRAIL_X, TRAIL_Y
    np.random.seed(123)

    # 1,400 Domain Wall conduction carriers (Type 0)
    n_wall = 1400
    P_X[:n_wall] = np.random.uniform(-6.2, 6.2, size=n_wall).astype(np.float32)
    P_Y[:n_wall] = np.random.uniform(-3.4, 3.4, size=n_wall).astype(np.float32)
    dirs = np.random.choice([-1.0, 1.0], size=n_wall).astype(np.float32)
    P_VX[:n_wall] = dirs * np.random.uniform(0.04, 0.07, size=n_wall).astype(np.float32)
    P_VY[:n_wall] = dirs * np.random.uniform(0.04, 0.07, size=n_wall).astype(np.float32)
    P_TYPE[:n_wall] = 0
    P_AGE[:n_wall] = np.random.uniform(0.0, 100.0, size=n_wall).astype(np.float32)

    # 900 Vortex orbital charges (Type 1)
    n_vortex = 900
    start_v = n_wall
    end_v = start_v + n_vortex
    v_indices = np.random.choice(len(VORTEX_CENTERS), size=n_vortex)
    angles = np.random.uniform(0.0, 2.0 * np.pi, size=n_vortex).astype(np.float32)
    radii = np.random.uniform(0.35, 1.25, size=n_vortex).astype(np.float32)
    P_VORTEX_IDX[start_v:end_v] = v_indices
    P_ANGLE[start_v:end_v] = angles
    P_RADIUS[start_v:end_v] = radii
    for i, idx in enumerate(v_indices):
        cx, cy, _ = VORTEX_CENTERS[idx]
        P_X[start_v + i] = cx + radii[i] * np.cos(angles[i])
        P_Y[start_v + i] = cy + radii[i] * np.sin(angles[i])
    P_TYPE[start_v:end_v] = 1
    P_AGE[start_v:end_v] = np.random.uniform(0.0, 100.0, size=n_vortex).astype(np.float32)

    # 500 Switching needle sparks (Type 2)
    n_switch = NUM_PARTICLES - end_v
    P_X[end_v:] = np.random.uniform(-6.2, 6.2, size=n_switch).astype(np.float32)
    P_Y[end_v:] = np.random.uniform(-3.4, 3.4, size=n_switch).astype(np.float32)
    s_dirs = np.random.choice([-1.0, 1.0], size=n_switch).astype(np.float32)
    P_VX[end_v:] = s_dirs * np.random.uniform(0.06, 0.10, size=n_switch).astype(np.float32)
    P_VY[end_v:] = np.random.uniform(-0.02, 0.02, size=n_switch).astype(np.float32)
    P_TYPE[end_v:] = 2
    P_AGE[end_v:] = np.random.uniform(0.0, 100.0, size=n_switch).astype(np.float32)

    for k in range(TRAIL_LEN):
        TRAIL_X[:, k] = P_X
        TRAIL_Y[:, k] = P_Y


init_particles()


def compute_ferroelectric_field(t_norm):
    """
    Computes razor-sharp non-linear saturated polarization fields,
    incandescent conductive domain wall filaments,
    flux-closure vortices, and dual-light specular relief normal mapping.
    """
    tau = 2.0 * np.pi * t_norm
    x, y = GX, GY

    # 1. External AC switching field E_ext(t)
    E_ext = 0.55 * np.sin(tau)

    # 2. Base crystal wavenumbers
    kx = np.pi / 3.2
    ky = np.pi / 1.8

    # Primary flux-closure potential components
    sin_kx = np.sin(kx * x)
    cos_ky = np.cos(ky * y)
    cos_kx = np.cos(kx * x)
    sin_ky = np.sin(ky * y)

    Px_raw = sin_kx * cos_ky
    Py_raw = -cos_kx * sin_ky

    # Vortex singularities at vertex centers
    Px_vort = np.zeros_like(x)
    Py_vort = np.zeros_like(y)
    for cx, cy, chiral in VORTEX_CENTERS:
        dx = x - cx
        dy = y - cy
        r_sq = dx**2 + dy**2 + 0.16
        Px_vort += chiral * (-dy / r_sq) * 0.55
        Py_vort += chiral * (dx / r_sq) * 0.55

    # Total polarization with switching needle modulation
    Px_tot = Px_raw + Px_vort + E_ext * 0.65 * np.cos(kx * x * 2.0)
    Py_tot = Py_raw + Py_vort + 0.3 * np.sin(tau + ky * y)

    # Sharp non-linear saturation via tanh (razor-sharp domain walls)
    Px_sat = np.tanh(Px_tot * 4.2)
    Py_sat = np.tanh(Py_tot * 4.2)

    # 3. Conductive Domain Wall Filaments
    # Peaks sharply where Px_sat or Py_sat crosses zero (domain boundaries)
    wall_x = np.exp(-0.5 * (np.abs(Px_raw) / 0.12)**2)
    wall_y = np.exp(-0.5 * (np.abs(Py_raw) / 0.12)**2)
    wall_metric = np.clip(wall_x + wall_y, 0.0, 1.0)

    # Bound charge density rho_b = -div(P)
    dPx_dy, dPx_dx = np.gradient(Px_sat)
    dPy_dy, dPy_dx = np.gradient(Py_sat)
    rho_b = -(dPx_dx + dPy_dy)

    # 4. Piezoelectric Surface Relief and Normal Mapping
    piezo_relief = (Px_sat**2 + Py_sat**2) * 1.4 + wall_metric * 1.8 + np.abs(rho_b) * 1.2
    gy, gx = np.gradient(piezo_relief)
    nx = -gx * 5.0
    ny = -gy * 5.0
    nz = np.ones_like(nx)
    norm_len = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    nx /= norm_len
    ny /= norm_len
    nz /= norm_len

    dot1 = np.clip(nx * LIGHT1_DIR[0] + ny * LIGHT1_DIR[1] + nz * LIGHT1_DIR[2], 0.0, 1.0)
    spec1 = dot1 ** 16.0

    dot2 = np.clip(nx * LIGHT2_DIR[0] + ny * LIGHT2_DIR[1] + nz * LIGHT2_DIR[2], 0.0, 1.0)
    spec2 = dot2 ** 22.0

    # 5. Color Synthesis
    # Base crystal void: Deep Bismuth Slate Obsidian
    r_bg, g_bg, b_bg = 7.0, 9.0, 18.0

    # Crisp block domains: Electric Sapphire (Px > 0) vs Neon Laser Coral (Px < 0)
    p_norm = np.clip(Px_sat * 0.5 + 0.5, 0.0, 1.0)

    # Sapphire domain (Px > 0)
    r_saph, g_saph, b_saph = 8.0, 60.0, 195.0
    # Coral domain (Px < 0)
    r_coral, g_coral, b_coral = 210.0, 20.0, 60.0

    domain_r = (1.0 - p_norm) * r_coral + p_norm * r_saph
    domain_g = (1.0 - p_norm) * g_coral + p_norm * g_saph
    domain_b = (1.0 - p_norm) * b_coral + p_norm * b_saph

    # Incandescent conductive wall conduction glow (Pearl White & Gold)
    conduction_glow = wall_metric * 0.95 + np.clip(np.abs(rho_b) * 0.4, 0.0, 0.8)

    r_out = domain_r + conduction_glow * 255.0 + spec2 * 255.0 + spec1 * 50.0
    g_out = domain_g + conduction_glow * 245.0 + spec2 * 225.0 + spec1 * 230.0
    b_out = domain_b + conduction_glow * 255.0 + spec2 * 120.0 + spec1 * 255.0

    rgb = np.stack([
        np.clip(r_out, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_out, 0, 255).astype(np.uint8)
    ], axis=-1)

    return rgb, Px_sat, Py_sat, wall_metric


def setup():
    py5.size(SIZE[0], SIZE[1])
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    print(f"[{WORK_NAME}] Initialized revised setup. Total frames: {TOTAL_FRAMES} @ {FPS} FPS")


def draw():
    frame = py5.frame_count

    if frame > TOTAL_FRAMES:
        finish_render()
        return

    t_norm = ((frame - 1) % TOTAL_FRAMES) / float(TOTAL_FRAMES)
    tau = 2.0 * np.pi * t_norm

    field_rgb, p_ux, p_uy, w_metric = compute_ferroelectric_field(t_norm)

    # Render background field via py5 image
    bg_img = py5.create_image_from_numpy(field_rgb, 'RGB')
    py5.image(bg_img, 0, 0, SIZE[0], SIZE[1])

    # Update particles and history trails
    global P_X, P_Y, P_VX, P_VY, P_TYPE, P_VORTEX_IDX, P_ANGLE, P_RADIUS, P_AGE, TRAIL_X, TRAIL_Y
    P_AGE += 1.0

    # Shift trail positions
    TRAIL_X[:, 1:] = TRAIL_X[:, :-1]
    TRAIL_X[:, 0] = P_X
    TRAIL_Y[:, 1:] = TRAIL_Y[:, :-1]
    TRAIL_Y[:, 0] = P_Y

    # Kinematics
    # Type 0: Conductive Domain Wall carriers (flow along polarization boundaries)
    is_wall = (P_TYPE == 0)
    grid_ix = np.clip(((P_X[is_wall] + 6.4) / 12.8 * (GRID_W - 1)).astype(np.int32), 0, GRID_W - 1)
    grid_iy = np.clip(((P_Y[is_wall] + 3.6) / 7.2 * (GRID_H - 1)).astype(np.int32), 0, GRID_H - 1)

    tangent_x = -p_uy[grid_iy, grid_ix] * 0.048
    tangent_y = p_ux[grid_iy, grid_ix] * 0.048

    P_X[is_wall] += tangent_x
    P_Y[is_wall] += tangent_y

    # Wrap wall particles and reset trail buffer
    wrap_wx = is_wall & ((P_X > 6.3) | (P_X < -6.3))
    if np.any(wrap_wx):
        new_wx = np.where(P_X[wrap_wx] > 6.3, -6.28, 6.28)
        P_X[wrap_wx] = new_wx
        TRAIL_X[wrap_wx, :] = new_wx[:, None]

    wrap_wy = is_wall & ((P_Y > 3.5) | (P_Y < -3.5))
    if np.any(wrap_wy):
        new_wy = np.where(P_Y[wrap_wy] > 3.5, -3.48, 3.48)
        P_Y[wrap_wy] = new_wy
        TRAIL_Y[wrap_wy, :] = new_wy[:, None]

    # Type 1: Vortex orbital charges
    is_vortex = (P_TYPE == 1)
    v_indices = P_VORTEX_IDX[is_vortex]
    for i, idx in enumerate(v_indices):
        cx, cy, chiral = VORTEX_CENTERS[idx]
        P_ANGLE[is_vortex][i] += chiral * (0.052 / (P_RADIUS[is_vortex][i] + 0.2))
        P_X[is_vortex][i] = cx + P_RADIUS[is_vortex][i] * np.cos(P_ANGLE[is_vortex][i])
        P_Y[is_vortex][i] = cy + P_RADIUS[is_vortex][i] * np.sin(P_ANGLE[is_vortex][i])

    # Type 2: Switching needle sparks
    is_switch = (P_TYPE == 2)
    P_X[is_switch] += P_VX[is_switch]
    P_Y[is_switch] += np.sin(P_X[is_switch] * 3.2 + tau * 4.0) * 0.014

    wrap_sx = is_switch & ((P_X > 6.3) | (P_X < -6.3))
    if np.any(wrap_sx):
        new_sx = np.where(P_X[wrap_sx] > 6.3, -6.25, 6.25)
        P_X[wrap_sx] = new_sx
        TRAIL_X[wrap_sx, :] = new_sx[:, None]

    # Fast Vectorized Drawing via py5.lines() and py5.points()
    # 1. Ribbon Trails (distance validated to guarantee zero wrap lines)
    for k in range(TRAIL_LEN - 1):
        alpha_factor = (TRAIL_LEN - 1 - k) / float(TRAIL_LEN)
        x0 = ((TRAIL_X[:, k + 1] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y0 = ((TRAIL_Y[:, k + 1] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
        x1 = ((TRAIL_X[:, k] + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
        y1 = ((TRAIL_Y[:, k] + 3.6) / 7.2 * SIZE[1]).astype(np.float32)

        dist_sq = (x1 - x0)**2 + (y1 - y0)**2
        valid = (dist_sq < (160.0**2)) & (x0 >= 0) & (x0 < SIZE[0]) & (y0 >= 0) & (y0 < SIZE[1]) & \
                (x1 >= 0) & (x1 < SIZE[0]) & (y1 >= 0) & (y1 < SIZE[1])

        # Type 0: Domain Wall Conduction (Incandescent Pearl White / Gold)
        m0 = valid & (P_TYPE == 0)
        if np.any(m0):
            lines0 = np.column_stack([x0[m0], y0[m0], x1[m0], y1[m0]])
            py5.stroke(255, 248, 195, int(185 * alpha_factor))
            py5.stroke_weight(2.2)
            py5.lines(lines0)

        # Type 1: Vortex Orbit (Electric Glacial Azure)
        m1 = valid & (P_TYPE == 1)
        if np.any(m1):
            lines1 = np.column_stack([x0[m1], y0[m1], x1[m1], y1[m1]])
            py5.stroke(0, 230, 255, int(170 * alpha_factor))
            py5.stroke_weight(2.0)
            py5.lines(lines1)

        # Type 2: Switching Sparks (Neon Laser Coral)
        m2 = valid & (P_TYPE == 2)
        if np.any(m2):
            lines2 = np.column_stack([x0[m2], y0[m2], x1[m2], y1[m2]])
            py5.stroke(255, 50, 90, int(170 * alpha_factor))
            py5.stroke_weight(2.0)
            py5.lines(lines2)

    # 2. Particle Heads
    sx = ((P_X + 6.4) / 12.8 * SIZE[0]).astype(np.float32)
    sy = ((P_Y + 3.6) / 7.2 * SIZE[1]).astype(np.float32)
    valid_head = (sx >= 0) & (sx < SIZE[0]) & (sy >= 0) & (sy < SIZE[1])

    m0_head = valid_head & (P_TYPE == 0)
    if np.any(m0_head):
        py5.stroke(255, 255, 255, 255)
        py5.stroke_weight(3.0)
        py5.points(np.column_stack([sx[m0_head], sy[m0_head]]))

    m1_head = valid_head & (P_TYPE == 1)
    if np.any(m1_head):
        py5.stroke(200, 250, 255, 250)
        py5.stroke_weight(2.8)
        py5.points(np.column_stack([sx[m1_head], sy[m1_head]]))

    m2_head = valid_head & (P_TYPE == 2)
    if np.any(m2_head):
        py5.stroke(255, 140, 160, 250)
        py5.stroke_weight(2.8)
        py5.points(np.column_stack([sx[m2_head], sy[m2_head]]))

    # Save frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{frame:04d}.png")
    py5.save_frame(frame_path)

    # Save preview image on representative frame
    if frame == 240:
        py5.save_frame(PREVIEW_FILE)
        print(f"[Preview Saved] Revised ferroelectric domain preview captured: {PREVIEW_FILE}")

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
        shutil.copyfile(OUTPUT_VIDEO, WORK_VIDEO)
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
    else:
        print(f"[Video Encoding Failed] ffmpeg error:\n{res.stderr}")

    os._exit(0)


if __name__ == "__main__":
    py5.run_sketch()

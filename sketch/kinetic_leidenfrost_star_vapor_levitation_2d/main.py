from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.8, 3.8, Nx, dtype=np.float32)
y_coords = np.linspace(-3.8 * (Ny / Nx), 3.8 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

R_grid = np.sqrt(X_grid**2 + Y_grid**2) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Directions for 3D Specular Liquid Chrome Shading
light1 = np.array([0.48, -0.62, 0.62], dtype=np.float32)
light1 /= np.linalg.norm(light1)

light2 = np.array([-0.55, 0.45, 0.70], dtype=np.float32)
light2 /= np.linalg.norm(light2)

# Droplet Base Radius (balanced for full star oscillation breathing room)
R0 = 1.48

# Lagrangian Particles: Marangoni Convection Tracers & Satellite Droplets
MAX_PARTICLES = 1600
particles = []


class LeidenfrostParticle:
    def __init__(self, px, py, ptype="marangoni", vx=0.0, vy=0.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "marangoni" or "satellite" or "vapor"
        self.vx = vx
        self.vy = vy

        if ptype == "marangoni":
            self.life = random.uniform(90.0, 240.0)
            self.radius = random.uniform(1.5, 3.0)
        elif ptype == "satellite":
            self.life = random.uniform(120.0, 280.0)
            self.radius = random.uniform(2.4, 4.4)
        else:  # vapor wisp
            self.life = random.uniform(45.0, 110.0)
            self.radius = random.uniform(1.2, 2.4)

        self.max_life = self.life

    def update(self, field_vx, field_vy, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "marangoni":
            # Swirled by internal thermo-capillary convection roll velocity
            self.px += field_vx * 4.4 * dt
            self.py += field_vy * 4.4 * dt
        elif self.ptype == "satellite":
            # Levitating micro-satellite pearl drifting outward, damped by vapor shear
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.984
            self.vy *= 0.984
        else:
            # Evaporating vapor wisp rising and dissipating
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.955
            self.vy *= 0.955

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 100
            or self.px < -100
            or self.py > py5.height + 100
            or self.py < -100
        )


def eval_r_star(theta, t):
    """Evaluates the analytical star boundary radius at angle theta and time t."""
    w0 = 0.42
    w3 = w0 * np.sqrt(30)
    w4 = w0 * np.sqrt(72)
    w5 = w0 * np.sqrt(140)
    w6 = w0 * np.sqrt(240)
    w7 = w0 * np.sqrt(378)

    rot3 = 0.16 * t
    rot4 = -0.13 * t
    rot5 = 0.20 * t
    rot6 = -0.10 * t
    rot7 = 0.15 * t

    a3 = 0.13 + 0.08 * np.cos(0.35 * t)
    a4 = 0.16 + 0.10 * np.cos(0.28 * t + 1.2)
    a5 = 0.15 + 0.09 * np.sin(0.40 * t + 0.6)
    a6 = 0.11 + 0.07 * np.cos(0.32 * t + 2.1)
    a7 = 0.06 + 0.04 * np.sin(0.48 * t)

    m3_term = a3 * np.cos(3.0 * (theta - rot3)) * np.cos(w3 * t)
    m4_term = a4 * np.cos(4.0 * (theta - rot4)) * np.cos(w4 * t + 0.8)
    m5_term = a5 * np.cos(5.0 * (theta - rot5)) * np.cos(w5 * t - 0.5)
    m6_term = a6 * np.cos(6.0 * (theta - rot6)) * np.cos(w6 * t + 1.4)
    m7_term = a7 * np.cos(7.0 * (theta - rot7)) * np.cos(w7 * t - 1.1)

    xi = m3_term + m4_term + m5_term + m6_term + m7_term
    xi_sharp = xi + 0.32 * np.sign(xi) * (np.abs(xi)**1.4)
    return float(R0 * (1.0 + xi_sharp))


def compute_leidenfrost_fields(frame):
    """
    Computes 2D hydrodynamic and thermo-capillary fields of the Leidenfrost star:
    - Polygonal star droplet boundary oscillation (Rayleigh-Lamb capillary modes m=3..7)
    - Substrate thermal radiation and vapor layer cushion
    - Thin-film optical interference fringes (Newton's rings / Fabry-Perot)
    - Internal Marangoni toroidal convection roll velocities and vorticity streamlines
    - 3D surface height profile and Blinn-Phong specular reflections
    """
    t = frame / 60.0  # seconds

    # 1. Polygonal Star Droplet Oscillation (Rayleigh-Lamb Capillary Modes)
    w0 = 0.42
    w3 = w0 * np.sqrt(3 * 2 * 5)   # ~2.30 rad/s
    w4 = w0 * np.sqrt(4 * 3 * 6)   # ~3.56 rad/s
    w5 = w0 * np.sqrt(5 * 4 * 7)   # ~4.97 rad/s
    w6 = w0 * np.sqrt(6 * 5 * 8)   # ~6.51 rad/s
    w7 = w0 * np.sqrt(7 * 6 * 9)   # ~8.17 rad/s

    # Azimuthal mode precession speeds
    rot3 = 0.16 * t
    rot4 = -0.13 * t
    rot5 = 0.20 * t
    rot6 = -0.10 * t
    rot7 = 0.15 * t

    # Dynamic modal amplitudes evolving across 18 seconds
    a3 = 0.13 + 0.08 * np.cos(0.35 * t)
    a4 = 0.16 + 0.10 * np.cos(0.28 * t + 1.2)
    a5 = 0.15 + 0.09 * np.sin(0.40 * t + 0.6)
    a6 = 0.11 + 0.07 * np.cos(0.32 * t + 2.1)
    a7 = 0.06 + 0.04 * np.sin(0.48 * t)

    # Azimuthal harmonic lobes
    m3_term = a3 * np.cos(3.0 * (Theta_grid - rot3)) * np.cos(w3 * t)
    m4_term = a4 * np.cos(4.0 * (Theta_grid - rot4)) * np.cos(w4 * t + 0.8)
    m5_term = a5 * np.cos(5.0 * (Theta_grid - rot5)) * np.cos(w5 * t - 0.5)
    m6_term = a6 * np.cos(6.0 * (Theta_grid - rot6)) * np.cos(w6 * t + 1.4)
    m7_term = a7 * np.cos(7.0 * (Theta_grid - rot7)) * np.cos(w7 * t - 1.1)

    xi = m3_term + m4_term + m5_term + m6_term + m7_term
    # Physical tip sharpening (cusped star lobes at maximum expansion)
    xi_sharp = xi + 0.32 * np.sign(xi) * (np.abs(xi)**1.4)
    R_star = R0 * (1.0 + xi_sharp)

    # Normalized radial coordinate relative to oscillating droplet rim
    r_norm = R_grid / (R_star + 1e-4)

    # 2. Droplet Bulk Interior & Dual-Layer Meniscus Rim
    # Smooth sigmoid transition prevents stair-casing at 4K
    bulk_droplet = 1.0 / (1.0 + np.exp(np.clip(28.0 * (r_norm - 1.0), -22.0, 22.0)))

    # Dual-layer meniscus rim: Razor-sharp core + luminous golden halo
    rim_dist = np.abs(r_norm - 1.0)
    rim_core = np.exp(- (rim_dist**2) / (2.0 * (0.016**2)))
    rim_halo = np.exp(- (rim_dist**2) / (2.0 * (0.052**2)))

    # 3. Substrate Thermal Glow & Vapor Cushion Optical Interference (Newton's Rings)
    # Superheated substrate background thermal radiation
    substrate_thermal = np.exp(- (R_grid**2) / 6.5) * (1.0 + 0.14 * np.cos(R_grid * 3.6 - 1.4 * t))

    # Vapor gap thickness under levitating droplet: sub-micron cushion
    vapor_gap = 1.0 + 0.55 * (r_norm**2) + 0.22 * np.cos(2.2 * t) * (1.0 - 0.4 * r_norm)
    # Thin-film optical interference phase (Newton's rings / Fabry-Perot)
    film_phase = 28.0 * vapor_gap + 2.5 * t
    fringe_violet = np.maximum(0.0, np.cos(film_phase))
    fringe_cyan = np.maximum(0.0, np.cos(film_phase - 2.094))
    fringe_gold = np.maximum(0.0, np.cos(film_phase - 4.188))
    # Concentric multi-ring interference envelope around the cushion perimeter
    cushion_envelope = (
        np.exp(- ((r_norm - 1.02)**2) / (2.0 * (0.15**2)))
        * (1.0 + 0.35 * np.cos(18.0 * (r_norm - 1.0)))
    )

    # 4. Internal Marangoni Toroidal Convection Roll Velocity Field
    # Vertical/radial thermal gradient generates surface-tension driven convective rolls
    roll_modes = np.sin(4.0 * (Theta_grid - 0.22 * t))
    u_radial = 1.8 * roll_modes * np.sin(np.pi * np.clip(r_norm, 0.0, 1.0)) * bulk_droplet
    u_azimuthal = -2.2 * np.cos(4.0 * (Theta_grid - 0.22 * t)) * np.cos(np.pi * np.clip(r_norm, 0.0, 1.0)) * bulk_droplet

    v_marangoni_x = (u_radial * np.cos(Theta_grid) - u_azimuthal * np.sin(Theta_grid))
    v_marangoni_y = (u_radial * np.sin(Theta_grid) + u_azimuthal * np.cos(Theta_grid))

    # Convective vorticity pattern inside liquid core
    vorticity_field = np.sin(6.0 * (Theta_grid - 0.18 * t)) * np.sin(2.0 * np.pi * np.clip(r_norm, 0.0, 1.0)) * bulk_droplet

    # 5. 3D Specular Surface Profile & Blinn-Phong Liquid Chrome Highlights
    # Dome-like droplet profile with undulating star lobes
    h_core = np.sqrt(np.maximum(0.0, 1.0 - np.clip(r_norm, 0.0, 1.0)**2)) * bulk_droplet
    H_surface = 0.95 * h_core + 0.22 * xi_sharp * bulk_droplet

    grad_y, grad_x = np.gradient(H_surface, dy, dx)
    norm_denom = np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    Nx_surf = -grad_x / norm_denom
    Ny_surf = -grad_y / norm_denom
    Nz_surf = 1.0 / norm_denom

    # Specular reflections for dual light sources
    view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
    h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

    spec1 = np.maximum(0.0, Nx_surf * h1[0] + Ny_surf * h1[1] + Nz_surf * h1[2])**32 * bulk_droplet
    spec2 = np.maximum(0.0, Nx_surf * h2[0] + Ny_surf * h2[1] + Nz_surf * h2[2])**24 * bulk_droplet

    return (
        bulk_droplet,
        rim_core,
        rim_halo,
        substrate_thermal,
        cushion_envelope,
        fringe_violet,
        fringe_cyan,
        fringe_gold,
        v_marangoni_x,
        v_marangoni_y,
        vorticity_field,
        spec1,
        spec2,
        t,
    )


def render_leidenfrost_canvas(
    bulk_droplet,
    rim_core,
    rim_halo,
    substrate_thermal,
    cushion_envelope,
    fringe_violet,
    fringe_cyan,
    fringe_gold,
    vorticity_field,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Substrate Obsidian Void & Thermal Infrared Charcoal (#030206, #0c0716, #180f2d)
    - 30% Oscillating Liquid Core Cobalt, Glacial Azure & Marangoni Indigo (#1e3a8a, #0284c7, #38bdf8)
    - 10% Incandescent Vapor Cushion White-Gold & Thin-Film Iridescent Violet (#fffbeb, #fef08a, #e879f9)
    """
    # 1. Background 60%: Superheated Substrate Obsidian Void & Infrared Glow
    r_bg = 3.0 + substrate_thermal * 38.0
    g_bg = 2.0 + substrate_thermal * 14.0
    b_bg = 6.0 + substrate_thermal * 45.0

    # 2. Secondary 30%: Oscillating Liquid Core Cobalt, Glacial Azure & Indigo
    # Deep cobalt-indigo bulk interior with convective vorticity streamlines
    core_indigo = bulk_droplet * 0.90
    r_core = core_indigo * 18.0 + np.maximum(0.0, vorticity_field) * 10.0
    g_core = core_indigo * 64.0 + np.maximum(0.0, vorticity_field) * 38.0
    b_core = core_indigo * 165.0 + np.maximum(0.0, vorticity_field) * 65.0

    # Specular liquid chrome highlights: Cool glacial azure and warm gold reflections
    spec_r = spec1 * 120.0 + spec2 * 255.0
    spec_g = spec1 * 210.0 + spec2 * 225.0
    spec_b = spec1 * 255.0 + spec2 * 140.0

    # Composite liquid body
    r_total = r_bg * (1.0 - bulk_droplet) + (r_core + spec_r) * bulk_droplet
    g_total = g_bg * (1.0 - bulk_droplet) + (g_core + spec_g) * bulk_droplet
    b_total = b_bg * (1.0 - bulk_droplet) + (b_core + spec_b) * bulk_droplet

    # 3. Accent 10%: Meniscus Rim & Vapor Cushion Thin-Film Iridescent Fringes
    # Thin-film interference colors at the vapor cushion gap (Newton's rings)
    film_r = cushion_envelope * (fringe_violet * 160.0 + fringe_gold * 240.0)
    film_g = cushion_envelope * (fringe_cyan * 200.0 + fringe_gold * 180.0)
    film_b = cushion_envelope * (fringe_violet * 230.0 + fringe_cyan * 255.0)

    # Refined Dual-Layer Meniscus Rim: Sharp caustic core + warm golden halo
    rim_r = rim_core * 240.0 + rim_halo * 115.0
    rim_g = rim_core * 230.0 + rim_halo * 85.0
    rim_b = rim_core * 210.0 + rim_halo * 180.0

    # Final additive composite
    r_final = np.clip(r_total + film_r + rim_r, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_total + film_g + rim_g, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_total + film_b + rim_b, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute hydrodynamic and thermo-capillary fields
    (
        bulk_droplet,
        rim_core,
        rim_halo,
        substrate_thermal,
        cushion_envelope,
        fringe_violet,
        fringe_cyan,
        fringe_gold,
        v_marangoni_x,
        v_marangoni_y,
        vorticity_field,
        spec1,
        spec2,
        t,
    ) = compute_leidenfrost_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_leidenfrost_canvas(
        bulk_droplet,
        rim_core,
        rim_halo,
        substrate_thermal,
        cushion_envelope,
        fringe_violet,
        fringe_cyan,
        fringe_gold,
        vorticity_field,
        spec1,
        spec2,
    )

    # 3. Blit upscaled pixel buffer to 4K canvas
    img = py5.create_image(Nx, Ny, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = pixel_buffer
        img.update_np_pixels()
    else:
        a = pixel_buffer[..., 0].astype(np.int32)
        r = pixel_buffer[..., 1].astype(np.int32)
        g = pixel_buffer[..., 2].astype(np.int32)
        b = pixel_buffer[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # 4. Lagrangian Particle Spawning
    canvas_center_x = py5.width / 2.0
    canvas_center_y = py5.height / 2.0
    scale_factor = py5.height / (y_coords[-1] - y_coords[0])

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(55, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()
            theta = random.uniform(0.0, 2.0 * np.pi)
            local_r = eval_r_star(theta, t)

            if roll < 0.62:
                # Internal Marangoni convection tracer
                r_pos = random.uniform(0.12, 0.88) * local_r * scale_factor
                px = canvas_center_x + np.cos(theta) * r_pos
                py = canvas_center_y + np.sin(theta) * r_pos
                particles.append(LeidenfrostParticle(px, py, ptype="marangoni"))
            elif roll < 0.84:
                # Rayleigh-Plateau pinch-off micro-satellite droplet
                r_pos = local_r * scale_factor
                px = canvas_center_x + np.cos(theta) * r_pos
                py = canvas_center_y + np.sin(theta) * r_pos
                # Ejected tangentially and radially outward
                eject_speed = random.uniform(2.8, 6.5)
                tangent_angle = theta + np.pi / 2.0 + random.uniform(-0.35, 0.35)
                vx = np.cos(theta) * (eject_speed * 0.65) + np.cos(tangent_angle) * (eject_speed * 0.75)
                vy = np.sin(theta) * (eject_speed * 0.65) + np.sin(tangent_angle) * (eject_speed * 0.75)
                particles.append(LeidenfrostParticle(px, py, ptype="satellite", vx=vx, vy=vy))
            else:
                # Evaporating vapor jet wisp
                r_pos = (local_r + random.uniform(0.06, 0.32)) * scale_factor
                px = canvas_center_x + np.cos(theta) * r_pos
                py = canvas_center_y + np.sin(theta) * r_pos
                v_speed = random.uniform(1.4, 3.8)
                vx = np.cos(theta) * v_speed + random.uniform(-0.55, 0.55)
                vy = np.sin(theta) * v_speed + random.uniform(-0.55, 0.55)
                particles.append(LeidenfrostParticle(px, py, ptype="vapor", vx=vx, vy=vy))

    # 5. Advect and Render Lagrangian Particles
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        gx = int(np.clip(((p.px / py5.width) * (Nx - 1)), 0, Nx - 1))
        gy = int(np.clip(((p.py / py5.height) * (Ny - 1)), 0, Ny - 1))

        f_vx = float(v_marangoni_x[gy, gx])
        f_vy = float(v_marangoni_y[gy, gx])

        p.update(f_vx, f_vy)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.ptype == "satellite":
                # Micro-satellite pearl: Incandescent solar white-gold (#fffbeb, #fbbf24)
                cr, cg, cb = 255, 235, 160
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.38))
                py5.circle(p.px, p.py, p.radius * 3.8)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(cr, cg, cb, int(alpha * 0.85))
                py5.stroke_weight(1.8)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "marangoni":
                # Internal Marangoni convection tracer: Glacial azure & electric cyan (#38bdf8, #06b6d4)
                cr, cg, cb = 30, 210, 255
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(220, 245, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.9)
                py5.stroke(cr, cg, cb, int(alpha * 0.75))
                py5.stroke_weight(1.5)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            else:
                # Vapor wisp: Iridescent violet & lavender (#e879f9)
                cr, cg, cb = 220, 130, 250
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.22))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(250, 220, 255, int(alpha * 0.75))
                py5.circle(p.px, p.py, p.radius * 1.1)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # 6. Safety check: fail-safe blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 7. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Particles: {len(particles)}")

    # 8. Finalize render on completion
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        output_mp4 = SKETCH_DIR / "output.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", str(mp4_path),
        ], check=True)
        shutil.copyfile(mp4_path, output_mp4)

        # Save preview snapshot from midpoint
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        import os
        os._exit(1)


py5.run_sketch()

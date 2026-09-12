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

# Spatial Simulation Grid (16:9 aspect ratio, horizontal jet domain)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.6, 3.6, Nx, dtype=np.float32)
y_coords = np.linspace(-2.025, 2.025, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Directions for 3D Specular Liquid Chrome Shading
light1 = np.array([0.52, -0.58, 0.62], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.66], dtype=np.float32)
light2 /= np.linalg.norm(light2)

# Lagrangian Particles: Internal Vortex Ring Tracers & Capillary Spray Droplets
MAX_PARTICLES = 1600
particles = []


class CapillaryParticle:
    def __init__(self, px, py, ptype="internal", vx=0.0, vy=0.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "internal", "spray", or "satellite"
        self.vx = vx
        self.vy = vy

        if ptype == "internal":
            self.life = random.uniform(80.0, 220.0)
            self.radius = random.uniform(1.3, 2.6)
        elif ptype == "spray":
            self.life = random.uniform(50.0, 130.0)
            self.radius = random.uniform(1.6, 3.2)
        else:  # satellite micro-droplet
            self.life = random.uniform(100.0, 260.0)
            self.radius = random.uniform(2.0, 4.0)

        self.max_life = self.life

    def update(self, u_fluid_x, u_fluid_y, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "internal":
            # Advected by internal liquid jet velocity
            self.px += u_fluid_x * 4.2 * dt
            self.py += u_fluid_y * 4.2 * dt
        elif self.ptype == "spray":
            # High-velocity radial spray bursting from pinch-off singularity
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.965
            self.vy *= 0.965
        else:
            # Satellite micro-pearl traveling along jet axis with slight deceleration
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx = max(2.5, self.vx * 0.992)
            self.vy *= 0.94

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


def compute_capillary_pinchoff_fields(frame):
    """
    Computes 2D fluid dynamics of Rayleigh-Plateau capillary jet pinch-off:
    - Inflowing cylindrical liquid jet undergoing capillary necking instability
    - Finite-time pinch-off singularity with Eggers self-similar profile
    - Primary prolate-oblate oscillating droplets and secondary satellite beads
    - Capillary surface recoil wave ripples and 3D Blinn-Phong chrome shading
    """
    t = frame / 60.0  # seconds

    # 1. Jet Kinematics & Wavelength Modulation
    U_jet = 1.35  # streaming velocity
    lambda_rp = 3.25  # Rayleigh-Plateau wavelength
    k_rp = 2.0 * np.pi / lambda_rp

    # Phase of capillary wave traveling along jet
    phase_jet = k_rp * (X_grid - U_jet * t)

    # Spatial instability growth: jet starts uniform on left (X < -2.2) and pinches near X ~ 0
    growth_envelope = 1.0 / (1.0 + np.exp(- 2.4 * (X_grid + 0.6)))

    # Base jet radius
    R0 = 0.52

    # Non-linear necking profile: sinusoidal at onset, steepening into narrow cusped necks
    wave_fund = np.cos(phase_jet)
    wave_harm2 = 0.42 * np.cos(2.0 * phase_jet + 0.5)
    wave_harm3 = 0.18 * np.cos(3.0 * phase_jet - 0.7)
    wave_combined = (wave_fund + wave_harm2 + wave_harm3) / 1.6

    # Necking depth: reaches zero in breakup region
    neck_depth = np.clip(growth_envelope * 1.25, 0.0, 1.1)
    # Physical local radius of jet / drop filament
    R_raw = R0 * (1.0 + 0.85 * growth_envelope * wave_combined - neck_depth * (1.0 - wave_combined))

    # 2. Downstream Droplet Detachment & Satellite Formation (X > 0.0)
    # Droplet quadrupole oscillation: prolate-oblate mode
    omega_quad = 5.2
    quad_phase = omega_quad * t - 1.8 * X_grid
    quadrupole_mode = 0.28 * np.cos(quad_phase)
    downstream_weight = 1.0 / (1.0 + np.exp(- 4.0 * (X_grid - 0.2)))
    R_mod = R_raw * (1.0 + downstream_weight * quadrupole_mode * np.cos(2.0 * np.arctan2(Y_grid, X_grid + 1e-4)))

    # Smooth satellite micro-droplet bead formation between primary drops
    sat_center_phase = phase_jet - np.pi
    sat_envelope = 1.0 / (1.0 + np.exp(- 3.0 * (X_grid - 0.0)))
    R_satellite = 0.15 * np.exp(- ((np.sin(sat_center_phase / 2.0))**2) / 0.035) * sat_envelope

    # Effective radius combining jet/droplet stream and satellite bead
    R_effective = np.maximum(0.0, np.maximum(R_mod, R_satellite))

    # Fluid existence factor: Strictly 0 where fluid has broken to zero, smooth quadratic ease-in
    fluid_exist = np.clip((R_effective - 0.025) / 0.045, 0.0, 1.0)**2

    # Fluid interior mask: |Y| <= R_effective
    r_dist = np.abs(Y_grid)
    fluid_mask = 1.0 / (1.0 + np.exp(np.clip(28.0 * (r_dist - R_effective), -22.0, 22.0))) * fluid_exist

    # Sharp luminous capillary meniscus interface (active ONLY where fluid exists)
    interface_dist = np.abs(r_dist - R_effective)
    interface_core = np.exp(- (interface_dist**2) / (2.0 * (0.018**2))) * fluid_exist
    interface_halo = np.exp(- (interface_dist**2) / (2.0 * (0.058**2))) * fluid_exist

    # 3. Finite-Time Pinch-Off Singularity Hotspots (compact Gaussian burst at snapping necks)
    neck_pinch_zone = np.exp(- (R_effective / 0.08)**2) * fluid_exist
    singularity_zones = (
        np.exp(- (interface_dist**2) / 0.012)
        * neck_pinch_zone
        * np.exp(- ((X_grid - 0.2)**2) / 0.6)
    )

    # Capillary recoil ripples radiating from snapped necks
    recoil_waves = (
        np.cos(18.0 * (X_grid - U_jet * t) - 8.0 * t)
        * np.exp(- (r_dist**2) / 0.25)
        * fluid_mask
        * (1.0 / (1.0 + np.exp(- 4.0 * (X_grid + 0.8))))
    )

    # 4. Internal Fluid Velocity Field
    # Longitudinal jet velocity with radial convergence into neck and expansion into drops
    u_jet_x = np.where(
        fluid_mask > 0.05,
        U_jet * (1.0 + 0.4 * growth_envelope * np.sin(phase_jet)),
        0.0
    )
    u_jet_y = np.where(
        fluid_mask > 0.05,
        -0.8 * growth_envelope * np.sin(phase_jet) * (Y_grid / (R_effective + 1e-4)),
        0.0
    )

    # 5. 3D Surface Profile & Blinn-Phong Specular Chrome Highlights
    H_fluid = np.sqrt(np.maximum(0.0, R_effective**2 - Y_grid**2)) * fluid_mask
    H_fluid += 0.08 * recoil_waves

    grad_y, grad_x = np.gradient(H_fluid, dy, dx)
    norm_denom = np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    Nx_surf = -grad_x / norm_denom
    Ny_surf = -grad_y / norm_denom
    Nz_surf = 1.0 / norm_denom

    view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
    h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

    spec1 = np.maximum(0.0, Nx_surf * h1[0] + Ny_surf * h1[1] + Nz_surf * h1[2])**32 * fluid_mask
    spec2 = np.maximum(0.0, Nx_surf * h2[0] + Ny_surf * h2[1] + Nz_surf * h2[2])**24 * fluid_mask

    return (
        fluid_mask,
        interface_core,
        interface_halo,
        singularity_zones,
        recoil_waves,
        spec1,
        spec2,
        u_jet_x,
        u_jet_y,
        t,
    )


def render_capillary_canvas(
    fluid_mask,
    interface_core,
    interface_halo,
    singularity_zones,
    recoil_waves,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Cryogenic Vacuum Obsidian Void & Deep Liquid Chromium (#020206, #080c18, #101828)
    - 30% Oscillating Liquid Mercury & Electric Glacial Cyan (#06b6d4, #38bdf8, #0284c7)
    - 10% Incandescent Singularity Pinch-Off Diamond-White & Solar Gold Caustics (#ffffff, #fef08a, #fbbf24)
    """
    # 1. Background 60%: Cryogenic Vacuum Obsidian Void & Subtle Radiative Glow
    r_bg = 2.0 + np.exp(- (Y_grid**2) / 3.2) * 6.0
    g_bg = 3.0 + np.exp(- (Y_grid**2) / 3.2) * 12.0
    b_bg = 8.0 + np.exp(- (Y_grid**2) / 3.2) * 32.0

    # 2. Secondary 30%: Liquid Mercury Core & Electric Glacial Cyan Ribbon
    core_intensity = fluid_mask * 0.92
    r_core = core_intensity * 14.0 + np.maximum(0.0, recoil_waves) * 10.0
    g_core = core_intensity * 75.0 + np.maximum(0.0, recoil_waves) * 35.0
    b_core = core_intensity * 175.0 + np.maximum(0.0, recoil_waves) * 65.0

    # Liquid Chrome specular reflections: Cool glacial azure and crystal highlights
    spec_r = spec1 * 140.0 + spec2 * 255.0
    spec_g = spec1 * 220.0 + spec2 * 235.0
    spec_b = spec1 * 255.0 + spec2 * 160.0

    # Composite liquid body
    r_fluid = r_bg * (1.0 - fluid_mask) + (r_core + spec_r) * fluid_mask
    g_fluid = g_bg * (1.0 - fluid_mask) + (g_core + spec_g) * fluid_mask
    b_fluid = b_bg * (1.0 - fluid_mask) + (b_core + spec_b) * fluid_mask

    # 3. Accent 10%: Incandescent Capillary Meniscus Interface & Pinch-Off Singularities
    # Dual-layer meniscus interface: Sharp electric cyan core + luminous gold halo
    r_interface = interface_core * 210.0 + interface_halo * 125.0
    g_interface = interface_core * 245.0 + interface_halo * 95.0
    b_interface = interface_core * 255.0 + interface_halo * 190.0

    # Blinding Diamond-White & Gold Pinch-Off Singularity Flashes (pure localized burst)
    flash_intensity = singularity_zones * 2.5
    r_flash = flash_intensity * 255.0
    g_flash = flash_intensity * 245.0
    b_flash = flash_intensity * 200.0

    # Final Additive Composite
    r_final = np.clip(r_fluid + r_interface + r_flash, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_fluid + g_interface + g_flash, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_fluid + b_interface + b_flash, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute capillary pinch-off fields
    (
        fluid_mask,
        interface_core,
        interface_halo,
        singularity_zones,
        recoil_waves,
        spec1,
        spec2,
        u_jet_x,
        u_jet_y,
        t,
    ) = compute_capillary_pinchoff_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_capillary_canvas(
        fluid_mask,
        interface_core,
        interface_halo,
        singularity_zones,
        recoil_waves,
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
    x_min, x_max = x_coords[0], x_coords[-1]
    y_min, y_max = y_coords[0], y_coords[-1]

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(55, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.58:
                # Internal fluid tracer advecting inside jet/droplets
                x_spawn = random.uniform(x_min, x_max)
                y_spawn = random.uniform(-0.45, 0.45)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_spawn - y_min) / (y_max - y_min)) * py5.height
                particles.append(CapillaryParticle(px, py_screen, ptype="internal"))

            elif roll < 0.82:
                # Capillary spray droplet bursting radially from pinch-off zone (X ~ -0.2 to 1.2)
                x_pinch = random.uniform(-0.4, 1.2)
                y_pinch = random.uniform(-0.15, 0.15)
                px = ((x_pinch - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_pinch - y_min) / (y_max - y_min)) * py5.height
                angle = random.uniform(0.0, 2.0 * np.pi)
                spray_speed = random.uniform(3.5, 8.5)
                vx = np.cos(angle) * spray_speed + 2.0  # forward drift
                vy = np.sin(angle) * spray_speed
                particles.append(CapillaryParticle(px, py_screen, ptype="spray", vx=vx, vy=vy))

            else:
                # Satellite micro-droplet bead traveling downstream
                x_spawn = random.uniform(0.0, 2.5)
                y_spawn = random.gauss(0.0, 0.05)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((y_spawn - y_min) / (y_max - y_min)) * py5.height
                particles.append(CapillaryParticle(px, py_screen, ptype="satellite", vx=random.uniform(4.0, 6.5)))

    # 5. Advect and Render Lagrangian Particles
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        norm_x = p.px / py5.width
        norm_y = p.py / py5.height

        gx = int(np.clip(norm_x * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip(norm_y * (Ny - 1), 0, Ny - 1))

        u_fx = float(u_jet_x[gy, gx])
        u_fy = float(u_jet_y[gy, gx])

        p.update(u_fx, u_fy)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.ptype == "spray":
                # Radial capillary spray: Incandescent diamond-white & solar gold (#ffffff, #fbbf24)
                cr, cg, cb = 255, 235, 170
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.40))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(cr, cg, cb, int(alpha * 0.85))
                py5.stroke_weight(1.8)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "internal":
                # Internal fluid tracer: Electric glacial cyan & azure (#06b6d4, #38bdf8)
                cr, cg, cb = 25, 215, 255
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.8)
                py5.fill(225, 245, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)
                py5.stroke(cr, cg, cb, int(alpha * 0.72))
                py5.stroke_weight(1.4)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            else:
                # Satellite micro-pearl: Warm amber & violet halo (#fbbf24, #e879f9)
                cr, cg, cb = 255, 210, 120
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.35))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(cr, cg, cb, int(alpha * 0.80))
                py5.stroke_weight(1.6)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

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


if __name__ == "__main__":
    py5.run_sketch()

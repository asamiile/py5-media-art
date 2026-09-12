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

# Spatial Simulation Grid (16:9 aspect ratio, polar circumpolar domain)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.6, 3.6, Nx, dtype=np.float32)
y_coords = np.linspace(-2.025, 2.025, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Polar coordinates centered at origin (Arctic Polar Vortex)
R_rad = np.sqrt(X_grid**2 + Y_grid**2)
Theta = np.arctan2(Y_grid, X_grid)

# Rossby wave parameters
m_wave = 5  # pentagonal planetary wave number
c_phase = 0.18  # slow eastward phase precession speed
omega_jet = 0.95  # rapid jet stream advection speed
R0 = 1.25  # mean jet stream radius

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Directions for 3D Specular Geopotential Relief Shading
light1 = np.array([0.55, -0.55, 0.62], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.52, 0.69], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Jet Streak Air Parcels, Cyclonic Eye Tracers & Polar Vortex Swirlers
MAX_PARTICLES = 1600
particles = []


class AtmosphericParcel:
    def __init__(self, px, py, ptype="jet", vx=0.0, vy=0.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "jet" (jet streak parcel), "cyclone" (trough eddy), "polar" (vortex core)
        self.vx = vx
        self.vy = vy

        if ptype == "jet":
            self.life = random.uniform(90.0, 220.0)
            self.radius = random.uniform(1.2, 2.4)
        elif ptype == "cyclone":
            self.life = random.uniform(70.0, 160.0)
            self.radius = random.uniform(1.8, 3.2)
        else:  # polar vortex core
            self.life = random.uniform(100.0, 260.0)
            self.radius = random.uniform(1.0, 2.0)

        self.max_life = self.life

    def update(self, u_fluid_x, u_fluid_y, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "jet":
            # Accelerated by jet stream advection field
            self.px += u_fluid_x * 4.4 * dt
            self.py += u_fluid_y * 4.4 * dt
        elif self.ptype == "cyclone":
            # Cyclonic orbit in cut-off cold pool
            self.px += (u_fluid_x * 3.8 + self.vx) * dt
            self.py += (u_fluid_y * 3.8 + self.vy) * dt
            self.vx *= 0.96
            self.vy *= 0.96
        else:
            # Polar core slow swirling
            self.px += u_fluid_x * 2.2 * dt
            self.py += u_fluid_y * 2.2 * dt

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


def compute_rossby_wave_fields(frame):
    """
    Computes 2D fluid dynamics of planetary Rossby wave jet stream meanders:
    - Pentagonal (m=5) baroclinic Rossby wave oscillation and slow eastward phase precession
    - Multi-core nested isotach stream-tubes and jet-streak wind acceleration
    - Arctic polar vortex core spiral potential vorticity bands
    - Subtropical anticyclonic blocking ridges and cut-off cyclonic cold pool eddies
    - 3D Blinn-Phong specular geopotential height relief shading
    - Internal atmospheric wind velocity vector fields (u_x, u_y)
    """
    t = frame / 60.0  # seconds

    # 1. Rossby Wave Kinematics & Meander Geometry
    phase_rossby = m_wave * (Theta - c_phase * t)

    # Dynamic breathing of Rossby wave amplitudes (baroclinic life cycle)
    wave_amp1 = 0.38 + 0.08 * np.sin(0.8 * t)
    wave_amp2 = 0.14 * np.cos(2.0 * phase_rossby + 0.5)
    wave_amp3 = 0.06 * np.cos(3.0 * phase_rossby - 0.7)

    # Meandering jet core radius R_jet(theta, t)
    R_jet = R0 + wave_amp1 * np.cos(phase_rossby) + wave_amp2 + wave_amp3
    dist_to_jet = np.abs(R_rad - R_jet)

    # 2. Multi-Filament Isotach Stream-Tubes & Jet-Streak Acceleration
    iso_core = np.exp(- (dist_to_jet**2) / (2.0 * (0.045**2)))
    iso_inner = np.exp(- ((dist_to_jet - 0.085)**2) / (2.0 * (0.035**2)))
    iso_outer = np.exp(- ((dist_to_jet - 0.165)**2) / (2.0 * (0.040**2)))

    V_envelope = np.exp(- (dist_to_jet**2) / (2.0 * (0.24**2)))
    streak_factor = 1.0 + 0.38 * np.cos(phase_rossby + 0.7)

    # 3. Polar Vortex & Subtropical Circulation
    # Arctic polar core (R < R_jet): Pinwheel spiral potential vorticity bands
    polar_interior = 1.0 / (1.0 + np.exp(np.clip(16.0 * (R_rad - R_jet + 0.1), -20.0, 20.0)))
    polar_spirals = (
        np.cos(4.0 * Theta - 10.0 * R_rad - 1.6 * t)
        * np.exp(- (R_rad**2) / 0.75)
        * polar_interior
        * 0.45
    )

    # Subtropical exterior (R > R_jet): Anticyclonic blocking ridges & radiating cirrus waves
    subtropical_exterior = 1.0 / (1.0 + np.exp(np.clip(-16.0 * (R_rad - R_jet - 0.1), -20.0, 20.0)))
    subtropical_ripples = (
        np.cos(m_wave * Theta + 8.0 * R_rad - 1.2 * t)
        * np.exp(- ((R_rad - 1.8)**2) / 1.2)
        * subtropical_exterior
        * 0.35
    )

    # Pinched-off cut-off cyclonic cold pool eddies in the 5 troughs
    trough_weight = np.clip(- np.cos(phase_rossby), 0.0, 1.0)**4
    cyclonic_nodes = np.exp(- ((R_rad - 0.74)**2) / 0.035) * trough_weight * 2.2

    # Kelvin-Helmholtz shear billows along jet flanks
    kh_billows = (
        np.sin(28.0 * (Theta - omega_jet * t) - 14.0 * R_rad)
        * np.exp(- (dist_to_jet**2) / 0.07)
        * 0.20
    )

    # 4. Wind Velocity Vector Field (Lagrangian Advection)
    # Azimuthal wind velocity: fastest at jet core, slower in polar vortex
    v_theta = omega_jet * R_rad * (0.55 + 0.45 * V_envelope)
    # Radial wind velocity following meander curvature dR_jet/dtheta
    dR_dtheta = - m_wave * wave_amp1 * np.sin(phase_rossby) - 2.0 * m_wave * wave_amp2 * np.sin(2.0 * phase_rossby + 0.5)
    v_rad = dR_dtheta * (v_theta / (R_jet + 1e-4)) * V_envelope

    # Convert polar velocity (v_rad, v_theta) to Cartesian (u_x, u_y)
    cos_th = np.cos(Theta)
    sin_th = np.sin(Theta)
    u_wind_x = (v_rad * cos_th - v_theta * sin_th) / (R_rad + 0.1)
    u_wind_y = (v_rad * sin_th + v_theta * cos_th) / (R_rad + 0.1)

    # 5. 3D Geopotential Relief & Blinn-Phong Specular Shading
    H_relief = (
        V_envelope * 0.45
        + iso_core * 0.40
        + iso_inner * 0.20
        + polar_spirals * 0.18
        + subtropical_ripples * 0.14
        + cyclonic_nodes * 0.35
        + kh_billows * 0.10
    )
    grad_y, grad_x = np.gradient(H_relief, dy, dx)
    norm_denom = np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    Nx_s = -grad_x / norm_denom
    Ny_s = -grad_y / norm_denom
    Nz_s = 1.0 / norm_denom

    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**32
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**22

    return (
        iso_core,
        iso_inner,
        iso_outer,
        V_envelope,
        streak_factor,
        polar_spirals,
        cyclonic_nodes,
        kh_billows,
        spec1,
        spec2,
        u_wind_x,
        u_wind_y,
        t,
    )


def render_rossby_canvas(
    iso_core,
    iso_inner,
    iso_outer,
    V_envelope,
    streak_factor,
    polar_spirals,
    cyclonic_nodes,
    kh_billows,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Arctic Stratosphere Obsidian Void & Deep Polar Indigo Abyss (#020308, #080c1e, #111632)
    - 30% Baroclinic Jet Ribbons, Glacial Cyan & Sapphire Isotachs (#0284c7, #06b6d4, #38bdf8, #7dd3fc)
    - 10% Incandescent Jet-Streak Fronts (Diamond-White & Solar Gold) + Cyclonic Eye Caustics (#ffffff, #fef08a, #fbbf24)
    """
    # 1. Background 60%: Arctic Stratosphere Obsidian Void & Deep Polar Indigo Abyss
    r_bg = 2.0 + np.exp(- (R_rad**2) / 3.8) * 3.0
    g_bg = 3.0 + np.exp(- (R_rad**2) / 3.8) * 6.0
    b_bg = 7.0 + np.exp(- (R_rad**2) / 3.8) * 22.0

    # 2. Secondary 30%: Baroclinic Jet Ribbons, Glacial Cyan & Sapphire Isotachs
    r_jet = iso_inner * 15.0 + iso_outer * 25.0 + np.maximum(0.0, polar_spirals) * 12.0
    g_jet = iso_inner * 110.0 + iso_outer * 85.0 + np.maximum(0.0, polar_spirals) * 75.0
    b_jet = iso_inner * 240.0 + iso_outer * 215.0 + np.maximum(0.0, polar_spirals) * 205.0

    # Specular reflections
    spec_r = spec1 * 125.0 + spec2 * 240.0
    spec_g = spec1 * 210.0 + spec2 * 230.0
    spec_b = spec1 * 255.0 + spec2 * 160.0

    # Base composite
    blend_field = np.clip(V_envelope * 1.25 + np.maximum(0.0, polar_spirals) * 0.5, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_field) + (r_jet + spec_r * 0.65) * blend_field
    g_mid = g_bg * (1.0 - blend_field) + (g_jet + spec_g * 0.65) * blend_field
    b_mid = b_bg * (1.0 - blend_field) + (b_jet + spec_b * 0.65) * blend_field

    # 3. Accent 10%: Incandescent Jet-Streak Core (Diamond-White) & Solar Gold Cyclonic Nodes
    r_core_streak = iso_core * streak_factor * 240.0 + cyclonic_nodes * 255.0
    g_core_streak = iso_core * streak_factor * 250.0 + cyclonic_nodes * 210.0
    b_core_streak = iso_core * streak_factor * 255.0 + cyclonic_nodes * 105.0

    r_final = np.clip(r_mid + r_core_streak, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_core_streak, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_core_streak, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute Rossby wave and baroclinic jet stream fields
    (
        iso_core,
        iso_inner,
        iso_outer,
        V_envelope,
        streak_factor,
        polar_spirals,
        cyclonic_nodes,
        kh_billows,
        spec1,
        spec2,
        u_wind_x,
        u_wind_y,
        t,
    ) = compute_rossby_wave_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_rossby_canvas(
        iso_core,
        iso_inner,
        iso_outer,
        V_envelope,
        streak_factor,
        polar_spirals,
        cyclonic_nodes,
        kh_billows,
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

    # 4. Lagrangian Particle Spawning (Jet Streak Parcels, Cyclonic Eyes & Polar Vortex Swirlers)
    x_min, x_max = x_coords[0], x_coords[-1]
    y_min, y_max = y_coords[0], y_coords[-1]

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(50, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.65:
                # Jet streak parcel spawned along the meandering jet stream ribbon
                th_spawn = random.uniform(0.0, 2.0 * np.pi)
                r_meander = R0 + 0.38 * np.cos(m_wave * th_spawn) + random.gauss(0.0, 0.08)
                px = ((r_meander * np.cos(th_spawn) - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((r_meander * np.sin(th_spawn) - y_min) / (y_max - y_min)) * py5.height
                particles.append(AtmosphericParcel(px, py_screen, ptype="jet"))

            elif roll < 0.85:
                # Cyclonic eye eddy parcel in one of the 5 troughs
                k_trough = random.randint(0, m_wave - 1)
                th_trough = (2.0 * np.pi * k_trough + np.pi) / m_wave + c_phase * t
                r_trough = 0.74 + random.gauss(0.0, 0.05)
                px = ((r_trough * np.cos(th_trough) - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((r_trough * np.sin(th_trough) - y_min) / (y_max - y_min)) * py5.height
                angle = random.uniform(0.0, 2.0 * np.pi)
                v_eddy = random.uniform(2.0, 4.5)
                vx = -np.sin(angle) * v_eddy
                vy = np.cos(angle) * v_eddy
                particles.append(AtmosphericParcel(px, py_screen, ptype="cyclone", vx=vx, vy=vy))

            else:
                # Polar vortex core parcel
                r_core = random.uniform(0.05, 0.65)
                th_core = random.uniform(0.0, 2.0 * np.pi)
                px = ((r_core * np.cos(th_core) - x_min) / (x_max - x_min)) * py5.width
                py_screen = ((r_core * np.sin(th_core) - y_min) / (y_max - y_min)) * py5.height
                particles.append(AtmosphericParcel(px, py_screen, ptype="polar"))

    # 5. Advect and Render Lagrangian Atmospheric Parcels in Native 4K Vector Mode
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        norm_x = p.px / py5.width
        norm_y = p.py / py5.height

        gx = int(np.clip(norm_x * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip(norm_y * (Ny - 1), 0, Ny - 1))

        u_wx = float(u_wind_x[gy, gx])
        u_wy = float(u_wind_y[gy, gx])

        p.update(u_wx, u_wy)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.ptype == "jet":
                # Jet streak parcel: Incandescent diamond-white & glacial cyan (#ffffff, #38bdf8)
                cr, cg, cb = 180, 235, 255
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.35))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(cr, cg, cb, int(alpha * 0.82))
                py5.stroke_weight(1.6)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "cyclone":
                # Cyclonic eye tracer: Warm solar gold & amber (#fbbf24, #f59e0b)
                cr, cg, cb = 255, 215, 110
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.38))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(255, 255, 240, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(cr, cg, cb, int(alpha * 0.85))
                py5.stroke_weight(1.8)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            else:
                # Polar vortex swirler: Deep sapphire & electric violet (#6366f1, #a855f7)
                cr, cg, cb = 140, 160, 255
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.8)
                py5.fill(220, 230, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)
                py5.stroke(cr, cg, cb, int(alpha * 0.70))
                py5.stroke_weight(1.3)
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Parcels: {len(particles)}")

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

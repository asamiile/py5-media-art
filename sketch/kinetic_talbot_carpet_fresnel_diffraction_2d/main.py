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

# Spatial Simulation Grid (16:9 aspect ratio, vertical Fresnel propagation domain)
# X: transverse coordinate across periodic grating slits
# Z: longitudinal Fresnel propagation distance from aperture into near-field
Nx, Ny = 640, 360
x_coords = np.linspace(-3.2, 3.2, Nx, dtype=np.float32)
z_coords = np.linspace(0.02, 2.2, Ny, dtype=np.float32)
X_grid, Z_grid = np.meshgrid(x_coords, z_coords)
dx = float(x_coords[1] - x_coords[0])
dz = float(z_coords[1] - z_coords[0])

# Grating and optical parameters
d = 0.80  # grating period along X (~8 spatial periods across canvas)
z_T = 2.0 * (d**2) / 0.5  # Talbot revival distance scale = 2.56
N_harm = 18
n_indices = np.arange(1, N_harm + 1, dtype=np.float32)

# Precompute static spatial harmonic factors for fast vectorized synthesis
# Shape: (N_harm, 1, 1)
n_vec = n_indices[:, np.newaxis, np.newaxis]
spatial_phase_z = 2.0 * np.pi * (n_vec**2 / z_T) * Z_grid[np.newaxis, ...]
spatial_phase_x = 2.0 * np.pi * n_vec * X_grid[np.newaxis, ...] / d
gaussian_cutoff = np.exp(- (n_vec / 14.5)**2)

# Transverse Gaussian beam envelope across aperture
beam_envelope = np.exp(- (X_grid**2) / (2.0 * (2.35**2)))

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Directions for 3D Specular Relief Shading
light1 = np.array([0.52, -0.58, 0.62], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.66], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Bohmian Photons & Topological Phase Vortex Tracers
MAX_PARTICLES = 1500
particles = []


class BohmianPhoton:
    def __init__(self, px, py, ptype="photon", vx=0.0, vy=0.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "photon" (forward streamer) or "vortex" (topological tracer)
        self.vx = vx
        self.vy = vy

        if ptype == "photon":
            self.life = random.uniform(90.0, 240.0)
            self.radius = random.uniform(1.2, 2.5)
        else:  # vortex core tracer
            self.life = random.uniform(60.0, 160.0)
            self.radius = random.uniform(1.8, 3.4)

        self.max_life = self.life

    def update(self, u_bohm_x, u_bohm_z, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "photon":
            # Guided by Poynting momentum vector with forward longitudinal drift
            forward_drift = 3.2
            self.px += u_bohm_x * 2.8 * dt
            self.py += (u_bohm_z * 1.8 + forward_drift) * dt
        else:
            # Vortex tracer orbiting optical phase singularities
            self.px += (u_bohm_x * 4.2 + self.vx) * dt
            self.py += (u_bohm_z * 4.2 + self.vy) * dt
            self.vx *= 0.95
            self.vy *= 0.95

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 80
            or self.px < -80
            or self.py > py5.height + 80
            or self.py < -80
        )


def compute_talbot_carpet_fields(frame):
    """
    Computes 2D wave optics of the Talbot Effect and Fresnel Diffraction Carpet:
    - Periodic Ronchi transmission grating undergoing breathing wavepacket modulation
    - Exact analytical Fresnel paraxial harmonic propagator with quadratic phase dispersion
    - Integer and fractional Talbot revivals (self-imaging lattices at z = z_T, z_T/2, z_T/4)
    - Poynting momentum vector field (Bohmian stream-tubes) and optical phase singularities
    - 3D Blinn-Phong specular relief shading of the coherent wavefield
    """
    t = frame / 60.0  # seconds

    # 1. Dynamic Grating Modulation
    # Breathing slit aperture width
    w_slit = d * (0.30 + 0.07 * np.sin(0.85 * t))
    c0 = w_slit / d

    # Traveling laser carrier phase
    phase_carrier = 2.4 * t

    # Analytical Fourier slit coefficients for current aperture width
    # cn = (sin(pi * n * w / d) / (pi * n)) * gaussian_cutoff
    cn_vec = (np.sin(np.pi * n_vec * w_slit / d) / (np.pi * n_vec)) * gaussian_cutoff

    # 2. Fresnel Harmonic Summation (Vectorized over N_harm)
    # Total phase for forward and backward transverse spatial modes
    # mode_pos: exp(i * (phase_x - phase_z - phase_carrier))
    # mode_neg: exp(i * (-phase_x - phase_z - phase_carrier))
    time_shift = 0.035 * np.sin(0.7 * t)
    phase_x_mod = spatial_phase_x - (2.0 * np.pi * n_vec * time_shift / d)
    
    phi_pos = phase_x_mod - spatial_phase_z - phase_carrier
    phi_neg = -phase_x_mod - spatial_phase_z - phase_carrier

    modes_sum = np.sum(cn_vec * (np.exp(1j * phi_pos) + np.exp(1j * phi_neg)), axis=0)
    psi = (c0 + modes_sum) * beam_envelope

    # Non-linear optical Kerr self-focusing at intense focal knots
    I_raw = np.abs(psi)**2
    psi *= np.exp(1j * 0.32 * I_raw)

    I = np.abs(psi)**2
    phase = np.angle(psi)

    # 3. Poynting Momentum Vector & Spatial Derivatives
    # dz along axis 0, dx along axis 1
    dpsi_dz, dpsi_dx = np.gradient(psi, dz, dx)
    
    # Poynting vector / Bohmian velocity: Im(psi* grad psi) / (|psi|^2 + eps)
    Sx = np.imag(np.conj(psi) * dpsi_dx) / (I + 0.006)
    Sz = np.imag(np.conj(psi) * dpsi_dz) / (I + 0.006)

    # 4. Normalized Intensity & Interference Features
    p99 = float(np.percentile(I, 99.2))
    I_norm = np.clip(I / (p99 + 1e-4), 0.0, 3.5)

    # Talbot focal knots (incandescent constructive interference peaks at revival centers)
    focal_knots = np.clip((I_norm - 1.15) / 1.35, 0.0, 1.0)**2.2

    # Fractal diamond lace (sub-harmonic fractional Talbot carpet fringes)
    lace_fringes = (
        np.sin(np.pi * I_norm * 2.2)**2
        * np.clip((I_norm - 0.15) / 0.7, 0.0, 1.0)
        * np.exp(- (I_norm - 0.75)**2 / 0.45)
    )

    # Topological phase singularities (optical vortices at dark nodal zeros)
    phase_grad_mag = np.sqrt(np.abs(dpsi_dx)**2 + np.abs(dpsi_dz)**2)
    vortex_cores = np.exp(- (I_norm / 0.06)**2) * np.clip((phase_grad_mag - 5.0) / 7.0, 0.0, 1.0)**2

    # 5. 3D Blinn-Phong Specular Relief Shading
    H_surf = np.sqrt(I_norm) * 0.85 + 0.12 * np.cos(phase)
    grad_H_z, grad_H_x = np.gradient(H_surf, dz, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_z**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Nz_s = -grad_H_z / norm_denom
    Ny_s = 1.0 / norm_denom

    spec1 = np.maximum(0.0, Nx_s * h1[0] + Nz_s * h1[1] + Ny_s * h1[2])**30
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Nz_s * h2[1] + Ny_s * h2[2])**20

    return (
        I_norm,
        lace_fringes,
        focal_knots,
        vortex_cores,
        spec1,
        spec2,
        Sx,
        Sz,
        t,
    )


def render_talbot_canvas(
    I_norm,
    lace_fringes,
    focal_knots,
    vortex_cores,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Quantum Vacuum Obsidian Void & Deep Indigo Shadow (#020207, #070a18, #0e1228)
    - 30% Coherent Laser Azure & Electric Glacial Cyan Interference Fringes (#0284c7, #06b6d4, #38bdf8, #7dd3fc)
    - 10% Incandescent Talbot Focal Knots Diamond-White & Solar Gold Caustics (#ffffff, #fef08a, #fbbf24) + Electric Violet Vortex Stars
    """
    # 1. Background 60%: Quantum Obsidian Vacuum Void & Deep Indigo Shadow
    r_bg = 2.0 + np.exp(- (X_grid**2) / 3.0) * 4.0
    g_bg = 3.0 + np.exp(- (X_grid**2) / 3.0) * 6.0
    b_bg = 8.0 + np.exp(- (X_grid**2) / 3.0) * 20.0

    # 2. Secondary 30%: Coherent Laser Azure & Electric Glacial Cyan Interference Fringes
    carpet_cyan = np.clip(I_norm * 0.90, 0.0, 1.0)
    r_carpet = carpet_cyan * 8.0 + lace_fringes * 24.0
    g_carpet = carpet_cyan * 72.0 + lace_fringes * 155.0
    b_carpet = carpet_cyan * 195.0 + lace_fringes * 250.0

    # Specular reflections: crystal glass and icy azure highlights
    spec_r = spec1 * 125.0 + spec2 * 240.0
    spec_g = spec1 * 210.0 + spec2 * 230.0
    spec_b = spec1 * 255.0 + spec2 * 160.0

    # Base field composite
    blend_field = np.clip((I_norm - 0.08) / 0.45, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_field) + (r_carpet + spec_r * 0.65) * blend_field
    g_mid = g_bg * (1.0 - blend_field) + (g_carpet + spec_g * 0.65) * blend_field
    b_mid = b_bg * (1.0 - blend_field) + (b_carpet + spec_b * 0.65) * blend_field

    # 3. Accent 10%: Incandescent Talbot Focal Knots (Diamond-White & Solar Gold) + Electric Violet Vortex Stars
    r_focal = focal_knots * 255.0 + vortex_cores * 180.0
    g_focal = focal_knots * 245.0 + vortex_cores * 100.0
    b_focal = focal_knots * 185.0 + vortex_cores * 255.0

    # Final composite clamped to uint8
    r_final = np.clip(r_mid + r_focal, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_focal, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_focal, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute wave optics and Fresnel diffraction fields
    (
        I_norm,
        lace_fringes,
        focal_knots,
        vortex_cores,
        spec1,
        spec2,
        Sx,
        Sz,
        t,
    ) = compute_talbot_carpet_fields(py5.frame_count)

    # 2. Render pixel buffer
    render_talbot_canvas(
        I_norm,
        lace_fringes,
        focal_knots,
        vortex_cores,
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

    # 4. Lagrangian Particle Spawning (Bohmian Photons & Vortex Tracers)
    x_min, x_max = x_coords[0], x_coords[-1]
    z_min, z_max = z_coords[0], z_coords[-1]

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(50, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.70:
                # Bohmian photon injected at aperture plane (top edge) or interior slit
                x_spawn = random.uniform(x_min * 0.85, x_max * 0.85)
                z_spawn = random.uniform(z_min, z_min + 0.15) if random.random() < 0.65 else random.uniform(z_min, z_max)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                pz = ((z_spawn - z_min) / (z_max - z_min)) * py5.height
                particles.append(BohmianPhoton(px, pz, ptype="photon"))
            else:
                # Topological vortex tracer trapped near phase singularities
                x_spawn = random.uniform(x_min * 0.75, x_max * 0.75)
                z_spawn = random.uniform(z_min + 0.3, z_max - 0.2)
                px = ((x_spawn - x_min) / (x_max - x_min)) * py5.width
                pz = ((z_spawn - z_min) / (z_max - z_min)) * py5.height
                angle = random.uniform(0.0, 2.0 * np.pi)
                v_spin = random.uniform(1.5, 4.0)
                vx = np.cos(angle) * v_spin
                vy = np.sin(angle) * v_spin
                particles.append(BohmianPhoton(px, pz, ptype="vortex", vx=vx, vy=vy))

    # 5. Advect and Render Lagrangian Particles in Native 4K Vector Mode
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        norm_x = p.px / py5.width
        norm_z = p.py / py5.height

        gx = int(np.clip(norm_x * (Nx - 1), 0, Nx - 1))
        gz = int(np.clip(norm_z * (Ny - 1), 0, Ny - 1))

        u_bx = float(Sx[gz, gx])
        u_bz = float(Sz[gz, gx])

        p.update(u_bx, u_bz)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.ptype == "photon":
                # Bohmian photon: Incandescent solar gold & diamond-white (#ffffff, #fbbf24)
                cr, cg, cb = 255, 235, 160
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.35))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(cr, cg, cb, int(alpha * 0.80))
                py5.stroke_weight(1.6)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)
            else:
                # Vortex core tracer: Electric cyan & violet star (#38bdf8, #c084fc)
                cr, cg, cb = 180, 140, 255
                py5.no_stroke()
                py5.fill(cr, cg, cb, int(alpha * 0.32))
                py5.circle(p.px, p.py, p.radius * 3.0)
                py5.fill(220, 240, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.9)
                py5.stroke(cr, cg, cb, int(alpha * 0.75))
                py5.stroke_weight(1.4)
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Photons: {len(particles)}")

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

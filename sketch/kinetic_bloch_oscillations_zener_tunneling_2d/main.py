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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio, 800x450 grid)
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Optical Lattice Parameters (Wavelength and Potential Depth)
k_lattice = 3.6  # Wavevector of periodic optical lattice
V0_depth = 1.25  # Potential well depth
# Static periodic egg-crate potential
V_lattice = V0_depth * (np.cos(k_lattice * X_grid)**2 + np.cos(k_lattice * Y_grid)**2)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Vectors for Specular Lattice Shading
light1 = np.array([0.55, -0.60, 0.58], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.67], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Bohmian Quantum Tracers, Zener Tunneling Sparks & Lattice Embers
MAX_PARTICLES = 1600
particles = []


class QuantumLatticeParticle:
    def __init__(self, px, py, ptype="bohmian", vx=0.0, vy=0.0, life=120.0, radius=2.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "bohmian", "zener", "lattice"
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "bohmian":
            # Guided along quantum probability flow
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.985
            self.vy *= 0.985
        elif self.ptype == "zener":
            # High-speed tunneling burst spark
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.96
            self.vy *= 0.96
        elif self.ptype == "lattice":
            # Bound in optical potential well with quantum micro-jitter
            self.px += (self.vx + random.uniform(-0.35, 0.35)) * dt
            self.py += (self.vy + random.uniform(-0.35, 0.35)) * dt
            self.vx *= 0.92
            self.vy *= 0.92

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 120
            or self.px < -120
            or self.py > py5.height + 120
            or self.py < -120
        )


def compute_bloch_fields(frame):
    """
    Computes 2D tight-binding Schrödinger wavepacket dynamics in an optical lattice:
    - Harmonic spatial Bloch oscillations across Brillouin zones under constant force
    - Landau-Zener inter-band tunneling at turning points
    - Wannier-Stark ladder resonance fringe formation
    - 3D Blinn-Phong specular quantum potential normal shading
    """
    t_norm = frame / TOTAL_FRAMES
    t_phase = frame * 0.055

    # 1. Bloch Oscillation Kinematics
    # Group velocity v_g ~ sin(q(t)*a), spatial coordinate X(t) ~ cos(omega_B * t)
    omega_B_x = 2.4  # Bloch frequency along X
    omega_B_y = 1.6  # Bloch frequency along Y (incommensurate ratio for Lissajous orbit)

    # Primary wavepacket center position
    X_c1 = 1.75 * np.cos(omega_B_x * t_phase)
    Y_c1 = 0.95 * np.sin(omega_B_y * t_phase + 0.4)

    # Velocity components (for Bohmian current and heading)
    Vx_c1 = -1.75 * omega_B_x * np.sin(omega_B_x * t_phase)
    Vy_c1 = 0.95 * omega_B_y * np.cos(omega_B_y * t_phase + 0.4)

    # 2. Landau-Zener Tunneling Daughter Wavepacket
    # Daughter packet bifurcates when primary reaches Brillouin zone edges (turning points)
    # Tunneling occurs near max displacement |X_c1| ~ 1.75
    zener_phase = t_phase - 0.75
    X_c2 = 1.45 * np.cos(omega_B_x * zener_phase + 0.8)
    Y_c2 = -0.85 * np.sin(omega_B_y * zener_phase - 0.2)

    # 3. Wavepacket Probability Densities |psi_1|^2 and |psi_2|^2
    # Envelope width
    sigma_pack = 0.48
    r_sq1 = (X_grid - X_c1)**2 + (Y_grid - Y_c1)**2
    # Primary Bloch wavepacket with internal crystalline interference fringes
    carrier_k1 = k_lattice * np.sin(omega_B_x * t_phase)
    carrier_fringe1 = np.cos(carrier_k1 * (X_grid - X_c1) + 2.0 * carrier_k1 * (Y_grid - Y_c1))**2
    psi_sq1 = np.exp(-r_sq1 / (2.0 * sigma_pack**2)) * (0.45 + 0.55 * carrier_fringe1)

    # Secondary Tunneled Wavepacket
    r_sq2 = (X_grid - X_c2)**2 + (Y_grid - Y_c2)**2
    carrier_k2 = k_lattice * np.cos(omega_B_x * zener_phase)
    carrier_fringe2 = np.cos(carrier_k2 * (X_grid - X_c2) - 1.5 * carrier_k2 * (Y_grid - Y_c2))**2
    # Zener tunneling weight pulses at turning points
    zener_weight = 0.35 + 0.35 * (np.sin(omega_B_x * t_phase)**4)
    psi_sq2 = np.exp(-r_sq2 / (2.0 * (sigma_pack * 0.85)**2)) * (0.4 + 0.6 * carrier_fringe2) * zener_weight

    # 4. Wannier-Stark Ladder Resonance (Equispaced potential energy step states)
    # Tilted potential V_tilt = F_x * X + F_y * Y creates discrete resonant rungs
    F_tilt_phase = 4.2 * X_grid + 2.8 * Y_grid - t_phase * 1.5
    wannier_stark_fringes = (
        np.cos(F_tilt_phase)**4
        * np.exp(- (X_grid**2 + Y_grid**2) / 6.5)
        * 0.42
    )

    # 5. Composite Quantum Energy Field
    # Combining lattice substrate with quantum wavepacket probabilities
    I_quantum = (
        psi_sq1 * 2.6
        + psi_sq2 * 1.8
        + wannier_stark_fringes * 0.75
        + V_lattice * 0.35
    )

    # 6. 3D Blinn-Phong Specular Normal Shading
    H_surf = np.sqrt(np.clip(I_quantum, 0.0, 4.0)) * 0.58
    grad_H_y, grad_H_x = np.gradient(H_surf, dy, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_y**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Ny_s = -grad_H_y / norm_denom
    Nz_s = 1.0 / norm_denom

    # Light 1: Cool Mint Emerald specular reflection
    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**22
    # Light 2: Radiant Amethyst Violet specular reflection
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**16

    return (
        I_quantum,
        psi_sq1,
        psi_sq2,
        wannier_stark_fringes,
        spec1,
        spec2,
        X_c1,
        Y_c1,
        Vx_c1,
        Vy_c1,
        X_c2,
        Y_c2,
        t_phase,
    )


def render_bloch_canvas(
    I_quantum,
    psi_sq1,
    psi_sq2,
    wannier_stark_fringes,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer following 60-30-10 palette rules:
    - 60% Quantum Lattice Obsidian Void & Deep Sub-Band Indigo (#02030a, #070a1a)
    - 30% Luminous Emerald (#10b981) & Mint Wavefronts (#34d399, #059669)
    - 30% Secondary: Deep Amethyst (#8b5cf6) & Radiant Violet Inter-Band Glow (#7c3aed, #4c1d95)
    - 10% Accent: Incandescent Zener Tunneling Spark Diamond-White & Solar Gold (#ffffff, #facc15)
    """
    # 1. Background 60%: Quantum Lattice Obsidian Void with optical lattice well shading
    lattice_dark = np.clip(V_lattice * 0.45, 0.0, 1.0)
    r_bg = 2.0 + lattice_dark * 10.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 4.0
    g_bg = 3.0 + lattice_dark * 16.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 6.0
    b_bg = 10.0 + lattice_dark * 38.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 24.0

    # 2. Dominant 60% (of foreground): Luminous Emerald & Mint Wavefronts (#10b981, #34d399)
    emerald_wave = np.clip(psi_sq1 * 1.35, 0.0, 2.5)
    r_emerald = emerald_wave * 16.0
    g_emerald = emerald_wave * 185.0
    b_emerald = emerald_wave * 129.0

    # Secondary 30%: Deep Amethyst & Radiant Violet Inter-Band Glow (#8b5cf6, #7c3aed)
    violet_wave = np.clip(psi_sq2 * 1.45 + wannier_stark_fringes * 0.9, 0.0, 2.5)
    r_violet = violet_wave * 139.0
    g_violet = violet_wave * 92.0
    b_violet = violet_wave * 246.0

    # Specular reflections (Light 1: ice-mint, Light 2: amethyst)
    spec_r = spec1 * 110.0 + spec2 * 210.0
    spec_g = spec1 * 245.0 + spec2 * 140.0
    spec_b = spec1 * 180.0 + spec2 * 255.0

    # Combined quantum wavepacket foreground
    r_wave = r_emerald * 0.60 + r_violet * 0.40 + spec_r * 0.45
    g_wave = g_emerald * 0.70 + g_violet * 0.30 + spec_g * 0.45
    b_wave = b_emerald * 0.40 + b_violet * 0.60 + spec_b * 0.45

    blend_factor = np.clip(I_quantum * 0.85, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_factor) + r_wave * blend_factor
    g_mid = g_bg * (1.0 - blend_factor) + g_wave * blend_factor
    b_mid = b_bg * (1.0 - blend_factor) + b_wave * blend_factor

    # 3. Accent 10%: Incandescent Zener Tunneling Spark Diamond-White & Solar Gold (#ffffff, #facc15)
    core_accent = np.clip((psi_sq1 * psi_sq1) * 2.2 + (psi_sq2 * psi_sq2) * 1.8 + spec1 * 0.45, 0.0, 2.5)
    r_accent = core_accent * 255.0
    g_accent = core_accent * 248.0
    b_accent = core_accent * 215.0

    # Final pixel buffer compilation clamped to uint8
    r_final = np.clip(r_mid + r_accent, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_accent, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_accent, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute Bloch oscillation and quantum fields
    (
        I_quantum,
        psi_sq1,
        psi_sq2,
        wannier_stark_fringes,
        spec1,
        spec2,
        X_c1,
        Y_c1,
        Vx_c1,
        Vy_c1,
        X_c2,
        Y_c2,
        t_phase,
    ) = compute_bloch_fields(py5.frame_count)

    # 2. Render pixel buffer canvas
    render_bloch_canvas(
        I_quantum,
        psi_sq1,
        psi_sq2,
        wannier_stark_fringes,
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

    # 4. Map wavepacket centers to screen coordinates
    screen_x1 = (X_c1 - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
    screen_y1 = (Y_c1 - y_coords[0]) / (y_coords[-1] - y_coords[0]) * py5.height

    screen_x2 = (X_c2 - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
    screen_y2 = (Y_c2 - y_coords[0]) / (y_coords[-1] - y_coords[0]) * py5.height

    # 5. Spawn Lagrangian Quantum Particles
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.60:
                # Bohmian Quantum Tracers: Swirling inside primary wavepacket
                angle = random.uniform(0.0, 2.0 * np.pi)
                radius_spawn = random.gauss(0.0, 48.0)
                px = screen_x1 + np.cos(angle) * radius_spawn
                py = screen_y1 + np.sin(angle) * radius_spawn
                # Velocity guided by wavepacket motion plus phase swirling
                vx = Vx_c1 * 1.6 + (-np.sin(angle) * 2.2)
                vy = Vy_c1 * 1.6 + (np.cos(angle) * 2.2)
                particles.append(QuantumLatticeParticle(
                    px,
                    py,
                    ptype="bohmian",
                    vx=vx,
                    vy=vy,
                    life=random.uniform(60.0, 120.0),
                    radius=random.uniform(1.4, 2.8)
                ))

            elif roll < 0.85:
                # Zener Tunneling Sparks: High-energy bursts between wavepackets
                px = screen_x2 + random.gauss(0.0, 24.0)
                py = screen_y2 + random.gauss(0.0, 24.0)
                tunnel_dir = np.arctan2(screen_y2 - screen_y1, screen_x2 - screen_x1) + random.gauss(0.0, 0.35)
                speed = random.uniform(3.5, 8.5)
                particles.append(QuantumLatticeParticle(
                    px,
                    py,
                    ptype="zener",
                    vx=np.cos(tunnel_dir) * speed,
                    vy=np.sin(tunnel_dir) * speed,
                    life=random.uniform(30.0, 70.0),
                    radius=random.uniform(1.8, 3.4)
                ))

            else:
                # Lattice Site Resonators: Trapped in periodic optical potential wells
                grid_col = random.randint(1, Nx - 2)
                grid_row = random.randint(1, Ny - 2)
                px = (grid_col / Nx) * py5.width
                py = (grid_row / Ny) * py5.height
                particles.append(QuantumLatticeParticle(
                    px,
                    py,
                    ptype="lattice",
                    vx=random.uniform(-0.5, 0.5),
                    vy=random.uniform(-0.5, 0.5),
                    life=random.uniform(80.0, 160.0),
                    radius=random.uniform(1.0, 2.2)
                ))

    # 6. Update and Draw Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        p.update()
        if not p.is_dead:
            active_particles.append(p)
            progress = p.life / p.max_life
            alpha = int(progress * 255)

            if p.ptype == "bohmian":
                # Bohmian tracer: Luminous emerald & mint glow (#10b981, #34d399)
                py5.no_stroke()
                py5.fill(16, 185, 129, int(alpha * 0.38))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(230, 255, 245, alpha)
                py5.circle(p.px, p.py, p.radius * 0.95)
                py5.stroke(52, 211, 153, int(alpha * 0.75))
                py5.stroke_weight(1.3)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "zener":
                # Zener tunneling spark: Solar gold & diamond-white (#facc15, #ffffff)
                py5.no_stroke()
                py5.fill(250, 204, 21, int(alpha * 0.45))
                py5.circle(p.px, p.py, p.radius * 3.5)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(250, 204, 21, int(alpha * 0.85))
                py5.stroke_weight(1.7)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "lattice":
                # Lattice site ember: Deep amethyst & violet (#8b5cf6)
                py5.no_stroke()
                py5.fill(139, 92, 246, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.6)
                py5.fill(216, 180, 254, alpha)
                py5.circle(p.px, p.py, p.radius * 0.8)

    particles = active_particles

    # 7. Render Primary & Secondary Wavepacket Cores
    py5.no_stroke()
    # Primary wavepacket core (Emerald / Diamond White)
    py5.fill(16, 185, 129, 50)
    py5.circle(screen_x1, screen_y1, 68.0)
    py5.fill(52, 211, 153, 110)
    py5.circle(screen_x1, screen_y1, 38.0)
    py5.fill(255, 255, 255, 240)
    py5.circle(screen_x1, screen_y1, 16.0)

    # Secondary tunneled wavepacket core (Amethyst / Solar Gold)
    py5.fill(139, 92, 246, 45)
    py5.circle(screen_x2, screen_y2, 54.0)
    py5.fill(250, 204, 21, 95)
    py5.circle(screen_x2, screen_y2, 28.0)
    py5.fill(255, 255, 255, 220)
    py5.circle(screen_x2, screen_y2, 12.0)

    py5.blend_mode(py5.BLEND)

    # 8. Fail-safe: Blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 9. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Particles: {len(particles)}")

    # 10. Finalize render on completion
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

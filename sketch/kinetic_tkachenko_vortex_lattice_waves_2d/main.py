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

# Spatial Grid for macroscopic phase & Voronoi field (16:9)
Nx, Ny = 640, 360
x_coords = np.linspace(-5.0, 5.0, Nx, dtype=np.float32)
y_coords = np.linspace(-5.0 * (Ny / Nx), 5.0 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Equilibrium triangular Abrikosov vortex lattice
a0 = 1.05
vortex_equilibrium = []
for row in range(-6, 7):
    for col in range(-7, 8):
        vx = col * a0 + (0.5 * a0 if row % 2 != 0 else 0.0)
        vy = row * a0 * (np.sqrt(3.0) / 2.0)
        if -4.5 <= vx <= 4.5 and -2.5 <= vy <= 2.5:
            vortex_equilibrium.append((vx, vy))

vortex_equilibrium = np.array(vortex_equilibrium, dtype=np.float32)
N_VORTICES = len(vortex_equilibrium)

# Tkachenko Shear Wave Modes:
# Mode 1: k1 = (1.2, 0.8), transverse polarization
kx1, ky1 = 1.2, 0.8
k_norm1 = np.sqrt(kx1**2 + ky1**2)
pol_x1, pol_y1 = -ky1 / k_norm1, kx1 / k_norm1
omega1 = 2.2

# Mode 2: k2 = (-0.9, 1.4), transverse polarization
kx2, ky2 = -0.9, 1.4
k_norm2 = np.sqrt(kx2**2 + ky2**2)
pol_x2, pol_y2 = -ky2 / k_norm2, kx2 / k_norm2
omega2 = 1.8

# Trapped Exciton / Quantum Impurity Particles
MAX_PARTICLES = 360
particles = []


class TrappedImpurity:
    def __init__(self, target_idx, cx_screen, cy_screen):
        self.target_idx = target_idx
        self.orbit_angle = random.uniform(0.0, 2.0 * np.pi)
        self.orbit_rad = random.uniform(12.0, 36.0)  # pixels on 4K canvas
        self.orbit_speed = random.uniform(0.04, 0.09) * random.choice([-1.0, 1.0])
        self.px = cx_screen + np.cos(self.orbit_angle) * self.orbit_rad
        self.py = cy_screen + np.sin(self.orbit_angle) * self.orbit_rad
        self.prev_x = self.px
        self.prev_y = self.py
        self.life = random.uniform(40.0, 120.0)
        self.max_life = self.life
        self.size = random.uniform(2.5, 4.8)

    def update(self, cx_screen, cy_screen):
        self.prev_x = self.px
        self.prev_y = self.py
        self.orbit_angle += self.orbit_speed
        target_x = cx_screen + np.cos(self.orbit_angle) * self.orbit_rad
        target_y = cy_screen + np.sin(self.orbit_angle) * self.orbit_rad

        self.px += (target_x - self.px) * 0.35
        self.py += (target_y - self.py) * 0.35
        self.life -= 1.0

    @property
    def is_dead(self):
        return self.life <= 0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_tkachenko_lattice(frame_idx):
    # Time variable parameterized for seamless loop over TOTAL_FRAMES
    t = (frame_idx / TOTAL_FRAMES) * 6.0 * np.pi

    # Transverse displacement field delta_r = sum_m A_m * pol_m * sin(k_m . r - omega_m * t)
    phase1 = kx1 * vortex_equilibrium[:, 0] + ky1 * vortex_equilibrium[:, 1] - omega1 * t
    disp_x = 0.28 * pol_x1 * np.sin(phase1)
    disp_y = 0.28 * pol_y1 * np.sin(phase1)

    phase2 = kx2 * vortex_equilibrium[:, 0] + ky2 * vortex_equilibrium[:, 1] - omega2 * t
    disp_x += 0.20 * pol_x2 * np.sin(phase2)
    disp_y += 0.20 * pol_y2 * np.sin(phase2)

    vortex_pos = vortex_equilibrium + np.stack([disp_x, disp_y], axis=1)

    # Macroscopic complex order parameter psi(r) = Prod_j (tanh(r_j/xi) * e^{i theta_j})
    psi = np.ones((Ny, Nx), dtype=np.complex64)
    xi = 0.32  # Healing length / core size
    for vx, vy in vortex_pos:
        dx = X_grid - vx
        dy = Y_grid - vy
        r = np.sqrt(dx**2 + dy**2) + 1e-4
        core_profile = np.tanh(r / xi)
        psi *= (core_profile * ((dx + 1j * dy) / r)).astype(np.complex64)

    density = np.abs(psi)**2
    phase = np.angle(psi)

    # Voronoi distance field to nearest and second-nearest vortex core
    dists = (X_grid[:, :, None] - vortex_pos[None, None, :, 0])**2 + (Y_grid[:, :, None] - vortex_pos[None, None, :, 1])**2
    dists_sorted = np.partition(dists, 1, axis=2)
    d_nearest = np.sqrt(dists_sorted[:, :, 0])
    d_second = np.sqrt(dists_sorted[:, :, 1])

    # Razor-sharp hexagonal Voronoi cell boundaries
    voronoi_edge = np.exp(- ((d_second - d_nearest) / 0.08)**2)

    # Topological equiphase streamlines
    phase_lines = (np.cos(phase * 3.0) * 0.5 + 0.5)**3.0

    # Vortex core luminous intensity
    vortex_core = np.exp(- (d_nearest / 0.15)**2)

    # Acoustic phonon compression waves across superfluid matrix
    sound_waves = 0.5 + 0.5 * np.sin(3.5 * np.sqrt(X_grid**2 + Y_grid**2) - 4.5 * t)

    return vortex_pos, density, phase, voronoi_edge, phase_lines, vortex_core, sound_waves


def render_superfluid_field(vortex_pos, density, phase, voronoi_edge, phase_lines, vortex_core, sound_waves):
    # Palette architecture:
    # 1. Deep Cryogenic Superfluid Matrix (60%): #02040d ~ #050b1a
    r = np.full_like(X_grid, 3.0)
    g = np.full_like(X_grid, 6.0)
    b = np.full_like(X_grid, 18.0)

    # Ambient superfluid density and acoustic ripples (Sapphire & Cobalt)
    ambient = np.clip(density * 0.65 + sound_waves * 0.15, 0.0, 1.0)
    r += ambient * 14.0
    g += ambient * 50.0
    b += ambient * 165.0

    # 2. Voronoi Elastic Shear Wave Boundaries (30%): Electric Cyan & Emerald
    r += voronoi_edge * 15.0
    g += voronoi_edge * 220.0
    b += voronoi_edge * 205.0

    # 3. Macroscopic Phase Winding Streamlines: Neon Magenta & Electric Violet
    p_norm = (phase + np.pi) / (2.0 * np.pi)
    r += phase_lines * (165.0 + 35.0 * np.sin(p_norm * 2.0 * np.pi))
    g += phase_lines * (25.0 + 25.0 * np.sin(p_norm * 2.0 * np.pi + 2.0))
    b += phase_lines * (215.0 + 35.0 * np.sin(p_norm * 2.0 * np.pi + 4.0))

    # 4. Quantized Vortex Cores (10% Accent): Incandescent Solar Gold & Diamond White
    r += vortex_core * 255.0
    g += vortex_core * 215.0
    b += vortex_core * 50.0

    peak_core = vortex_core**2.2
    r += peak_core * 255.0
    g += peak_core * 255.0
    b += peak_core * 240.0

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global particles

    # 1. Physics update
    (vortex_pos, density, phase, voronoi_edge,
     phase_lines, vortex_core, sound_waves) = compute_tkachenko_lattice(py5.frame_count)

    # 2. Render field into pixel buffer
    render_superfluid_field(vortex_pos, density, phase, voronoi_edge, phase_lines, vortex_core, sound_waves)

    # 3. Blit superfluid field image upscaled to 4K
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

    # Convert vortex positions to 4K screen coordinates
    # Domain: x in [-5.0, 5.0], y in [-5.0 * (Ny/Nx), 5.0 * (Ny/Nx)]
    y_span = 10.0 * (Ny / Nx)
    screen_cores = []
    for vx, vy in vortex_pos:
        sc_x = ((vx - (-5.0)) / 10.0) * py5.width
        sc_y = ((vy - (-5.0 * (Ny / Nx))) / y_span) * py5.height
        screen_cores.append((sc_x, sc_y))

    # 4. Replenish trapped exciton / quantum impurity particles
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(16, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            v_idx = random.randint(0, len(screen_cores) - 1)
            cx, cy = screen_cores[v_idx]
            particles.append(TrappedImpurity(v_idx, cx, cy))

    # 5. Draw Trapped Impurity Particles on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        cx, cy = screen_cores[p.target_idx % len(screen_cores)]
        p.update(cx, cy)
        if not p.is_dead:
            active_particles.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * 235)

            # Radiant solar gold to cyan-teal luminescence
            cr = int(120 + life_norm * 135)
            cg = int(220 + life_norm * 35)
            cb = int(245 - life_norm * 140)

            # Outer glow aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.35))
            py5.circle(p.px, p.py, p.size * 2.8)

            # Nucleus bead
            py5.fill(255, 255, 230, alpha)
            py5.circle(p.px, p.py, p.size * 1.1)

            # Orbital streak
            py5.stroke(cr, cg, cb, int(alpha * 0.5))
            py5.stroke_weight(1.4)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # Fail-safe blank screen check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Trapped Impurities: {len(particles)}")

    # Finalize render
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

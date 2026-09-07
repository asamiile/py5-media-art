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

# Optical Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
x_coords = np.linspace(-3.2, 3.2, Nx, dtype=np.float32)
y_coords = np.linspace(-3.2 * (Ny / Nx), 3.2 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Fundamental Gaussian envelope beam waist
w0 = 2.4
envelope = np.exp(- (X_grid**2 + Y_grid**2) / (w0**2)).astype(np.float32)

# RGBA pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Trapped Dielectric Nanoparticles in Optical Tweezers / Poynting Streamlines
MAX_PARTICLES = 360
particles = []


class DielectricParticle:
    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.vx = 0.0
        self.vy = 0.0
        self.life = random.uniform(40.0, 110.0)
        self.max_life = self.life
        self.size = random.uniform(1.8, 3.8)
        self.charge_phase = random.uniform(0.0, 2.0 * np.pi)

    def update(self, fx, fy):
        # Optical gradient and scattering forces drive particle kinematics
        self.vx = self.vx * 0.84 + fx * 0.16
        self.vy = self.vy * 0.84 + fy * 0.16
        self.px += self.vx
        self.py += self.vy
        self.life -= 1.0

    @property
    def is_dead(self):
        return (self.life <= 0 or self.px < -20 or self.px > py5.width + 20 or
                self.py < -20 or self.py > py5.height + 20)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_optical_field(frame_idx):
    # Normalized time cycle across 18s (2 full choreography cycles)
    t = (frame_idx / TOTAL_FRAMES) * 4.0 * np.pi

    # Dynamic choreography of 4 interacting optical vortex singularities
    # Topological charges: ell1 = +2, ell2 = -3, ell3 = +1, ell4 = -1
    v1_x = 1.15 * np.cos(t * 0.75)
    v1_y = 0.72 * np.sin(t * 1.05)

    v2_x = 1.25 * np.cos(t * 0.65 + 2.2)
    v2_y = 0.85 * np.sin(t * 0.85 + 1.3)

    v3_x = 0.95 * np.cos(t * 1.15 + 4.1)
    v3_y = 0.90 * np.sin(t * 0.75 + 2.8)

    v4_x = 0.55 * np.cos(t * 1.45 + 0.9)
    v4_y = 0.55 * np.sin(t * 1.45 + 2.4)

    # Complex vortex factor polynomials: (dx + i * dy)^ell
    d1 = (X_grid - v1_x) + 1j * (Y_grid - v1_y)
    f1 = d1**2
    d2 = (X_grid - v2_x) - 1j * (Y_grid - v2_y)
    f2 = d2**3
    d3 = (X_grid - v3_x) + 1j * (Y_grid - v3_y)
    f3 = d3
    d4 = (X_grid - v4_x) - 1j * (Y_grid - v4_y)
    f4 = d4

    # Complex optical beam field
    psi = envelope * (
        (f1 / (np.abs(f1) + 0.28)) *
        (f2 / (np.abs(f2) + 0.28)) *
        (f3 / (np.abs(f3) + 0.28)) *
        (f4 / (np.abs(f4) + 0.28))
    )

    intensity = np.abs(psi)**2
    phase = np.angle(psi)

    # Holographic interference with tilted + spherical reference wave (Fork dislocations)
    R_ref = 3.6
    ref_phase = 3.2 * (X_grid**2 + Y_grid**2) / R_ref + 15.0 * X_grid + 5.0 * Y_grid + t * 1.8
    ref_wave = 0.72 * np.exp(1j * ref_phase)
    interferogram = np.abs(psi + ref_wave)**2
    norm_interf = interferogram / (np.max(interferogram) + 1e-4)

    # Equiphase spiral arms (Helical phase dislocation fan petals)
    phase_petals = (np.cos(phase * 6.0) * 0.5 + 0.5)**4.0

    # Transverse Poynting vector flow: S_perp = Im(psi* grad psi)
    dpsi_x = (np.roll(psi, -1, axis=1) - np.roll(psi, 1, axis=1)) * 0.5
    dpsi_y = (np.roll(psi, -1, axis=0) - np.roll(psi, 1, axis=0)) * 0.5
    Sx = np.imag(np.conj(psi) * dpsi_x)
    Sy = np.imag(np.conj(psi) * dpsi_y)
    S_mag = np.sqrt(Sx**2 + Sy**2)
    S_norm = np.clip(S_mag / 0.65, 0.0, 1.0)

    # Vortex singularity center coordinates
    centers = [(v1_x, v1_y), (v2_x, v2_y), (v3_x, v3_y), (v4_x, v4_y)]

    return psi, intensity, phase, norm_interf, phase_petals, Sx, Sy, S_norm, centers


def render_optical_field(intensity, phase, norm_interf, phase_petals, S_norm, centers):
    global pixel_buffer

    # 1. Base Abyssal Obsidian Void (60% background/matrix): #02040d
    r = np.full_like(intensity, 2.0)
    g = np.full_like(intensity, 4.0)
    b = np.full_like(intensity, 13.0)

    # Ambient laser beam envelope sheen: Midnight Indigo
    r += intensity * 12.0
    g += intensity * 24.0
    b += intensity * 58.0

    # 2. Holographic Interference Fringes & Fork Dislocations: Electric Cyan & Aquamarine (30% secondary)
    r += norm_interf * 24.0
    g += norm_interf * 185.0
    b += norm_interf * 225.0

    # 3. Equiphase Spiral Arms: Radiant Fuchsia / Magenta
    p_cyclic = (phase + np.pi) / (2.0 * np.pi)
    r += phase_petals * (160.0 + 80.0 * np.sin(p_cyclic * 2 * np.pi))
    g += phase_petals * (28.0 + 40.0 * np.sin(p_cyclic * 2 * np.pi + 2.0))
    b += phase_petals * (215.0 + 35.0 * np.sin(p_cyclic * 2 * np.pi + 4.0))

    # 4. Poynting Vector Energy Circulation Streamlines: Electric Violet Sheen
    r += S_norm * 85.0
    g += S_norm * 40.0
    b += S_norm * 255.0

    # 5. Intense Optical Vortex Halos (10% accent): Incandescent Solar Gold to Pure White
    for vx, vy in centers:
        dist_sq = (X_grid - vx)**2 + (Y_grid - vy)**2
        dist = np.sqrt(dist_sq)

        # Luminous singularity eye ring
        halo = np.exp(- (dist - 0.07)**2 / (2.0 * 0.022**2))
        r += halo * 255.0
        g += halo * 220.0
        b += halo * 95.0

        # Core dark phase null
        core_null = np.exp(- dist_sq / (2.0 * 0.04**2))
        r *= (1.0 - core_null * 0.75)
        g *= (1.0 - core_null * 0.75)
        b *= (1.0 - core_null * 0.75)

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global particles

    # 1. Compute field physics
    psi, intensity, phase, norm_interf, phase_petals, Sx, Sy, S_norm, centers = compute_optical_field(py5.frame_count)

    # 2. Render field into pixel buffer
    render_optical_field(intensity, phase, norm_interf, phase_petals, S_norm, centers)

    # 3. Blit upscaled image to 4K canvas
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

    # 4. Spawn replacement dielectric nanoparticles near vortex orbits
    if len(particles) < MAX_PARTICLES:
        spawn_num = min(16, MAX_PARTICLES - len(particles))
        for _ in range(spawn_num):
            # Pick a vortex center and spawn in its vicinity
            cvx, cvy = random.choice(centers)
            angle = random.uniform(0.0, 2.0 * np.pi)
            rad = random.uniform(0.12, 0.95)
            spx = ((cvx + np.cos(angle) * rad - (-3.2)) / 6.4) * py5.width
            spy = ((cvy + np.sin(angle) * rad - (-3.2 * (Ny / Nx))) / (6.4 * (Ny / Nx))) * py5.height
            particles.append(DielectricParticle(spx, spy))

    # 5. Update and render dielectric nanoparticles on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        # Sample Poynting vector flow at particle position
        gx = int(np.clip(p.px * (Nx / py5.width), 0, Nx - 1))
        gy = int(np.clip(p.py * (Ny / py5.height), 0, Ny - 1))

        fx = Sx[gy, gx] * 8.5
        fy = Sy[gy, gx] * 8.5

        p.update(fx, fy)
        if not p.is_dead:
            active_particles.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * 235)

            # Dielectric nanoparticle color: Solar Gold core with Cyan radiation trail
            pr = int(245 + life_norm * 10)
            pg = int(190 + life_norm * 50)
            pb = int(60 + life_norm * 180)

            # Outer glow halo
            py5.no_stroke()
            py5.fill(pr, pg, pb, int(alpha * 0.35))
            py5.circle(p.px, p.py, p.size * 2.6)

            # Radiant core
            py5.fill(pr, pg, pb, alpha)
            py5.circle(p.px, p.py, p.size * 1.1)

            # Photon streamline tail
            py5.stroke(pr, pg, pb, int(alpha * 0.40))
            py5.stroke_weight(1.1)
            py5.line(p.px, p.py, p.px - p.vx * 2.2, p.py - p.vy * 2.2)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # Fail-safe check
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Trapped Particles: {len(particles)}")

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
